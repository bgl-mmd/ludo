import dataclasses

from ludo.engine import get_result
from ludo.model import CompetitionState, GameResult, GameState

INITIAL_TOKENS = ((0, 0, 0, 0), (0, 0, 0, 0))


def _state(**overrides) -> GameState:
    base = GameState(
        tokens=INITIAL_TOKENS,
        current_player=0,
        dice_value=None,
        consecutive_sixes=0,
        game_over=False,
        winner=None,
        error_count=0,
        turn_number=0,
        state=CompetitionState.NONE,
    )
    return dataclasses.replace(base, **overrides)


class TestWinResult:
    def test_winner_index_reflects_finished_state(self) -> None:
        state = _state(game_over=True, winner=0, turn_number=73, error_count=2)
        result = get_result(state, ("Alice", "Bob"))
        assert result.winner == 0

    def test_turn_count_reflects_finished_state(self) -> None:
        state = _state(game_over=True, winner=0, turn_number=73, error_count=2)
        result = get_result(state, ("Alice", "Bob"))
        assert result.turn_count == 73

    def test_error_count_reflects_finished_state(self) -> None:
        state = _state(game_over=True, winner=0, turn_number=73, error_count=2)
        result = get_result(state, ("Alice", "Bob"))
        assert result.error_count == 2

    def test_returns_game_result_instance(self) -> None:
        state = _state(game_over=True, winner=0, turn_number=73, error_count=2)
        result = get_result(state, ("Alice", "Bob"))
        assert isinstance(result, GameResult)


class TestLossResult:
    def test_opponent_is_winner(self) -> None:
        state = _state(game_over=True, winner=1, turn_number=80, error_count=0)
        result = get_result(state, ("Alice", "Bob"))
        assert result.winner == 1
        assert result.turn_count == 80
        assert result.error_count == 0


class TestDrawResult:
    def test_winner_is_none_for_draw(self) -> None:
        state = _state(game_over=True, winner=None, turn_number=100, error_count=5)
        result = get_result(state, ("Alice", "Bob"))
        assert result.winner is None

    def test_draw_still_records_turn_and_error_counts(self) -> None:
        state = _state(game_over=True, winner=None, turn_number=100, error_count=5)
        result = get_result(state, ("Alice", "Bob"))
        assert result.turn_count == 100
        assert result.error_count == 5


class TestGetResultPurity:
    def test_state_not_mutated(self) -> None:
        state = _state(game_over=True, winner=0, turn_number=73, error_count=2)
        get_result(state, ("Alice", "Bob"))
        assert state.game_over is True
        assert state.winner == 0
        assert state.turn_number == 73
        assert state.error_count == 2

    def test_result_does_not_depend_on_player_names(self) -> None:
        state = _state(game_over=True, winner=1, turn_number=90, error_count=1)
        assert get_result(state, ("Alice", "Bob")) == get_result(state, ("X", "Y"))