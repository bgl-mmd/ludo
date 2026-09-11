# RULE-006 — Turn management

**ID:** RULE-006
**Title:** Turn management (next player, extra turn)
**Phase:** 2
**Depends on:** DOMAIN-001

## Goal

Pure turn-rotation and extra-turn logic (spec 05 §10, spec 03 §3.3).

## Scope

- `next_player(current, config)` — `(current + 1) % num_players`.
- `should_grant_extra_turn(dice_value, consecutive_sixes, config)` — true iff `dice_value == 6` and `consecutive_sixes < config.max_consecutive_sixes` (with `consecutive_sixes` already incremented for the current 6). With the default `max_consecutive_sixes=2` this grants an extra turn only for the first 6 in a sequence; a second consecutive 6 ends the turn. See architecture §7.

## Out of scope

- `apply_action`, dice rolling, error handling.

## Acceptance criteria

- Player alternation works for 2 players.
- First 6 ⇒ extra turn; second consecutive 6 ⇒ no extra turn; non-6 ⇒ no extra turn; `Move(0)` never grants an extra turn even on a 6 (OQ-17).

## Tests

- `test_dice_6_grants_extra_turn`, `test_second_consecutive_6_no_extra_turn`, `test_turn_ends_after_extra_turn`, `test_regular_roll_no_extra_turn` (spec 09).