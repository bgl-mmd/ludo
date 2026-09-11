# RULE-004 — Legal action generation and validation

**ID:** RULE-004
**Title:** Legal action generation and validation
**Phase:** 2
**Depends on:** RULE-002, RULE-003

## Goal

Produce the set of legal token indices for the current player (spec 04 §5), and validate an arbitrary action.

## Scope

- `get_legal_actions(state, config) -> tuple[int, ...]` — reads `state.current_player` and `state.dice_value`; empty tuple means "no valid move" (`Move(0)`).
- `is_valid_action(state, action, config)` — action is legal, or `action is None` exactly when no legal moves exist.

## Out of scope

- Applying actions, turn transitions, error recording.

## Acceptance criteria

- Generated actions match spec 04 §5 algorithm exactly.
- Empty when no token can move (all blocked / all overshooting).
- `None` is valid only when `legal_actions` is empty.

## Tests

- `test_legal_actions_include_all_valid_moves`, `test_legal_actions_exclude_blocked_destinations`, `test_legal_actions_include_enter_on_6`, `test_legal_actions_exclude_enter_on_non_6`, `test_legal_actions_empty_when_no_moves`, `test_legal_actions_include_move_0_when_empty` (spec 09 §2.3).