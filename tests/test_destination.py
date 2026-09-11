from ludo.model import CompetitionState, GameConfig, GameState
from ludo.rules import compute_destination

CONFIG = GameConfig()


def _state(tokens, dice_value):
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


class TestComputeDestination:
    def test_token_moves_forward_by_dice_value(self) -> None:
        state = _state(((0, 5, 0, 0), (0, 0, 0, 0)), dice_value=4)
        assert compute_destination(state, player=0, token_index=1, config=CONFIG) == 9

    def test_token_on_track_1_to_40(self) -> None:
        state = _state(((1, 40, 7, 0), (0, 0, 0, 0)), dice_value=3)
        assert compute_destination(state, player=0, token_index=0, config=CONFIG) == 4
        assert compute_destination(state, player=0, token_index=2, config=CONFIG) == 10
        assert compute_destination(state, player=0, token_index=1, config=CONFIG) == 43

    def test_token_enters_board_on_dice_6(self) -> None:
        state = _state(((0, 0, 0, 0), (0, 0, 0, 0)), dice_value=6)
        assert compute_destination(state, player=0, token_index=0, config=CONFIG) == 1

    def test_token_at_home_cannot_enter_on_non_6(self) -> None:
        state = _state(((0, 0, 0, 0), (0, 0, 0, 0)), dice_value=3)
        assert compute_destination(state, player=0, token_index=0, config=CONFIG) is None
        state = _state(((0, 0, 0, 0), (0, 0, 0, 0)), dice_value=1)
        assert compute_destination(state, player=0, token_index=1, config=CONFIG) is None

    def test_entering_board_moves_to_position_1(self) -> None:
        state = _state(((0, 0, 0, 0), (0, 0, 0, 0)), dice_value=6)
        for token_index in range(4):
            assert (
                compute_destination(state, player=0, token_index=token_index, config=CONFIG)
                == 1
            )

    def test_token_transitions_to_home_stretch_after_40(self) -> None:
        state = _state(((0, 39, 0, 0), (0, 0, 0, 0)), dice_value=3)
        assert compute_destination(state, player=0, token_index=1, config=CONFIG) == 42

    def test_overshooting_home_stretch_is_illegal(self) -> None:
        state = _state(((0, 43, 40, 41), (0, 0, 0, 0)), dice_value=5)
        assert compute_destination(state, player=0, token_index=1, config=CONFIG) is None
        assert compute_destination(state, player=0, token_index=2, config=CONFIG) is None
        assert compute_destination(state, player=0, token_index=3, config=CONFIG) is None
        state = _state(((0, 39, 0, 0), (0, 0, 0, 0)), dice_value=6)
        assert compute_destination(state, player=0, token_index=1, config=CONFIG) is None

    def test_token_at_44_is_finished(self) -> None:
        state = _state(((44, 0, 0, 0), (0, 0, 0, 0)), dice_value=6)
        assert compute_destination(state, player=0, token_index=0, config=CONFIG) is None
        state = _state(((44, 0, 0, 0), (0, 0, 0, 0)), dice_value=1)
        assert compute_destination(state, player=0, token_index=0, config=CONFIG) is None

    def test_token_cannot_move_backward(self) -> None:
        for pos in (1, 5, 20, 40, 41, 43):
            for dice in range(1, 7):
                state = _state(((pos, 0, 0, 0), (0, 0, 0, 0)), dice_value=dice)
                dest = compute_destination(state, player=0, token_index=0, config=CONFIG)
                assert dest is None or dest > pos

    def test_dice_none_returns_none(self) -> None:
        state = _state(((0, 5, 0, 0), (0, 0, 0, 0)), dice_value=None)
        assert compute_destination(state, player=0, token_index=0, config=CONFIG) is None
        assert compute_destination(state, player=0, token_index=1, config=CONFIG) is None