import dataclasses

from ludo.bots import make_greedy_bot, make_random_bot
from ludo.coordinates import global_to_player, player_to_global
from ludo.dice import create_rng, roll_dice
from ludo.engine import apply_action, new_game
from ludo.model import GameConfig
from ludo.observation import get_observation
from ludo.rules import get_legal_actions, is_game_over
from ludo.simulation import run_simulation

SEEDS = range(20)
CONFIG = GameConfig()


def _random_bots() -> tuple:
    return (make_random_bot(seed=1), make_random_bot(seed=2))


def _mixed_bots() -> tuple:
    return (make_random_bot(seed=3), make_greedy_bot())


def _greedy_bots() -> tuple:
    return (make_greedy_bot(), make_greedy_bot())


def _greedy_random_bots() -> tuple:
    return (make_greedy_bot(), make_random_bot(seed=5))


_BOT_FACTORIES = (_random_bots, _mixed_bots, _greedy_bots, _greedy_random_bots)


def _play(seed: int, bots: tuple) -> tuple:
    rng = create_rng(seed)
    names = tuple(getattr(b, "__name__", "bot") for b in bots)
    state = new_game(CONFIG, names)
    steps = []
    while not is_game_over(state):
        state, _ = roll_dice(state, rng)
        obs = get_observation(state, state.current_player, CONFIG, game_id="g")
        action = bots[state.current_player](obs)
        before = state
        state, record = apply_action(state, action, CONFIG)
        steps.append((before, action, state, record))
    return state, tuple(steps)


def _play_all() -> list:
    games = []
    for seed in SEEDS:
        for factory in _BOT_FACTORIES:
            games.append(_play(seed, factory()))
    return games


def _mid_game_states() -> list:
    states = []
    for _terminal, steps in _play_all():
        for before, _action, _after, _record in steps:
            states.append(before)
    return states


def _assert_at_most_one_token_per_cell(state) -> None:
    for player in range(CONFIG.num_players):
        seen = set()
        for pos in state.tokens[player]:
            if pos == 0:
                continue
            assert pos not in seen
            seen.add(pos)
    global_cells = set()
    for player in range(CONFIG.num_players):
        for pos in state.tokens[player]:
            if 1 <= pos <= CONFIG.board_size:
                cell = player_to_global(pos, player, CONFIG)
                assert cell not in global_cells
                global_cells.add(cell)


def _illegal_actions(state, legal: tuple) -> list:
    actions = [index for index in range(CONFIG.tokens_per_player) if index not in legal]
    if legal:
        actions.append(None)
    return actions


class TestInvariantAtMostOneTokenPerCell:
    def test_invariant_at_most_one_token_per_cell(self) -> None:
        initial = new_game(CONFIG, ("A", "B"))
        _assert_at_most_one_token_per_cell(initial)
        for _terminal, steps in _play_all():
            for _before, _action, after, _record in steps:
                _assert_at_most_one_token_per_cell(after)


class TestInvariantTokensNeverMoveBackward:
    def test_invariant_tokens_never_move_backward(self) -> None:
        for _terminal, steps in _play_all():
            for before, action, after, record in steps:
                if record.error or action is None:
                    assert after.tokens == before.tokens
                    continue
                source = before.tokens[record.player][record.action]
                assert record.destination > source
                expected = [list(row) for row in before.tokens]
                expected[record.player][record.action] = record.destination
                if record.captured is not None:
                    global_pos = player_to_global(
                        record.destination, record.player, CONFIG
                    )
                    opp_rel = global_to_player(global_pos, record.captured, CONFIG)
                    for index, pos in enumerate(expected[record.captured]):
                        if pos == opp_rel:
                            expected[record.captured][index] = 0
                            break
                expected_tokens = tuple(tuple(row) for row in expected)
                assert after.tokens == expected_tokens


class TestInvariantIllegalActionNeverMutatesState:
    def test_invariant_illegal_action_never_mutates_state(self) -> None:
        for state in _mid_game_states():
            legal = get_legal_actions(state, CONFIG)
            for action in _illegal_actions(state, legal):
                snapshot = dataclasses.asdict(state)
                new_state, record = apply_action(state, action, CONFIG)
                assert dataclasses.asdict(state) == snapshot
                assert record.error is True
                assert new_state.error_count == state.error_count + 1
                assert new_state.tokens == state.tokens


class TestInvariantCompletedGameRejectsMoves:
    def test_invariant_completed_game_rejects_moves(self) -> None:
        for terminal, _steps in _play_all():
            assert terminal.game_over is True
            assert terminal.winner is not None
            for action in (None, 0, 1, 2, 3):
                new_state, record = apply_action(terminal, action, CONFIG)
                assert record.error is True
                assert new_state.error_count == terminal.error_count + 1
                assert new_state.game_over is True
                assert new_state.winner == terminal.winner
                assert new_state.tokens == terminal.tokens
                assert is_game_over(new_state) is True


class TestInvariantLegalActionsSubsetOfAllActions:
    def test_invariant_legal_actions_subset_of_all_actions(self) -> None:
        for state in _mid_game_states():
            legal = get_legal_actions(state, CONFIG)
            assert len(legal) == len(set(legal))
            for action in legal:
                assert 0 <= action < CONFIG.tokens_per_player


class TestInvariantEachLegalActionProducesValidState:
    def test_invariant_each_legal_action_produces_valid_state(self) -> None:
        for state in _mid_game_states():
            for action in get_legal_actions(state, CONFIG):
                new_state, record = apply_action(state, action, CONFIG)
                assert record.error is False
                _assert_at_most_one_token_per_cell(new_state)
                assert is_game_over(new_state) == new_state.game_over
                if new_state.game_over:
                    assert new_state.winner == record.player
                else:
                    assert new_state.winner is None


class TestInvariantGameEventuallyEnds:
    def test_invariant_game_eventually_ends(self) -> None:
        for seed in SEEDS:
            for factory in _BOT_FACTORIES:
                result, _log = run_simulation(factory(), CONFIG, seed=seed)
                assert result.winner is not None
                assert result.turn_count < 2000