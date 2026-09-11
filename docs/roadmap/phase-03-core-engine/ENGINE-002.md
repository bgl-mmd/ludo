# ENGINE-002 — apply_action (state reducer)

**ID:** ENGINE-002
**Title:** apply_action — the state reducer
**Phase:** 3
**Depends on:** RULE-002, RULE-003, RULE-004, RULE-005, RULE-006

## Goal

The single `(state, action) -> (new_state, MoveRecord)` reducer (spec 05 §9, spec 03 §4). This is the heart of the vertical slice.

## Scope

- `apply_action(state, action, config) -> tuple[GameState, MoveRecord]`:
  1. Validate (`is_valid_action`); illegal ⇒ record error and force a pass.
  2. Compute destination (`RULE-002`).
  3. Resolve capture / self-block (`RULE-003`).
  4. Move the token (rebuild the immutable `tokens` tuple).
  5. Check win (`RULE-005`).
  6. Determine next turn (`RULE-006`): extra turn keeps the player; otherwise switch to the next player and reset `consecutive_sixes`; `dice_value` reset to `None` (runner rolls next, architecture §6).
  7. Increment `turn_number`; build and return `MoveRecord`.
- `None` (no valid move) ends the turn immediately (OQ-17), no extra turn.
- Never mutates the input state.

## Out of scope

- Dice rolling (runner responsibility), observation building, result building.

## Acceptance criteria

- Every row of the spec 04 §9 summary table transitions correctly.
- A 6 grants one extra turn; a second consecutive 6 ends the turn.
- Illegal actions increment `error_count` and produce `MoveRecord.error=True` without throwing.
- Input state is never mutated; win sets `game_over`/`winner`.

## Tests

- Normal move, capture, enter-on-6, home-stretch transitions, overshoot rejection, self-block rejection, `Move(0)` pass, extra turn, second-6, `test_state_not_changed_by_illegal_action`, `test_state_transitions_*` (spec 09 §2.4), plus all spec 09 §2.1 movement/capture/home-stretch/win/no-valid-move/six-and-extra-turn cases.