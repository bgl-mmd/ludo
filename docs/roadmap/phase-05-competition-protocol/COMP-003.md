# COMP-003 — Competition runner and callback handler

**ID:** COMP-003
**Title:** Competition runner and callback handler
**Phase:** 5
**Depends on:** COMP-002

## Goal

Play a full game against the real server with the same bot interface as the simulator (spec 08 §8/§9).

## Scope

- `run_competition(bot, base_url, game_id, username, password, config) -> GameResult`: login, poll until `WAIT_FOR_YOU`, build observation, call bot, convert to address, `make_move`, poll, terminate on `END_*`.
- `handle_callback(state, bot, base_url, token)` for callback-based play.

## Out of scope

- The competition server itself, deployment, credentials management.

## Acceptance criteria

- Loop structure mirrors `run_simulation` (spec 07 §1 vs §8).
- A mock client drives the runner through a full scripted game.

## Tests

- Runner loop against a mocked client (login → several turns → terminal state).
- `test_callback_url_state_replacement` (spec 09 §2.8).