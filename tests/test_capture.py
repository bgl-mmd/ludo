from ludo.model import CompetitionState, GameConfig, GameState
from ludo.rules import OPPONENT, SAME_PLAYER, check_capture, get_occupant

CONFIG = GameConfig()


def _state(tokens, dice_value=None):
    return GameState(
        tokens=tokens,
        current_player=0,
        dice_value=dice_value,
        consecutive_sixes=0,
        game_over=False,
        winner=None,
        error_count=0,
        turn_number=0,
        state=CompetitionState.NONE,
    )


class TestGetOccupant:
    def test_empty_cell_returns_none(self) -> None:
        state = _state(((0, 5, 0, 0), (0, 0, 0, 0)))
        assert get_occupant(state, player=0, position=10, config=CONFIG) is None

    def test_home_yard_zero_is_empty(self) -> None:
        state = _state(((0, 0, 0, 0), (0, 0, 0, 0)))
        assert get_occupant(state, player=0, position=0, config=CONFIG) is None

    def test_own_token_returns_same_player(self) -> None:
        state = _state(((0, 5, 8, 0), (0, 0, 0, 0)))
        assert get_occupant(state, player=0, position=5, config=CONFIG) is SAME_PLAYER

    def test_entering_board_blocked_if_position_1_occupied_by_self(self) -> None:
        state = _state(((1, 0, 0, 0), (0, 0, 0, 0)))
        assert get_occupant(state, player=0, position=1, config=CONFIG) is SAME_PLAYER

    def test_opponent_on_shared_track_returns_opponent(self) -> None:
        state = _state(((0, 5, 0, 0), (0, 30, 0, 0)))
        assert get_occupant(state, player=0, position=10, config=CONFIG) is OPPONENT
        assert get_occupant(state, player=1, position=30, config=CONFIG) is SAME_PLAYER

    def test_home_stretch_is_private(self) -> None:
        state = _state(((0, 0, 0, 0), (42, 0, 0, 0)))
        assert get_occupant(state, player=0, position=42, config=CONFIG) is None
        assert get_occupant(state, player=1, position=42, config=CONFIG) is SAME_PLAYER

    def test_home_stretch_own_token_returns_same_player(self) -> None:
        state = _state(((41, 42, 0, 0), (0, 0, 0, 0)))
        assert get_occupant(state, player=0, position=42, config=CONFIG) is SAME_PLAYER


class TestCheckCapture:
    def test_capturing_opponent_returns_opponent_to_0(self) -> None:
        state = _state(((0, 5, 0, 0), (0, 30, 0, 0)))
        assert check_capture(state, player=0, destination=10, config=CONFIG) == 1

    def test_capture_is_symmetric_between_players(self) -> None:
        state = _state(((0, 5, 0, 0), (0, 20, 0, 0)))
        assert check_capture(state, player=1, destination=25, config=CONFIG) == 0

    def test_own_token_blocks_destination(self) -> None:
        state = _state(((0, 5, 8, 0), (0, 0, 0, 0)))
        assert check_capture(state, player=0, destination=5, config=CONFIG) is None

    def test_cannot_move_to_cell_occupied_by_self(self) -> None:
        state = _state(((1, 0, 0, 0), (0, 0, 0, 0)))
        assert check_capture(state, player=0, destination=1, config=CONFIG) is None

    def test_no_capture_on_empty_cell(self) -> None:
        state = _state(((0, 5, 0, 0), (0, 0, 0, 0)))
        assert check_capture(state, player=0, destination=10, config=CONFIG) is None

    def test_multiple_opponents_captured_independently(self) -> None:
        config = GameConfig(num_players=3)
        state = _state(((0, 5, 7, 0), (0, 37, 0, 0), (0, 29, 0, 0)))
        assert check_capture(state, player=0, destination=10, config=config) == 1
        assert check_capture(state, player=0, destination=15, config=config) == 2

    def test_no_capture_on_home_stretch(self) -> None:
        state = _state(((0, 41, 0, 0), (42, 0, 0, 0)))
        for destination in (41, 42, 43, 44):
            assert check_capture(state, player=0, destination=destination, config=CONFIG) is None

    def test_no_capture_on_home_yard(self) -> None:
        state = _state(((0, 0, 0, 0), (0, 0, 0, 0)))
        assert check_capture(state, player=0, destination=0, config=CONFIG) is None