from ludo.model import CompetitionState, GameConfig, GameState
from ludo.rules import get_legal_actions, is_valid_action

CONFIG = GameConfig()


def _state(tokens, dice_value, current_player=0):
    return GameState(
        tokens=tokens,
        current_player=current_player,
        dice_value=dice_value,
        consecutive_sixes=0,
        game_over=False,
        winner=None,
        error_count=0,
        turn_number=0,
        state=CompetitionState.NONE,
    )


class TestGetLegalActions:
    def test_legal_actions_include_all_valid_moves(self) -> None:
        state = _state(((0, 5, 7, 0), (0, 0, 0, 0)), dice_value=4)
        assert get_legal_actions(state, CONFIG) == (1, 2)

    def test_legal_actions_include_capturing_move(self) -> None:
        state = _state(((0, 5, 0, 0), (0, 30, 0, 0)), dice_value=5)
        assert get_legal_actions(state, CONFIG) == (1,)

    def test_legal_actions_exclude_blocked_destinations(self) -> None:
        state = _state(((0, 5, 9, 0), (0, 0, 0, 0)), dice_value=4)
        assert get_legal_actions(state, CONFIG) == (2,)

    def test_legal_actions_exclude_enter_when_start_blocked_by_self(self) -> None:
        state = _state(((0, 1, 0, 0), (0, 0, 0, 0)), dice_value=6)
        assert get_legal_actions(state, CONFIG) == (1,)

    def test_legal_actions_exclude_self_blocked_home_stretch(self) -> None:
        state = _state(((0, 41, 42, 0), (0, 0, 0, 0)), dice_value=1)
        assert get_legal_actions(state, CONFIG) == (2,)

    def test_legal_actions_include_enter_on_6(self) -> None:
        state = _state(((0, 5, 3, 4), (0, 0, 0, 0)), dice_value=6)
        assert get_legal_actions(state, CONFIG) == (0, 1, 2, 3)

    def test_legal_actions_exclude_enter_on_non_6(self) -> None:
        state = _state(((0, 5, 0, 0), (0, 0, 0, 0)), dice_value=3)
        assert get_legal_actions(state, CONFIG) == (1,)

    def test_legal_actions_empty_when_no_moves(self) -> None:
        state = _state(((0, 0, 0, 0), (0, 0, 0, 0)), dice_value=3)
        assert get_legal_actions(state, CONFIG) == ()

    def test_legal_actions_empty_when_all_overshoot(self) -> None:
        state = _state(((0, 43, 44, 44), (0, 0, 0, 0)), dice_value=5)
        assert get_legal_actions(state, CONFIG) == ()

    def test_legal_actions_reads_current_player(self) -> None:
        state = _state(
            ((0, 0, 0, 0), (0, 5, 0, 0)),
            dice_value=3,
            current_player=1,
        )
        assert get_legal_actions(state, CONFIG) == (1,)

    def test_legal_actions_empty_when_dice_none(self) -> None:
        state = _state(((0, 5, 0, 0), (0, 0, 0, 0)), dice_value=None)
        assert get_legal_actions(state, CONFIG) == ()


class TestIsValidAction:
    def test_legal_action_is_valid(self) -> None:
        state = _state(((0, 5, 0, 0), (0, 0, 0, 0)), dice_value=3)
        assert is_valid_action(state, 1, CONFIG) is True

    def test_illegal_action_is_invalid(self) -> None:
        state = _state(((0, 5, 0, 0), (0, 0, 0, 0)), dice_value=3)
        assert is_valid_action(state, 0, CONFIG) is False
        assert is_valid_action(state, 2, CONFIG) is False
        assert is_valid_action(state, 4, CONFIG) is False

    def test_none_valid_only_when_no_legal_moves(self) -> None:
        state = _state(((0, 0, 0, 0), (0, 0, 0, 0)), dice_value=3)
        assert get_legal_actions(state, CONFIG) == ()
        assert is_valid_action(state, None, CONFIG) is True

    def test_none_invalid_when_legal_moves_exist(self) -> None:
        state = _state(((0, 5, 0, 0), (0, 0, 0, 0)), dice_value=3)
        assert get_legal_actions(state, CONFIG) != ()
        assert is_valid_action(state, None, CONFIG) is False