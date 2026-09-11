# COMP-001 — Board parsing and observation mapping

**ID:** COMP-001
**Title:** Board parsing and observation mapping (pure)
**Phase:** 5
**Depends on:** OBS-001, DOMAIN-001

## Goal

Translate competition REST payloads into typed, bot-ready values (spec 08 §4/§8).

## Scope

- `BoardState` typed container.
- `parse_board(json) -> BoardState` (per-user `begin`/`end`/`tokens`, `dice`, `state`; handle `dice: 0` as "not rolled", OQ-10).
- `parse_observation(board) -> Observation` — includes legal-action generation for `WAIT_FOR_YOU`.
- `parse_result(board) -> GameResult`.
- State mapping per spec 08 §8 table (`WAIT_FOR_YOU`→`is_your_turn=True`, etc.).

## Out of scope

- HTTP, the runner loop, the callback handler.

## Acceptance criteria

- The spec 08 §4 example payloads parse correctly.
- `address` conversion (token index → source position) is correct.
- State mapping matches spec 08 §8.

## Tests

- `test_board_response_parsing`, `test_login_response_parsing`, `test_move_address_conversion`, `test_move_0_for_no_valid_move`, `test_state_mapping_competition_to_engine` (spec 09 §2.8).