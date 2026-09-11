from ludo.model import CompetitionState, GameConfig, GameState
from ludo.rules import check_win, compute_destination, is_game_over

CONFIG = GameConfig()


def _state(tokens, dice_value=None, game_over=False, winner=None):
    return GameState(
        tokens=tokens,
        current_player=0,
        dice_value=dice_value,
        consecutive_sixes=0,
        game_over=game_over,
        winner=winner,
        error_count=0,
        turn_number=0,
        state=CompetitionState.NONE,
    )


class TestCheckWin:
    def test_win_when_all_4_tokens_at_44(self) -> None:
        state = _state(((44, 44, 44, 44), (0, 0, 0, 0)))
        assert check_win(state, player=0, config=CONFIG) is True

    def test_win_tokens_spread_across_home_stretch(self) -> None:
        state = _state(((41, 42, 43, 44), (0, 0, 0, 0)))
        assert check_win(state, player=0, config=CONFIG) is True

    def test_no_win_with_3_tokens_at_44(self) -> None:
        state = _state(((44, 44, 44, 0), (0, 0, 0, 0)))
        assert check_win(state, player=0, config=CONFIG) is False

    def test_no_win_with_token_still_at_40(self) -> None:
        state = _state(((41, 42, 43, 40), (0, 0, 0, 0)))
        assert check_win(state, player=0, config=CONFIG) is False

    def test_no_win_with_token_in_home_yard(self) -> None:
        state = _state(((44, 44, 44, 0), (0, 0, 0, 0)))
        assert check_win(state, player=0, config=CONFIG) is False

    def test_win_only_for_own_player(self) -> None:
        state = _state(((41, 42, 43, 44), (0, 0, 0, 0)))
        assert check_win(state, player=0, config=CONFIG) is True
        assert check_win(state, player=1, config=CONFIG) is False

    def test_win_any_tokens_per_player_count(self) -> None:
        config = GameConfig(tokens_per_player=3)
        state = _state(((41, 42, 43), (0, 0, 0)))
        assert check_win(state, player=0, config=config) is True
        state = _state(((41, 42, 40), (0, 0, 0)))
        assert check_win(state, player=0, config=config) is False

    def test_win_respects_custom_home_stretch_bounds(self) -> None:
        config = GameConfig(home_stretch_size=5)
        state = _state(((41, 42, 43, 44), (0, 0, 0, 0)))
        assert check_win(state, player=0, config=config) is True
        state = _state(((40, 41, 42, 43), (0, 0, 0, 0)))
        assert check_win(state, player=0, config=config) is False
        state = _state(((41, 42, 43, 45), (0, 0, 0, 0)))
        assert check_win(state, player=0, config=config) is True

    def test_win_detected_after_move(self) -> None:
        pre = _state(((43, 42, 44, 40), (0, 0, 0, 0)), dice_value=1)
        assert compute_destination(pre, player=0, token_index=3, config=CONFIG) == 41
        post = _state(((43, 42, 44, 41), (0, 0, 0, 0)))
        assert check_win(pre, player=0, config=CONFIG) is False
        assert check_win(post, player=0, config=CONFIG) is True


class TestIsGameOver:
    def test_false_for_fresh_state(self) -> None:
        state = _state(((0, 0, 0, 0), (0, 0, 0, 0)))
        assert is_game_over(state) is False

    def test_true_when_player_zero_wins(self) -> None:
        state = _state(((41, 42, 43, 44), (0, 0, 0, 0)))
        assert is_game_over(state) is True

    def test_true_when_any_player_wins(self) -> None:
        state = _state(((0, 0, 0, 0), (41, 42, 43, 44)))
        assert is_game_over(state) is True

    def test_respects_game_over_flag(self) -> None:
        state = _state(((0, 0, 0, 0), (0, 0, 0, 0)), game_over=True, winner=1)
        assert is_game_over(state) is True

    def test_false_when_no_player_won(self) -> None:
        state = _state(((44, 44, 44, 40), (0, 0, 0, 0)))
        assert is_game_over(state) is False

    def test_reconstructs_config_from_state(self) -> None:
        state = _state(((41, 42, 43), (44, 44, 44), (0, 0, 0)))
        assert is_game_over(state) is True