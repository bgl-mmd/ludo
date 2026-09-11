# Game Engine Architecture (Functional)

## 1. Role

The engine is the **local replacement for the competition server**. In simulation mode, the engine does everything the server does: dice rolls, turn management, rules enforcement, win detection. The bot never knows the difference.

The engine is a **library of pure functions**, not a server and not an object. It has no HTTP dependency, no hidden state, and never calls bot code directly.

## 2. Core Design Principles

1. **Pure functions.** `(state, action) -> new state`. No side effects, no mutation.
2. **No HTTP dependency.** The engine is a library, not a server.
3. **No bot dependency.** The engine never calls bot code directly.
4. **Deterministic.** Given the same seed, the engine produces the same game.
5. **Immutable state.** `GameState` is a frozen dataclass; every transition returns a new copy.
6. **No classes, only data + functions.** Classes exist only for data types (`GameState`, `GameConfig`, `Observation`, `GameResult`, `MoveRecord`). All behavior is module-level functions.
7. **Explicit state threading.** State is passed in and returned out. There is no hidden mutable state inside any function.
8. **Faithful to competition rules.** The engine must reproduce the server's behavior so the same bot works against both.

## 3. Engine API

The engine is a module of pure functions. There is no `GameEngine` class.

```python
# engine.py — module of pure functions

def new_game(config: GameConfig, player_names: tuple[str, ...]) -> GameState:
    """Create a fresh game with given player names. Pure."""

def roll_dice(state: GameState, rng: random.Random) -> tuple[GameState, int]:
    """Roll the dice, return (new_state_with_dice_value, value). Pure w.r.t. state."""

def get_legal_actions(state: GameState, config: GameConfig) -> tuple[int, ...]:
    """Return all legal actions (token indices 0-3) for the current player. Pure."""

def get_observation(state: GameState, player: int, config: GameConfig) -> Observation:
    """Return what a specific player can see. Pure."""

def apply_action(state: GameState, action: int | None, config: GameConfig) -> tuple[GameState, MoveRecord]:
    """Apply an action (token index, or None for no valid move) and return (new_state, move_record).
    Validates internally. Pure."""

def is_game_over(state: GameState) -> bool:
    """Check if the game has ended. Pure."""

def get_result(state: GameState, player_names: tuple[str, ...]) -> GameResult:
    """Return the final result of a completed game. Pure."""
```

Key signature differences from an object-oriented design:

| OOP | Functional |
|-----|-----------|
| `engine.roll_dice(state)` (relies on `self.rng`) | `roll_dice(state, rng)` — the RNG is passed explicitly |
| `engine.get_legal_actions(state, player)` | `get_legal_actions(state, config)` — current player comes from state |
| `engine.apply_action(state, action)` (mutates) | `apply_action(state, action, config)` returns `(new_state, MoveRecord)` |
| `GameEngine(config, rng)` (constructed once) | functions take `config` / `rng` as explicit parameters |

There is no `self`. Everything the function needs is in its arguments.

## 4. Game State

```python
@dataclass(frozen=True)
class GameState:
    # Board state
    tokens: tuple[tuple[int, ...], ...]  # tokens[player][token_idx] = position (0-44+)
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

Notes:
- `tokens` is a tuple of tuples (immutable), not a list of lists. Any move must rebuild the whole tuple.
- Because the dataclass is `frozen`, there is no possibility of in-place mutation. `apply_action` must construct a new `GameState`.
- A small helper is allowed for the common rebuild pattern:

```python
def _replace(state: GameState, **changes) -> GameState:
    """Build a new GameState with the given fields changed. Internal helper."""
    return replace(state, **changes)
```

`dataclasses.replace` is the functional equivalent of "mutate one field".

## 5. Game Configuration

```python
@dataclass(frozen=True)
class GameConfig:
    num_players: int = 2
    tokens_per_player: int = 4
    board_size: int = 40       # shared track cells
    home_stretch_size: int = 4 # cells 41-44
    dice_sides: int = 6
    max_consecutive_sixes: int = 2  # [DESIGN] after this, turn ends
```

## 6. Coordinate Conversion (Centralized)

```python
def global_to_player(global_pos: int, player: int, config: GameConfig) -> int:
    """Convert global position to player-relative position. Pure."""

def player_to_global(player_pos: int, player: int, config: GameConfig) -> int:
    """Convert player-relative position to global position. Pure."""

def compute_begin_offsets(config: GameConfig) -> tuple[int, ...]:
    """Compute the global start position for each player. Pure."""
    # Derived from the board diagram:
    # Player 0: begin = 1
    # Player 1: begin = 21
```

The conversion is a set of pure functions keyed on `config`. The begin offsets are derived from `config` by `compute_begin_offsets`; if caching is needed, the caller may memoize — the functions themselves stay pure.

## 7. Dice Module

```python
def create_rng(seed: int | None = None) -> random.Random:
    """Create a seeded RNG. The ONLY source of randomness in the engine."""
    return random.Random(seed)

def roll_dice(state: GameState, rng: random.Random) -> tuple[GameState, int]:
    """Return (new_state, value) where value is from 1 to 6. Pure w.r.t. state."""
    value = rng.randint(1, 6)
    return _replace(state, dice_value=value), value
```

The RNG is **injected** — it is not stored anywhere. The runner owns the RNG and threads it through the loop. `roll_dice` is pure with respect to `state`; the only impurity (consuming the RNG) is contained in the passed-in `rng`.

## 8. Rules Engine

```python
def is_valid_action(state: GameState, action: int | None, config: GameConfig) -> bool:
    """Check if an action (token index) is legal given the current state and dice. Pure."""

def compute_destination(state: GameState, action: int, config: GameConfig) -> int:
    """Compute the destination position for a move. Pure."""

def check_capture(state: GameState, player: int, destination: int) -> int | None:
    """Check if a capture occurs at the destination. Return captured player index or None. Pure."""

def check_win(state: GameState, player: int, config: GameConfig) -> bool:
    """Check if a player has won (all 4 tokens in home stretch at position 44). Pure."""

def get_legal_actions(state: GameState, config: GameConfig) -> tuple[int, ...]:
    """Generate all legal actions (token indices) for the current player. Empty = no valid move. Pure."""
```

No class, no `@staticmethod` wrappers. These are plain module-level functions. `get_legal_actions` reads the current player and dice value from `state`, so it needs no `player` argument.

An action is a **token index `int`** (0–3). The competition's `address` (the token's source position) is *not* part of the action — the runner derives it from the state when building a `Move` request. `None` means "no valid move".

## 9. State Transitions

```python
def apply_action(state: GameState, action: int | None, config: GameConfig) -> tuple[GameState, MoveRecord]:
    """
    Apply an action (token index, or None for no valid move) and return (new_state, move_record).

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

    Never mutates the input — always returns a new GameState.
    """
```

This is the **reducer** of the system: `(state, action) -> (state, record)`. Every game loop iteration reduces down to this single function.

## 10. Turn Management

```python
def next_player(current: int, config: GameConfig) -> int:
    """Return the next player index (simple alternation for 2 players). Pure."""
    return (current + 1) % config.num_players

def should_grant_extra_turn(dice_value: int, consecutive_sixes: int, config: GameConfig) -> bool:
    """Determine if the current player gets another turn. Pure."""
    if dice_value != 6:
        return False
    return consecutive_sixes < config.max_consecutive_sixes
```

## 11. Observation Builder

```python
def build_observation(state: GameState, player: int, config: GameConfig) -> Observation:
    """
    Build a player-specific observation:
    - Own token positions (player-relative)
    - Opponent token positions (player-relative)
    - Dice value
    - Game state
    - Legal actions
    - Turn information
    Pure: state -> observation, no side effects.
    """
```

## 12. Event Log

The event log is an **immutable value**, not a mutable object:

```python
@dataclass(frozen=True)
class MoveRecord:
    turn: int
    player: int
    action: int | None        # token index moved, or None for no-move
    dice_value: int
    destination: int
    captured: int | None   # captured player index
    is_extra_turn: bool
    error: bool

# The log is simply a tuple of records.
# New records are appended with tuple concatenation:
#   new_log = (*log, record)
```

The game loop threads the log as a value:

```python
def run_simulation(bots, config, seed) -> tuple[GameResult, tuple[MoveRecord, ...]]:
    ...
    log: tuple[MoveRecord, ...] = ()
    while not is_game_over(state):
        ...
        state, record = apply_action(state, action, config)
        log = (*log, record)
    ...
```

Replay is just iterating the returned tuple. No `GameLog` class is needed.

## 13. Dependencies

The engine depends only on:
- Standard library (dataclasses, enum, random)
- No external packages
- No HTTP libraries
- No game framework