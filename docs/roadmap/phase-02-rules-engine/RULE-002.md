# RULE-002 — Destination computation

**ID:** RULE-002
**Title:** Destination computation
**Phase:** 2
**Depends on:** DOMAIN-001

## Goal

Pure position arithmetic per spec 04 §8/§9 — where a token lands for a given dice value, independent of occupancy.

## Scope

- `compute_destination(state, player, token_index, config)`:
  - Home yard token (`0`): legal only when dice `== 6` → destination `1`.
  - Track token (`1–40`): `dest = pos + dice`; `1..40` → track, `41..44` → home stretch entry, `>44` → illegal (overshoot).
  - Home-stretch token (`41–43`): `dest = pos + dice`; `≤44` legal, `>44` illegal (overshoot).
- Returns the destination, or an explicit "illegal" marker (e.g. `None`).

## Out of scope

- Occupancy checks, self-blocks, captures, legal-action generation.

## Acceptance criteria

- Mapping matches the spec 04 §9 summary table for every row.
- Overshooting is illegal (`None`). Entering requires exactly 6.
- Example from spec 04 §8.2: token at 39, dice 3 → 42.

## Tests

- `test_token_moves_forward_by_dice_value`, `test_token_on_track_1_to_40`, `test_token_enters_board_on_dice_6`, `test_token_at_home_cannot_enter_on_non_6`, `test_entering_board_moves_to_position_1`, `test_token_transitions_to_home_stretch_after_40`, `test_overshooting_home_stretch_is_illegal`, `test_token_at_44_is_finished`, `test_token_cannot_move_backward` (spec 09).