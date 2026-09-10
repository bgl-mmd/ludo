# Testing Strategy

## 1. Test Philosophy

Tests should verify **game rules** rather than implementation details. A test that checks a rule will remain valid even if the implementation is refactored.

## 2. Test Categories

### 2.1 Unit Tests — Rules Engine

#### Initial State
```
test_initial_state_all_tokens_in_home_yard
test_initial_state_dice_is_none
test_initial_state_current_player_is_zero
test_initial_state_game_not_over
```

#### Movement Rules
```
test_token_moves_forward_by_dice_value
test_token_on_track_1_to_40
test_token_cannot_move_backward
test_token_at_40_cannot_move_beyond_home_stretch
```

#### Entering the Board
```
test_token_enters_board_on_dice_6
test_token_at_home_cannot_enter_on_non_6
test_entering_board_moves_to_position_1
test_entering_board_blocked_if_position_1_occupied_by_self
```

#### Capturing
```
test_capturing_opponent_returns_opponent_to_0
test_own_token_blocks_destination
test_cannot_move_to_cell_occupied_by_self
test_multiple_opponents_captured_independently
```

#### Home Stretch
```
test_token_transitions_to_home_stretch_after_40
test_token_in_home_stretch_must_roll_exact_to_finish
test_overshooting_home_stretch_is_illegal
test_token_at_44_is_finished
```

#### Win Condition
```
test_win_when_all_4_tokens_at_44
test_no_win_with_3_tokens_at_44
test_win_detected_after_move
```

#### No Valid Move
```
test_no_valid_move_returns_move_0
test_all_tokens_blocked_by_self
test_all_tokens_overshooting
```

#### Six and Extra Turn
```
test_dice_6_grants_extra_turn
test_second_consecutive_6_no_extra_turn
test_turn_ends_after_extra_turn
test_regular_roll_no_extra_turn
```

### 2.2 Unit Tests — Coordinate Conversion

```
test_global_to_player_identity
test_player_to_global_identity
test_global_to_player_wraparound
test_player_to_global_wraparound
test_home_yard_always_zero
test_home_stretch_positions
test_begin_end_offsets_for_each_player
```

### 2.3 Unit Tests — Legal Action Generation

```
test_legal_actions_include_all_valid_moves
test_legal_actions_exclude_blocked_destinations
test_legal_actions_include_enter_on_6
test_legal_actions_exclude_enter_on_non_6
test_legal_actions_empty_when_no_moves
test_legal_actions_include_move_0_when_empty
```

### 2.4 Unit Tests — State Machine

```
test_state_transitions_normal_turn
test_state_transitions_on_6_extra_turn
test_state_transitions_on_second_6
test_state_transitions_on_win
test_state_transitions_on_loss
test_state_not_changed_by_illegal_action
```

### 2.5 Integration Tests — Full Games

```
test_game_completes_with_random_bots
test_game_always_has_a_winner
test_game_deterministic_with_same_seed
test_game_records_all_moves
test_game_no_errors_with_valid_bots
```

### 2.6 Property/Invariant Tests

```
test_invariant_at_most_one_token_per_cell
test_invariant_tokens_never_move_backward
test_invariant_illegal_action_never_mutates_state
test_invariant_completed_game_rejects_moves
test_invariant_player_cannot_see_other_player_coordinates
test_invariant_legal_actions_subset_of_all_actions
test_invariant_each_legal_action_produces_valid_state
test_invariant_game_eventually_ends
```

### 2.7 Bot Tests

```
test_random_bot_always_returns_legal_action
test_greedy_bot_always_returns_legal_action
test_bot_cannot_return_action_not_in_legal_actions
test_bot_reset_between_games
test_bot_receives_valid_observation
```

### 2.8 Competition Protocol Tests

```
test_login_request_format
test_login_response_parsing
test_board_request_format
test_board_response_parsing
test_move_request_format
test_move_address_conversion
test_move_0_for_no_valid_move
test_callback_url_state_replacement
test_state_mapping_competition_to_engine
```

### 2.9 Simulation Tests

```
test_batch_simulation_completes
test_statistics_correctly_aggregate
test_replay_matches_original_game
test_deterministic_replay
test_parallel_simulation_same_results
```

## 3. Test Data

### 3.1 Known Board States

Provide pre-defined game states for testing specific scenarios:

```python
@pytest.fixture
def initial_state():
    """Fresh game with all tokens in home yards."""

@pytest.fixture
def mid_game_state():
    """Game with tokens on the board."""

@pytest.fixture
def capturing_state():
    """State where a capture is possible."""

@pytest.fixture
def home_stretch_state():
    """State with tokens near the end."""

@pytest.fixture
def no_moves_state():
    """State where no token can move with current dice."""

@pytest.fixture
def winning_state():
    """State where one move wins the game."""
```

### 3.2 Deterministic Dice

For testing, use a controlled RNG:

```python
class FixedDice:
    """Dice that returns pre-determined values."""
    def __init__(self, values: list[int]):
        self.values = values
        self.index = 0

    def roll(self) -> int:
        val = self.values[self.index]
        self.index = (self.index + 1) % len(self.values)
        return val
```

## 4. Coverage Targets

| Component | Minimum Coverage |
|-----------|-----------------|
| Rules engine | 100% |
| Coordinate conversion | 100% |
| State machine | 100% |
| Legal action generation | 100% |
| Bot interface | 90% |
| Simulation | 80% |
| Competition adapter | 80% |

## 5. Test Execution

```bash
# Run all tests
pytest spec/tests/ -v

# Run with coverage
pytest spec/tests/ --cov=src --cov-report=term-missing

# Run only property tests
pytest spec/tests/ -m property

# Run only integration tests
pytest spec/tests/ -m integration
```

## 6. CI Integration

Tests should run automatically on every commit:
1. Unit tests (fast, < 10s)
2. Integration tests (< 60s)
3. Property tests (< 120s)
4. Full simulation batch (< 300s)
