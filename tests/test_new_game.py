import dataclasses

import pytest

from ludo.engine import new_game
from ludo.model import CompetitionState, GameConfig


class TestNewGame:
    def test_initial_state_all_tokens_in_home_yard(self) -> None:
        config = GameConfig()
        state = new_game(config, ("Alice", "Bob"))
        assert state.tokens == ((0, 0, 0, 0), (0, 0, 0, 0))
        assert all(pos == 0 for player_tokens in state.tokens for pos in player_tokens)

    def test_initial_state_dice_is_none(self) -> None:
        state = new_game(GameConfig(), ("Alice", "Bob"))
        assert state.dice_value is None

    def test_initial_state_current_player_is_zero(self) -> None:
        state = new_game(GameConfig(), ("Alice", "Bob"))
        assert state.current_player == 0

    def test_initial_state_game_not_over(self) -> None:
        state = new_game(GameConfig(), ("Alice", "Bob"))
        assert state.game_over is False

    def test_initial_state_winner_is_none(self) -> None:
        state = new_game(GameConfig(), ("Alice", "Bob"))
        assert state.winner is None

    def test_initial_state_consecutive_sixes_is_zero(self) -> None:
        state = new_game(GameConfig(), ("Alice", "Bob"))
        assert state.consecutive_sixes == 0

    def test_initial_state_error_count_is_zero(self) -> None:
        state = new_game(GameConfig(), ("Alice", "Bob"))
        assert state.error_count == 0

    def test_initial_state_turn_number_is_zero(self) -> None:
        state = new_game(GameConfig(), ("Alice", "Bob"))
        assert state.turn_number == 0

    def test_initial_state_is_competition_state_none(self) -> None:
        state = new_game(GameConfig(), ("Alice", "Bob"))
        assert state.state is CompetitionState.NONE

    def test_tokens_shape_matches_config(self) -> None:
        config = GameConfig(num_players=4, tokens_per_player=3)
        state = new_game(config, ("A", "B", "C", "D"))
        assert len(state.tokens) == 4
        assert all(len(player_tokens) == 3 for player_tokens in state.tokens)
        assert state.tokens == ((0, 0, 0), (0, 0, 0), (0, 0, 0), (0, 0, 0))

    def test_tokens_are_immutable(self) -> None:
        state = new_game(GameConfig(), ("Alice", "Bob"))
        assert isinstance(state.tokens, tuple)
        assert all(isinstance(player_tokens, tuple) for player_tokens in state.tokens)
        with pytest.raises(TypeError):
            state.tokens[0][0] = 1  # type: ignore[index]
        with pytest.raises(dataclasses.FrozenInstanceError):
            state.tokens = ((1, 0, 0, 0), (0, 0, 0, 0))