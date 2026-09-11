from dataclasses import dataclass, replace

from ludo.engine import next_player
from ludo.model import (
    CompetitionState,
    GameConfig,
    GameResult,
    GameState,
    Observation,
)
from ludo.observation import get_observation


@dataclass(frozen=True)
class BoardUser:
    name: str
    begin: int
    end: int
    tokens: tuple[int, ...]


@dataclass(frozen=True)
class BoardState:
    game_id: str
    state: str
    dice: int
    users: tuple[BoardUser, ...]


def parse_board(json: dict) -> BoardState:
    return BoardState(
        game_id=json["gameID"],
        state=json["state"],
        dice=json["dice"],
        users=tuple(
            BoardUser(
                name=user["name"],
                begin=user["begin"],
                end=user["end"],
                tokens=tuple(user["tokens"]),
            )
            for user in json["users"]
        ),
    )


def _game_state(board: BoardState, player_id: int, config: GameConfig) -> GameState:
    state = CompetitionState(board.state)
    game_over = state in (
        CompetitionState.END_YOU_WIN,
        CompetitionState.END_YOU_LOST,
        CompetitionState.END_EQUALS,
    )
    if state is CompetitionState.WAIT_FOR_YOU:
        current_player = player_id
    else:
        current_player = next_player(player_id, config)
    if state is CompetitionState.END_YOU_WIN:
        winner = player_id
    elif state is CompetitionState.END_YOU_LOST:
        winner = next_player(player_id, config)
    else:
        winner = None
    return GameState(
        tokens=tuple(user.tokens for user in board.users),
        current_player=current_player,
        dice_value=board.dice,
        consecutive_sixes=0,
        game_over=game_over,
        winner=winner,
        error_count=0,
        turn_number=0,
        state=state,
    )


def parse_observation(board: BoardState, player_id: int = 0) -> Observation:
    config = GameConfig(num_players=len(board.users), tokens_per_player=4)
    state = _game_state(board, player_id, config)
    obs = get_observation(state, player_id, config, game_id=board.game_id)
    legal_actions = obs.legal_actions if board.state == "WAIT_FOR_YOU" else ()
    return replace(obs, game_state=board.state, legal_actions=legal_actions)


def parse_result(board: BoardState, player_id: int = 0) -> GameResult:
    config = GameConfig(num_players=len(board.users), tokens_per_player=4)
    if board.state == "END_YOU_WIN":
        winner = player_id
    elif board.state == "END_YOU_LOST":
        winner = next_player(player_id, config)
    else:
        winner = None
    return GameResult(winner=winner, turn_count=0, error_count=0)


def action_to_address(own_tokens: tuple[int, ...], action: int | None) -> int | str:
    if action is None:
        return "0"
    return own_tokens[action]