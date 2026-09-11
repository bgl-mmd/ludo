# COMP-003 — Competition runner and callback handler

**ID:** COMP-003
**Title:** Competition runner and callback handler
**Phase:** 5
**Depends on:** COMP-002

## Goal

Play a full game against the real server with the same bot interface as the simulator (spec 08 §8/§9).

## Scope

- `run_competition(bot, base_url, game_id, username, password, config, poll_interval, callback_url=None) -> GameResult`: login (with optional callback URL), poll until `WAIT_FOR_YOU`, build observation (for the logged-in user's slot), call bot, convert to address, `make_move`, poll, terminate on `END_*`.
- `handle_callback(state, bot, base_url, token, username)` for callback-based play.
- `callback_server.process_callback(...)` and `callback_server.run_callback_server(host, port, bot, base_url, token, username)` — an HTTP endpoint that receives the game server's state-change callbacks, makes a move on `WAIT_FOR_YOU`, and reports the result on `END_*`.
- `scripts/play_callback.py` — registers a `callbackUrl` at login and serves callbacks until the game ends.

## Out of scope

- The competition server itself, deployment, credentials management.

## Acceptance criteria

- Loop structure mirrors `run_simulation` (spec 07 §1 vs §8).
- A mock client drives the runner through a full scripted game.

## Tests

- Runner loop against a mocked client (login → several turns → terminal state).
- `test_callback_url_state_replacement` (spec 09 §2.8).