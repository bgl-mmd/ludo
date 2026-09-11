from dataclasses import dataclass
from enum import Enum


class CompetitionState(Enum):
    NONE = "NONE"
    WAIT_FOR_START = "WAIT_FOR_START"
    WAIT_FOR_YOU = "WAIT_FOR_YOU"
    WAIT_FOR_MOVE = "WAIT_FOR_MOVE"
    END_YOU_WIN = "END_YOU_WIN"
    END_YOU_LOST = "END_YOU_LOST"
    END_EQUALS = "END_EQUALS"


@dataclass(frozen=True)
class GameConfig:
    num_players: int = 2
    tokens_per_player: int = 4
    board_size: int = 40
    home_stretch_size: int = 4
    dice_sides: int = 6
    max_consecutive_sixes: int = 2


@dataclass(frozen=True)
class GameState:
    tokens: tuple[tuple[int, ...], ...]
    current_player: int
    dice_value: int | None
    consecutive_sixes: int
    game_over: bool
    winner: int | None
    error_count: int
    turn_number: int
    state: CompetitionState


@dataclass(frozen=True)
class MoveRecord:
    turn: int
    player: int
    action: int | None
    dice_value: int
    destination: int
    captured: int | None
    is_extra_turn: bool
    error: bool


@dataclass(frozen=True)
class GameResult:
    winner: int | None
    turn_count: int
    error_count: int


@dataclass(frozen=True)
class Observation:
    game_id: str
    turn_number: int
    player_id: int
    num_players: int
    dice_value: int
    consecutive_sixes: int
    own_tokens: tuple[int, ...]
    opponent_tokens: tuple[tuple[int, ...], ...]
    game_state: str
    game_over: bool
    is_your_turn: bool
    legal_actions: tuple[int, ...]
