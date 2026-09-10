# Game Engine Architecture

## 1. Core Design Principles

1. **Pure functions.** State + action → new state. No side effects.
2. **No HTTP dependency.** The engine is a library, not a server.
3. **No bot dependency.** The engine never calls bot code directly.
4. **Deterministic.** Given the same seed, the engine produces the same game.
5. **Immutable state.** Game state is never mutated; new copies are returned.

## 2. Engine API

```python
class GameEngine:
    def __init__(self, config: GameConfig, rng: Random):
        """Initialize engine with configuration and RNG."""
        pass

    def new_game(self, players: list[str]) -> GameState:
        """Create a fresh game with given player names."""
        pass

    def get_legal_actions(self, state: GameState, player: int) -> list[Action]:
        """Return all legal actions for the current player."""
        pass

    def get_observation(self, state: GameState, player: int) -> Observation:
        """Return what a specific player can see."""
        pass

    def roll_dice(self, state: GameState) -> tuple[int, GameState]:
        """Roll the dice, return (value, new_state)."""
        pass

    def apply_action(self, state: GameState, action: Action) -> GameState:
        """Apply an action and return new state. Validates internally."""
        pass

    def is_game_over(self, state: GameState) -> bool:
        """Check if the game has ended."""
        pass

    def get_result(self, state: GameState) -> GameResult:
        """Return the final result of a completed game."""
        pass
```

## 3. Game State

```python
@dataclass(frozen=True)
class GameState:
    # Board state
    tokens: list[list[int]]   # tokens[player][token_idx] = position (0-44+)
    current_player: int       # index of player whose turn it is
    dice_value: int | None    # current dice value (None before roll)
    consecutive_sixes: int    # number of consecutive 6s this turn (0, 1, ...)

    # Game metadata
    game_over: bool
    winner: int | None        # player index, or None
    error_count: int          # total errors recorded

    # Turn tracking
    turn_number: int          # total turns played
    state: CompetitionState   # external competition state enum
```

## 4. Game Configuration

```python
@dataclass
class GameConfig:
    num_players: int = 2
    tokens_per_player: int = 4
    board_size: int = 40       # shared track cells
    home_stretch_size: int = 4 # cells 41-44
    dice_sides: int = 6
    max_consecutive_sixes: int = 2  # [DESIGN] after this, turn ends
```

## 5. Coordinate Conversion (Centralized)

```python
class CoordinateSystem:
    """Handles all coordinate conversions. Single source of truth."""

    def __init__(self, config: GameConfig):
        self.begin_offsets = self._compute_begin_offsets(config)

    def global_to_player(self, global_pos: int, player: int) -> int:
        """Convert global position to player-relative position."""
        pass

    def player_to_global(self, player_pos: int, player: int) -> int:
        """Convert player-relative position to global position."""
        pass

    def _compute_begin_offsets(self, config: GameConfig) -> list[int]:
        """Compute the global start position for each player."""
        # Derived from the board diagram:
        # Player 0: begin = 1
        # Player 1: begin = 21
        pass
```

## 6. Dice Module

```python
class Dice:
    def __init__(self, rng: Random):
        self.rng = rng

    def roll(self) -> int:
        """Return a value from 1 to 6."""
        return self.rng.randint(1, 6)
```

## 7. Rules Engine

```python
class Rules:
    """Encapsulates all game rules. Stateless."""

    @staticmethod
    def is_valid_action(state: GameState, action: Action, dice_value: int) -> bool:
        """Check if an action is legal given the current state and dice."""
        pass

    @staticmethod
    def compute_destination(state: GameState, player: int, action: Action, dice_value: int) -> int:
        """Compute the destination position for a move."""
        pass

    @staticmethod
    def check_capture(state: GameState, player: int, destination: int) -> int | None:
        """Check if a capture occurs at the destination. Return captured player index or None."""
        pass

    @staticmethod
    def check_win(state: GameState, player: int) -> bool:
        """Check if a player has won (all4 tokens in home stretch at position 44)."""
        pass

    @staticmethod
    def get_legal_actions(state: GameState, player: int, dice_value: int) -> list[Action]:
        """Generate all legal actions for a player given the dice value."""
        pass
```

## 8. State Transitions

```python
def apply_action(state: GameState, action: Action) -> GameState:
    """
    Apply an action to the state and return the new state.

    Algorithm:
    1. Validate the action
    2. Compute destination
    3. Check for capture (remove opponent token if present)
    4. Move token to destination
    5. Check win condition
    6. Determine next turn:
       - If dice was 6 and consecutive_sixes < max: extra turn (same player)
       - Else: switch to opponent
    7. Roll new dice for next turn (or use existing if extra turn)
    8. Return new state
    """
    pass
```

## 9. Turn Management

```python
class TurnManager:
    """Manages whose turn it is and turn sequencing."""

    def __init__(self, config: GameConfig):
        self.config = config

    def next_player(self, current: int) -> int:
        """Return the next player index (simple alternation for 2 players)."""
        return (current + 1) % self.config.num_players

    def should_grant_extra_turn(self, dice_value: int, consecutive_sixes: int) -> bool:
        """Determine if the current player gets another turn."""
        if dice_value != 6:
            return False
        return consecutive_sixes < self.config.max_consecutive_sixes
```

## 10. Observation Builder

```python
class ObservationBuilder:
    """Builds observations for each player from the game state."""

    def build(self, state: GameState, player: int) -> Observation:
        """
        Build a player-specific observation:
        - Own token positions (player-relative)
        - Opponent token positions (player-relative)
        - Dice value
        - Game state
        - Legal actions
        - Turn information
        """
        pass
```

## 11. Event Log

```python
@dataclass
class MoveRecord:
    turn: int
    player: int
    action: Action
    dice_value: int
    destination: int
    captured: int | None   # captured player index
    is_extra_turn: bool
    error: bool

class GameLog:
    def __init__(self):
        self.records: list[MoveRecord] = []

    def record(self, move: MoveRecord):
        self.records.append(move)

    def replay(self) -> list[MoveRecord]:
        return list(self.records)
```

## 12. Dependencies

The engine depends only on:
- Standard library (dataclasses, enum, random)
- No external packages
- No HTTP libraries
- No game framework
