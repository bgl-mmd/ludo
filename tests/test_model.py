import dataclasses
from typing import get_type_hints

import pytest

from ludo import (
    CompetitionState,
    GameConfig,
    GameResult,
    GameState,
    MoveRecord,
    Observation,
)

INITIAL_TOKENS = ((0, 0, 0, 0), (0, 0, 0, 0))


def _initial_state(state: CompetitionState = CompetitionState.NONE) -> GameState:
    return GameState(
        tokens=INITIAL_TOKENS,
        current_player=0,
        dice_value=None,
        consecutive_sixes=0,
        game_over=False,
        winner=None,
        error_count=0,
        turn_number=0,
        state=state,
    )


class TestCompetitionState:
    def test_members(self) -> None:
        members = {m.name for m in CompetitionState}
        assert members == {
            "NONE",
            "WAIT_FOR_START",
            "WAIT_FOR_YOU",
            "WAIT_FOR_MOVE",
            "END_YOU_WIN",
            "END_YOU_LOST",
            "END_EQUALS",
        }

    def test_member_values_are_strings(self) -> None:
        for member in CompetitionState:
            assert isinstance(member.value, str)


class TestGameConfig:
    def test_defaults(self) -> None:
        config = GameConfig()
        assert config.num_players == 2
        assert config.tokens_per_player == 4
        assert config.board_size == 40
        assert config.home_stretch_size == 4
        assert config.dice_sides == 6
        assert config.max_consecutive_sixes == 2

    def test_explicit_values(self) -> None:
        config = GameConfig(
            num_players=4,
            tokens_per_player=3,
            board_size=40,
            home_stretch_size=5,
            dice_sides=6,
            max_consecutive_sixes=3,
        )
        assert config.num_players == 4
        assert config.tokens_per_player == 3
        assert config.board_size == 40
        assert config.home_stretch_size == 5
        assert config.dice_sides == 6
        assert config.max_consecutive_sixes == 3

    def test_field_types(self) -> None:
        hints = get_type_hints(GameConfig)
        assert hints["num_players"] is int
        assert hints["tokens_per_player"] is int
        assert hints["board_size"] is int
        assert hints["home_stretch_size"] is int
        assert hints["dice_sides"] is int
        assert hints["max_consecutive_sixes"] is int

    def test_immutable(self) -> None:
        config = GameConfig()
        with pytest.raises(dataclasses.FrozenInstanceError):
            config.num_players = 4


class TestGameState:
    def test_construction(self) -> None:
        state = _initial_state()
        assert state.tokens == INITIAL_TOKENS
        assert state.current_player == 0
        assert state.dice_value is None
        assert state.consecutive_sixes == 0
        assert state.game_over is False
        assert state.winner is None
        assert state.error_count == 0
        assert state.turn_number == 0
        assert state.state is CompetitionState.NONE

    def test_explicit_values(self) -> None:
        tokens = ((1, 5, 0, 44), (2, 3, 4, 0))
        state = GameState(
            tokens=tokens,
            current_player=1,
            dice_value=6,
            consecutive_sixes=1,
            game_over=True,
            winner=0,
            error_count=2,
            turn_number=17,
            state=CompetitionState.END_YOU_WIN,
        )
        assert state.tokens == tokens
        assert state.current_player == 1
        assert state.dice_value == 6
        assert state.consecutive_sixes == 1
        assert state.game_over is True
        assert state.winner == 0
        assert state.error_count == 2
        assert state.turn_number == 17
        assert state.state is CompetitionState.END_YOU_WIN

    def test_field_types(self) -> None:
        hints = get_type_hints(GameState)
        assert hints["tokens"] == tuple[tuple[int, ...], ...]
        assert hints["current_player"] is int
        assert hints["dice_value"] == int | None
        assert hints["consecutive_sixes"] is int
        assert hints["game_over"] is bool
        assert hints["winner"] == int | None
        assert hints["error_count"] is int
        assert hints["turn_number"] is int
        assert hints["state"] is CompetitionState

    def test_immutable(self) -> None:
        state = _initial_state()
        with pytest.raises(dataclasses.FrozenInstanceError):
            state.turn_number = 1

    def test_initial_state_matches_spec(self) -> None:
        state = _initial_state()
        assert state.tokens == INITIAL_TOKENS
        assert all(pos == 0 for player_tokens in state.tokens for pos in player_tokens)
        assert state.dice_value is None
        assert state.current_player == 0
        assert state.game_over is False


class TestMoveRecord:
    def test_construction(self) -> None:
        record = MoveRecord(
            turn=1,
            player=0,
            action=2,
            dice_value=4,
            destination=5,
            captured=None,
            is_extra_turn=False,
            error=False,
        )
        assert record.turn == 1
        assert record.player == 0
        assert record.action == 2
        assert record.dice_value == 4
        assert record.destination == 5
        assert record.captured is None
        assert record.is_extra_turn is False
        assert record.error is False

    def test_explicit_values(self) -> None:
        record = MoveRecord(
            turn=9,
            player=1,
            action=None,
            dice_value=6,
            destination=0,
            captured=0,
            is_extra_turn=True,
            error=True,
        )
        assert record.turn == 9
        assert record.player == 1
        assert record.action is None
        assert record.dice_value == 6
        assert record.destination == 0
        assert record.captured == 0
        assert record.is_extra_turn is True
        assert record.error is True

    def test_field_types(self) -> None:
        hints = get_type_hints(MoveRecord)
        assert hints["turn"] is int
        assert hints["player"] is int
        assert hints["action"] == int | None
        assert hints["dice_value"] is int
        assert hints["destination"] is int
        assert hints["captured"] == int | None
        assert hints["is_extra_turn"] is bool
        assert hints["error"] is bool

    def test_immutable(self) -> None:
        record = MoveRecord(
            turn=1,
            player=0,
            action=0,
            dice_value=4,
            destination=5,
            captured=None,
            is_extra_turn=False,
            error=False,
        )
        with pytest.raises(dataclasses.FrozenInstanceError):
            record.dice_value = 3


class TestGameResult:
    def test_construction(self) -> None:
        result = GameResult(winner=1, turn_count=40, error_count=0)
        assert result.winner == 1
        assert result.turn_count == 40
        assert result.error_count == 0

    def test_draw(self) -> None:
        result = GameResult(winner=None, turn_count=50, error_count=3)
        assert result.winner is None
        assert result.turn_count == 50
        assert result.error_count == 3

    def test_field_types(self) -> None:
        hints = get_type_hints(GameResult)
        assert hints["winner"] == int | None
        assert hints["turn_count"] is int
        assert hints["error_count"] is int

    def test_immutable(self) -> None:
        result = GameResult(winner=0, turn_count=10, error_count=0)
        with pytest.raises(dataclasses.FrozenInstanceError):
            result.winner = 1


class TestObservation:
    def test_construction(self) -> None:
        obs = Observation(
            game_id="game-1",
            turn_number=3,
            player_id=0,
            num_players=2,
            dice_value=5,
            consecutive_sixes=0,
            own_tokens=(1, 5, 0, 0),
            opponent_tokens=((2, 3, 4, 0),),
            game_state="WAIT_FOR_YOU",
            game_over=False,
            is_your_turn=True,
            legal_actions=(0, 1),
        )
        assert obs.game_id == "game-1"
        assert obs.turn_number == 3
        assert obs.player_id == 0
        assert obs.num_players == 2
        assert obs.dice_value == 5
        assert obs.consecutive_sixes == 0
        assert obs.own_tokens == (1, 5, 0, 0)
        assert obs.opponent_tokens == ((2, 3, 4, 0),)
        assert obs.game_state == "WAIT_FOR_YOU"
        assert obs.game_over is False
        assert obs.is_your_turn is True
        assert obs.legal_actions == (0, 1)

    def test_explicit_values(self) -> None:
        obs = Observation(
            game_id="",
            turn_number=0,
            player_id=1,
            num_players=4,
            dice_value=6,
            consecutive_sixes=1,
            own_tokens=(0, 0, 0, 0),
            opponent_tokens=((0, 0, 0, 0), (0, 0, 0, 0), (0, 0, 0, 0)),
            game_state="END_YOU_LOST",
            game_over=True,
            is_your_turn=False,
            legal_actions=(),
        )
        assert obs.game_id == ""
        assert obs.turn_number == 0
        assert obs.player_id == 1
        assert obs.num_players == 4
        assert obs.dice_value == 6
        assert obs.consecutive_sixes == 1
        assert obs.own_tokens == (0, 0, 0, 0)
        assert obs.opponent_tokens == ((0, 0, 0, 0),) * 3
        assert obs.game_state == "END_YOU_LOST"
        assert obs.game_over is True
        assert obs.is_your_turn is False
        assert obs.legal_actions == ()

    def test_field_types(self) -> None:
        hints = get_type_hints(Observation)
        assert hints["game_id"] is str
        assert hints["turn_number"] is int
        assert hints["player_id"] is int
        assert hints["num_players"] is int
        assert hints["dice_value"] is int
        assert hints["consecutive_sixes"] is int
        assert hints["own_tokens"] == tuple[int, ...]
        assert hints["opponent_tokens"] == tuple[tuple[int, ...], ...]
        assert hints["game_state"] is str
        assert hints["game_over"] is bool
        assert hints["is_your_turn"] is bool
        assert hints["legal_actions"] == tuple[int, ...]

    def test_immutable(self) -> None:
        obs = Observation(
            game_id="game-1",
            turn_number=3,
            player_id=0,
            num_players=2,
            dice_value=5,
            consecutive_sixes=0,
            own_tokens=(1, 5, 0, 0),
            opponent_tokens=((2, 3, 4, 0),),
            game_state="WAIT_FOR_YOU",
            game_over=False,
            is_your_turn=True,
            legal_actions=(0, 1),
        )
        with pytest.raises(dataclasses.FrozenInstanceError):
            obs.dice_value = 3


def test_package_exports() -> None:
    import ludo

    assert ludo.GameConfig is GameConfig
    assert ludo.GameState is GameState
    assert ludo.MoveRecord is MoveRecord
    assert ludo.GameResult is GameResult
    assert ludo.Observation is Observation
    assert ludo.CompetitionState is CompetitionState
