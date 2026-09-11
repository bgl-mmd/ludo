# COMP-002 — Competition HTTP client

**ID:** COMP-002
**Title:** Competition HTTP client (IO at the edge)
**Phase:** 5
**Depends on:** COMP-001

## Goal

Minimal REST client for `Login`, `Borad`, `Move` (spec 08 §2–§5).

## Scope

- `login(base_url, game_id, username, password, callback_url=None) -> token`.
- `get_board(base_url, token) -> BoardState`.
- `make_move(base_url, token, address)` — `address` sent as int for a token move and string `"0"` for no-move (OQ-8); literal `Borad` spelling (OQ-7).
- HTTP via `urllib.request`; timeouts and non-200 handling recorded as errors.

## Out of scope

- The game loop, the callback handler, any engine logic.

## Acceptance criteria

- Request bodies match spec 08 examples (mock transport).
- Responses are parsed through COMP-001.
- No engine/rule code lives in this module.

## Tests

- `test_login_request_format`, `test_board_request_format`, `test_move_request_format` (spec 09 §2.8) using a mocked HTTP transport.