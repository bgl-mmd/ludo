# RULE-003 — Occupancy and capture

**ID:** RULE-003
**Title:** Occupancy and capture
**Phase:** 2
**Depends on:** DOMAIN-001, DOMAIN-002

## Goal

Cross-player cell occupancy and capture resolution (spec 02 §7).

## Scope

- `get_occupant(state, player, position, config)` → `SAME_PLAYER`, `OPPONENT`, or empty.
- `check_capture(state, player, destination, config)` → captured opponent player index, or `None`. Uses coordinate conversion to check the opponent's view of a shared-track destination.
- Enforcement of "exactly one token per cell": self tokens block; opponent tokens are removed to `0`.
- Home-stretch cells (`41–44`) are private: no opponent can occupy them, so no capture occurs there (architecture §4).

## Out of scope

- Legal-action generation, applying moves, turn flow.

## Acceptance criteria

- Moving onto an opponent cell removes that opponent token to `0`.
- A cell occupied by a same-player token is blocked (cannot move there).
- Independent captures are resolved per destination.
- No capture on home-stretch positions.

## Tests

- `test_capturing_opponent_returns_opponent_to_0`, `test_own_token_blocks_destination`, `test_cannot_move_to_cell_occupied_by_self`, `test_multiple_opponents_captured_independently`, home-stretch no-capture.