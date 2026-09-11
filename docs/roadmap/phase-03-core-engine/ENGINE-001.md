# ENGINE-001 — new_game

**ID:** ENGINE-001
**Title:** new_game — fresh game state
**Phase:** 3
**Depends on:** DOMAIN-001

## Goal

Create a brand-new `GameState` (spec 05 §3).

## Scope

- `new_game(config, player_names)` — all tokens at `0`, `current_player = 0`, `dice_value = None`, `consecutive_sixes = 0`, `game_over = False`, `winner = None`, `error_count = 0`, `turn_number = 0`.

## Out of scope

- Dice rolling, first-player randomization (runner concern, RULE-001/architecture).

## Acceptance criteria

- Matches spec 09 §2.1 initial-state expectations.

## Tests

- `test_initial_state_all_tokens_in_home_yard`, `test_initial_state_dice_is_none`, `test_initial_state_current_player_is_zero`, `test_initial_state_game_not_over` (spec 09).