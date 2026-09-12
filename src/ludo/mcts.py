import math
import random
from dataclasses import dataclass, field
from typing import Callable

from ludo.coordinates import global_to_player, player_to_global
from ludo.dice import roll_dice
from ludo.engine import apply_action
from ludo.model import CompetitionState, GameConfig, GameState, Observation
from ludo.rules import get_legal_actions, is_game_over

BotFn = Callable[[Observation], int | None]


def _observation_to_state(obs: Observation, config: GameConfig) -> GameState:
    """Reconstruct the engine state from an observation. Exact inverse of get_observation."""
    tokens: list[tuple[int, ...] | None] = [None] * config.num_players
    tokens[obs.player_id] = obs.own_tokens
    opponents = [p for p in range(config.num_players) if p != obs.player_id]
    for opponent, seen in zip(opponents, obs.opponent_tokens):
        tokens[opponent] = tuple(
            global_to_player(
                player_to_global(pos, obs.player_id, config), opponent, config
            )
            for pos in seen
        )
    return GameState(
        tokens=tuple(tokens),
        current_player=obs.player_id,
        dice_value=obs.dice_value,
        consecutive_sixes=obs.consecutive_sixes,
        game_over=obs.game_over,
        winner=None,
        error_count=0,
        turn_number=obs.turn_number,
        state=CompetitionState.NONE,
    )


@dataclass
class _Node:
    state: GameState
    visits: int = 0
    wins: int = 0
    children: dict[int, "_Node"] = field(default_factory=dict)
    legal_actions: tuple[int, ...] = ()

    def is_fully_expanded(self) -> bool:
        return len(self.children) >= len(self.legal_actions)

    def is_terminal(self) -> bool:
        return is_game_over(self.state) or not self.legal_actions


def _ucb1(node: "_Node", child: "_Node", exploration_constant: float) -> float:
    if child.visits == 0:
        return math.inf
    exploitation = child.wins / child.visits
    exploration = exploration_constant * math.sqrt(
        math.log(node.visits) / child.visits
    )
    return exploitation + exploration


def _score(action: int, state: GameState, config: GameConfig) -> tuple[int, int, int]:
    player = state.current_player
    pos = state.tokens[player][action]
    dest = 1 if pos == 0 else pos + state.dice_value
    captures = int(
        1 <= dest <= config.board_size
        and any(
            dest in state.tokens[p]
            for p in range(config.num_players)
            if p != player
        )
    )
    enters = int(pos == 0)
    return (captures, enters, pos)


def _playout(
    state: GameState,
    config: GameConfig,
    rng: random.Random,
    turn_cap: int,
) -> int | None:
    """Roll out from `state` using a greedy default policy. Returns winner index."""
    while not is_game_over(state) and state.turn_number < turn_cap:
        state, _ = roll_dice(state, rng)
        actions = get_legal_actions(state, config)
        if not actions:
            state, _ = apply_action(state, None, config)
            continue
        action = max(actions, key=lambda a: _score(a, state, config))
        state, _ = apply_action(state, action, config)
    return state.winner


def _search(
    root: GameState,
    config: GameConfig,
    iterations: int,
    rng: random.Random,
    exploration_constant: float,
    root_actions: tuple[int, ...] | None = None,
) -> int | None:
    legal = root_actions if root_actions is not None else get_legal_actions(root, config)
    root_node = _Node(state=root, legal_actions=legal)
    if not root_node.legal_actions:
        return None

    turn_cap = root.turn_number + 500

    for _ in range(iterations):
        path: list[_Node] = []
        node = root_node

        while node.is_fully_expanded() and not node.is_terminal():
            action = max(
                node.children,
                key=lambda a: _ucb1(node, node.children[a], exploration_constant),
            )
            node = node.children[action]
            path.append(node)

        if node.is_terminal():
            winner = node.state.winner
            leaf, ancestors = node, path[:-1]
        else:
            action = next(a for a in node.legal_actions if a not in node.children)
            moved, _ = apply_action(node.state, action, config)
            rolled, _ = roll_dice(moved, rng)
            child = _Node(state=rolled, legal_actions=get_legal_actions(rolled, config))
            node.children[action] = child
            winner = _playout(rolled, config, rng, turn_cap)
            leaf, ancestors = child, path

        leaf.visits += 1
        if winner is not None and leaf.state.current_player == winner:
            leaf.wins += 1
        for ancestor in reversed(ancestors):
            ancestor.visits += 1
            if winner is not None and ancestor.state.current_player == winner:
                ancestor.wins += 1
        root_node.visits += 1

    return max(
        root_node.children,
        key=lambda a: (root_node.children[a].visits, root_node.children[a].wins),
    )


def make_mcts_bot(
    iterations: int = 200,
    seed: int | None = None,
    config: GameConfig | None = None,
    exploration_constant: float = 1.41,
) -> BotFn:
    cfg = config or GameConfig()
    rng = random.Random(seed)

    def bot(obs: Observation) -> int | None:
        if not obs.legal_actions:
            return None
        game_cfg = GameConfig(
            num_players=obs.num_players,
            tokens_per_player=cfg.tokens_per_player,
            board_size=cfg.board_size,
            home_stretch_size=cfg.home_stretch_size,
            dice_sides=cfg.dice_sides,
            max_consecutive_sixes=cfg.max_consecutive_sixes,
        )
        state = _observation_to_state(obs, game_cfg)
        return _search(state, game_cfg, iterations, rng, exploration_constant, obs.legal_actions)

    return bot


def _destination(pos: int, dice: int) -> int | None:
    if pos == 0:
        return 1 if dice == 6 else None
    return pos + dice


def _is_threatened(
    pos: int, opponent_tokens: tuple[tuple[int, ...], ...], danger_window: int
) -> bool:
    """True if an opponent token is behind `pos` by 1..danger_window steps on the track."""
    if not 1 <= pos <= 40:
        return False
    return any(
        1 <= pos - opponent_pos <= danger_window
        for opponent in opponent_tokens
        for opponent_pos in opponent
        if 1 <= opponent_pos <= 40
    )


def _classify_actions(
    obs: Observation, danger_window: int
) -> tuple[tuple[int, ...], tuple[int, ...]]:
    """Split legal actions into (captures, escapes) on player-relative coords.

    A capture lands on an opponent token. An escape moves a threatened token
    (opponent 1..danger_window behind) fully out of that danger window or into
    the home stretch.
    """
    captures: list[int] = []
    escapes: list[int] = []
    for action in obs.legal_actions:
        dest = _destination(obs.own_tokens[action], obs.dice_value)
        if dest is None:
            continue
        if 1 <= dest <= 40 and any(
            dest in opponent for opponent in obs.opponent_tokens
        ):
            captures.append(action)
        elif _is_threatened(
            obs.own_tokens[action], obs.opponent_tokens, danger_window
        ) and (
            dest > 40
            or not _is_threatened(dest, obs.opponent_tokens, danger_window)
        ):
            escapes.append(action)
    return tuple(captures), tuple(escapes)


def _obs_score(action: int, obs: Observation) -> tuple[int, int, int]:
    pos = obs.own_tokens[action]
    dest = 1 if pos == 0 else pos + obs.dice_value
    captures = int(
        1 <= dest <= 40
        and any(dest == token for opponent in obs.opponent_tokens for token in opponent)
    )
    enters = int(pos == 0)
    return (captures, enters, pos)


def make_mcts_evasive_bot(
    iterations: int = 200,
    seed: int | None = None,
    config: GameConfig | None = None,
    exploration_constant: float = 1.41,
    danger_window: int = 4,
) -> BotFn:
    """MCTS bot with capture-first, then flee-if-threatened priorities.

    Priorities per turn:
      1. If any legal move captures an opponent token, MCTS picks among captures.
      2. Elif an opponent is 1..danger_window steps behind a token, MCTS picks
         among moves that get that token fully out of the danger window.
      3. Otherwise plain MCTS.
    """
    cfg = config or GameConfig()
    rng = random.Random(seed)

    def bot(obs: Observation) -> int | None:
        if not obs.legal_actions:
            return None
        game_cfg = GameConfig(
            num_players=obs.num_players,
            tokens_per_player=cfg.tokens_per_player,
            board_size=cfg.board_size,
            home_stretch_size=cfg.home_stretch_size,
            dice_sides=cfg.dice_sides,
            max_consecutive_sixes=cfg.max_consecutive_sixes,
        )
        captures, escapes = _classify_actions(obs, danger_window)
        root_actions = captures or escapes or obs.legal_actions
        action = _search(
            _observation_to_state(obs, game_cfg),
            game_cfg,
            iterations,
            rng,
            exploration_constant,
            root_actions,
        )
        if action is None:
            return max(obs.legal_actions, key=lambda a: _obs_score(a, obs))
        return action

    return bot