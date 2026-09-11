import dataclasses

from ludo.engine import apply_action
from ludo.model import CompetitionState, GameConfig, GameState

CONFIG = GameConfig()


def _state(tokens, **overrides):
    base = GameState(
        tokens=tokens,
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


class TestNormalMove:
    def test_token_moves_forward_by_dice_value(self) -> None:
        state = _state(((0, 5, 0, 0), (0, 0, 0, 0)), dice_value=3)
        new_state, record = apply_action(state, 1, CONFIG)
        assert new_state.tokens == ((0, 8, 0, 0), (0, 0, 0, 0))
        assert record.destination == 8

    def test_normal_move_ends_turn(self) -> None:
        state = _state(((0, 5, 0, 0), (0, 0, 0, 0)), dice_value=3)
        new_state, record = apply_action(state, 1, CONFIG)
        assert new_state.current_player == 1
        assert new_state.dice_value is None
        assert new_state.consecutive_sixes == 0
        assert new_state.turn_number == 1
        assert record.turn == 0
        assert record.player == 0
        assert record.action == 1
        assert record.dice_value == 3
        assert record.captured is None
        assert record.is_extra_turn is False
        assert record.error is False


class TestCapture:
    def test_capturing_opponent_returns_opponent_to_0(self) -> None:
        state = _state(((0, 5, 0, 0), (0, 30, 0, 0)), dice_value=5)
        new_state, record = apply_action(state, 1, CONFIG)
        assert new_state.tokens == ((0, 10, 0, 0), (0, 0, 0, 0))
        assert record.captured == 1
        assert record.destination == 10


class TestEnterOnSix:
    def test_entering_board_moves_to_position_1(self) -> None:
        state = _state(((0, 0, 0, 0), (0, 0, 0, 0)), dice_value=6)
        new_state, record = apply_action(state, 0, CONFIG)
        assert new_state.tokens == ((1, 0, 0, 0), (0, 0, 0, 0))
        assert record.destination == 1


class TestHomeStretch:
    def test_token_transitions_to_home_stretch_after_40(self) -> None:
        state = _state(((39, 0, 0, 0), (0, 0, 0, 0)), dice_value=3)
        new_state, record = apply_action(state, 0, CONFIG)
        assert new_state.tokens == ((42, 0, 0, 0), (0, 0, 0, 0))
        assert record.destination == 42

    def test_token_moves_within_home_stretch(self) -> None:
        state = _state(((42, 0, 0, 0), (0, 0, 0, 0)), dice_value=1)
        new_state, record = apply_action(state, 0, CONFIG)
        assert new_state.tokens == ((43, 0, 0, 0), (0, 0, 0, 0))
        assert record.destination == 43

    def test_token_finishes_at_44(self) -> None:
        state = _state(((43, 0, 0, 0), (0, 0, 0, 0)), dice_value=1)
        new_state, record = apply_action(state, 0, CONFIG)
        assert new_state.tokens == ((44, 0, 0, 0), (0, 0, 0, 0))
        assert record.destination == 44


class TestOvershoot:
    def test_overshooting_home_stretch_is_illegal(self) -> None:
        state = _state(((43, 0, 0, 0), (0, 0, 0, 0)), dice_value=5)
        new_state, record = apply_action(state, 0, CONFIG)
        assert new_state.tokens == ((43, 0, 0, 0), (0, 0, 0, 0))
        assert record.error is True
        assert new_state.error_count == 1
        assert new_state.current_player == 1

    def test_overshooting_from_track_is_illegal(self) -> None:
        state = _state(((39, 0, 0, 0), (0, 0, 0, 0)), dice_value=6)
        new_state, record = apply_action(state, 0, CONFIG)
        assert record.error is True
        assert new_state.tokens == ((39, 0, 0, 0), (0, 0, 0, 0))


class TestBlockedBySelf:
    def test_own_token_blocks_destination(self) -> None:
        state = _state(((0, 5, 9, 0), (0, 0, 0, 0)), dice_value=4)
        new_state, record = apply_action(state, 1, CONFIG)
        assert record.error is True
        assert new_state.tokens == ((0, 5, 9, 0), (0, 0, 0, 0))
        assert new_state.error_count == 1

    def test_entering_board_blocked_by_self(self) -> None:
        state = _state(((0, 1, 0, 0), (0, 0, 0, 0)), dice_value=6)
        new_state, record = apply_action(state, 0, CONFIG)
        assert record.error is True
        assert new_state.tokens == ((0, 1, 0, 0), (0, 0, 0, 0))


class TestPass:
    def test_move_0_ends_turn(self) -> None:
        state = _state(((0, 0, 0, 0), (0, 0, 0, 0)), dice_value=3)
        new_state, record = apply_action(state, None, CONFIG)
        assert record.error is False
        assert record.action is None
        assert record.destination == 0
        assert record.is_extra_turn is False
        assert new_state.current_player == 1
        assert new_state.dice_value is None
        assert new_state.consecutive_sixes == 0
        assert new_state.turn_number == 1

    def test_move_0_on_six_never_grants_extra_turn(self) -> None:
        state = _state(((43, 44, 44, 44), (0, 0, 0, 0)), dice_value=6)
        new_state, record = apply_action(state, None, CONFIG)
        assert record.is_extra_turn is False
        assert new_state.current_player == 1
        assert new_state.consecutive_sixes == 0


class TestExtraTurn:
    def test_dice_6_grants_extra_turn(self) -> None:
        state = _state(((0, 5, 0, 0), (0, 0, 0, 0)), dice_value=6)
        new_state, record = apply_action(state, 1, CONFIG)
        assert record.is_extra_turn is True
        assert new_state.current_player == 0
        assert new_state.consecutive_sixes == 1

    def test_second_consecutive_6_ends_turn(self) -> None:
        state = _state(
            ((0, 5, 0, 0), (0, 0, 0, 0)),
            dice_value=6,
            consecutive_sixes=1,
        )
        new_state, record = apply_action(state, 1, CONFIG)
        assert record.is_extra_turn is False
        assert new_state.current_player == 1
        assert new_state.consecutive_sixes == 0

    def test_regular_roll_no_extra_turn(self) -> None:
        state = _state(((0, 5, 0, 0), (0, 0, 0, 0)), dice_value=3)
        new_state, record = apply_action(state, 1, CONFIG)
        assert record.is_extra_turn is False
        assert new_state.current_player == 1


class TestWin:
    def test_win_sets_game_over_and_winner(self) -> None:
        state = _state(((40, 41, 42, 43), (0, 0, 0, 0)), dice_value=4)
        new_state, record = apply_action(state, 0, CONFIG)
        assert new_state.game_over is True
        assert new_state.winner == 0
        assert new_state.tokens == ((44, 41, 42, 43), (0, 0, 0, 0))
        assert record.error is False
        assert record.is_extra_turn is False

    def test_no_win_with_tokens_not_finished(self) -> None:
        state = _state(((44, 44, 44, 10), (0, 0, 0, 0)), dice_value=2)
        new_state, record = apply_action(state, 3, CONFIG)
        assert new_state.game_over is False
        assert new_state.winner is None


class TestIllegalAction:
    def test_state_not_changed_by_illegal_action(self) -> None:
        state = _state(((0, 5, 0, 0), (0, 0, 0, 0)), dice_value=3)
        new_state, record = apply_action(state, 0, CONFIG)
        assert state.tokens == ((0, 5, 0, 0), (0, 0, 0, 0))
        assert state.current_player == 0
        assert state.dice_value == 3
        assert state.consecutive_sixes == 0
        assert state.error_count == 0
        assert state.turn_number == 0
        assert new_state is not state
        assert new_state.error_count == 1
        assert record.error is True

    def test_none_invalid_when_legal_moves_exist(self) -> None:
        state = _state(((0, 5, 0, 0), (0, 0, 0, 0)), dice_value=3)
        new_state, record = apply_action(state, None, CONFIG)
        assert record.error is True
        assert new_state.error_count == 1
        assert new_state.current_player == 1

    def test_illegal_action_forces_pass(self) -> None:
        state = _state(((0, 5, 0, 0), (0, 0, 0, 0)), dice_value=3)
        new_state, record = apply_action(state, 2, CONFIG)
        assert new_state.current_player == 1
        assert new_state.dice_value is None
        assert new_state.consecutive_sixes == 0
        assert new_state.turn_number == 1
        assert record.turn == 0
        assert record.destination == 0
        assert record.error is True


class TestStateTransitions:
    def test_state_transitions_normal_turn(self) -> None:
        state = _state(((0, 5, 0, 0), (0, 0, 0, 0)), dice_value=3)
        new_state, record = apply_action(state, 1, CONFIG)
        assert new_state.tokens == ((0, 8, 0, 0), (0, 0, 0, 0))
        assert new_state.current_player == 1
        assert new_state.dice_value is None
        assert record.is_extra_turn is False
        assert record.error is False

    def test_state_transitions_on_6_extra_turn(self) -> None:
        state = _state(((0, 5, 0, 0), (0, 0, 0, 0)), dice_value=6)
        new_state, record = apply_action(state, 1, CONFIG)
        assert new_state.current_player == 0
        assert new_state.consecutive_sixes == 1
        assert record.is_extra_turn is True

    def test_state_transitions_on_second_6(self) -> None:
        state = _state(
            ((0, 5, 0, 0), (0, 0, 0, 0)),
            dice_value=6,
            consecutive_sixes=1,
        )
        new_state, record = apply_action(state, 1, CONFIG)
        assert new_state.current_player == 1
        assert new_state.consecutive_sixes == 0
        assert record.is_extra_turn is False

    def test_state_transitions_on_win(self) -> None:
        state = _state(((40, 41, 42, 43), (0, 0, 0, 0)), dice_value=4)
        new_state, record = apply_action(state, 0, CONFIG)
        assert new_state.game_over is True
        assert new_state.winner == 0
        assert record.error is False

    def test_state_transitions_on_loss(self) -> None:
        state = _state(((44, 44, 44, 10), (0, 0, 0, 0)), dice_value=2)
        new_state, record = apply_action(state, 3, CONFIG)
        assert new_state.game_over is False
        assert new_state.winner is None
        assert new_state.current_player == 1
        assert record.error is False