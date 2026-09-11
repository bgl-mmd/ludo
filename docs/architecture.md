# Ludo — Architecture

This document records the architecture for the implementation described by the
specifications in `spec/`. The specs are authoritative; where they are ambiguous
or contradictory, the chosen resolution is recorded here and in the roadmap's
**Open Questions**.

## 1. Scope

**Current scope (to implement):**

- Pure functional Ludo engine (`state + action -> new state`)
- Board/coordinate conversion
- Dice + turn management
- Observation builder and bot interface
- Example bots (random, greedy)
- Simulation runner (single game, batch, statistics, replay/history)
- Competition REST client + runner (parse, HTTP, run)

**Future scope (NOT implemented now, boundary only):**

- RL environment adapter (`make_env` reset/step, `compute_reward`, training loop)
- MCTS bot, RL bot, self-play, opponent pool

The core engine has no knowledge of the RL environment. The RL adapter later
reuses the pure engine functions; it is a separate module above the engine.

## 2. Language & Dependencies

- Python 3.10+ (uses `dataclasses`, `enum`, `typing`, `int | None`).
- **Runtime deps:** standard library only (no HTTP libs, no game framework).
  The competition HTTP client uses `urllib.request`.
- **Dev deps:** `pytest`, `pytest-cov`.
- Layout: `src/` package layout (matches spec `--cov=src`).

## 3. Module Layout

```
src/ludo/            # pure engine — stdlib only, NO HTTP, NO bot dependency
  model.py           # GameConfig, GameState, MoveRecord, GameResult,
                     # Observation, CompetitionState (frozen dataclasses)
  coordinates.py     # compute_begin_offsets, player_to_global, global_to_player
  dice.py            # create_rng, roll_dice
  rules.py           # compute_destination, get_occupant, check_capture,
                     # check_win, get_legal_actions, is_valid_action
  engine.py          # new_game, apply_action, is_game_over, get_result,
                     # next_player, should_grant_extra_turn
  observation.py     # get_observation
  bots.py            # make_random_bot, make_greedy_bot
  simulation.py      # run_simulation, run_batch, aggregate,
                     # export_history, import_history

src/competition/    # IO at the edge — depends on src/ludo
  parsing.py         # BoardState, parse_board, parse_observation, parse_result (pure)
  client.py          # login, get_board, make_move, handle_callback (HTTP)
  runner.py          # run_competition (composes IO + pure parsing)

tests/               # pytest suite (spec 09's literal `spec/tests/` path is
                     # treated as illustrative; tests live in tests/)
```

`src/ludo` depends only on the standard library. `src/competition` depends on
`src/ludo` plus `urllib`. Nothing in `src/ludo` calls a bot or touches HTTP.

## 4. State Model

`GameState` is a frozen dataclass (spec 05 §4):

- `tokens`: `tuple[tuple[int, ...], ...]` — `tokens[player][token]`.
- `current_player: int`
- `dice_value: int | None` — `None` before a roll and after a move is applied.
- `consecutive_sixes: int` — count of 6s in the current turn (see §7).
- `game_over: bool`, `winner: int | None`, `error_count: int`
- `turn_number: int` — increments once per applied action.
- `state: CompetitionState` — external competition state enum.

**Coordinate representation (recorded decision).** Tokens are stored in
**player-relative coordinates** (`0` home yard, `1–40` track, `41–44` home
stretch) per player. This matches the rule/action pseudocode (spec 04/05) that
operates directly on `tokens[player]`, and it makes the home stretch naturally
private to each player (resolving OQ-1/OQ-2: no global home-stretch mapping is
needed). The global frame exists only as a conversion layer used to resolve
cross-player collisions: a destination on the shared track is converted
relative→global→opponent-relative to check occupancy and capture. Home-stretch
cells are never on the shared track, so captures never occur there (per OQ-16).
This is a deliberate deviation from spec 02's "global is the internal
representation"; it is recorded as an open question.

## 5. Action Model

An action is a plain **token index** `int` (0–3), or `None` for "no valid move"
(spec 04). The competition `address` (source cell) is **derived** by the runner,
never part of the action. `None` maps to `address: "0"`.

## 6. State-Transition Model

The system reduces to `state + action -> (state, MoveRecord)`.

```
new_game(config, names)
  -> roll_dice(state, rng)          # runner owns RNG; sets dice_value
  -> get_observation(state, player) # legal_actions computed inside
  -> bot(obs) -> action             # runner never decides for the bot
  -> apply_action(state, action)    # validate, move, capture, win, turn
  -> [repeat] until is_game_over
  -> get_result(state, names)
```

`apply_action` (the reducer) performs, in order:

1. Validate the action (illegal ⇒ record error + force pass, see §8).
2. Compute destination.
3. Capture: if destination holds an opponent token, that token → 0.
4. Move the token to the destination.
5. Check win (all 4 tokens in 41–44 ⇒ win).
6. Determine next turn: extra turn on a first 6; otherwise switch to opponent;
   reset `dice_value` to `None` and reset `consecutive_sixes` on a switch.
7. Build a `MoveRecord` and return `(new_state, record)`.

**Dice rolling is NOT inside `apply_action`.** Spec 05 §9 step 7 ("roll new dice")
conflicts with the runner loop in spec 07, which rolls at the top of every
iteration. Resolution: `apply_action` only resets `dice_value` to `None`; the
runner rolls. This keeps `apply_action` pure with respect to the RNG.

## 7. Turn Flow & Dice

- The runner rolls at the top of each loop iteration: `roll_dice(state, rng)`.
- If the dice is 6, `consecutive_sixes` increments; an extra turn is granted iff
  the (new) count `< config.max_consecutive_sixes` (default `2`). So the first 6
  grants an extra turn; a second consecutive 6 ends the turn (matching
  "second consecutive 6 has no reward"). `Move(0)` always ends the turn (OQ-17).
- On a turn switch, `current_player = next_player(...)` and `consecutive_sixes`
  resets to 0.
- First player is chosen randomly from the seed (OQ-6).
- Randomness is isolated in `dice.create_rng(seed)`; the runner threads one RNG
  through the loop. `roll_dice(state, rng)` is the only consumer of randomness.

## 8. Error Handling

Illegal action (wrong turn, occupied/overshoot destination, `None` when moves
exist): `apply_action` records the error (`error_count += 1`,
`MoveRecord.error = True`) and forces a pass, terminating the turn. This is the
simulator default for OQ-11 (re-prompting is an optional later enhancement).
The exact server recovery behavior is unknown; recorded as an open question.

## 9. Component Responsibilities & Dependencies

| Module            | Responsibilities                                     | Depends on                |
| ----------------- | ---------------------------------------------------- | ------------------------- |
| `model.py`        | All frozen data types / enums                        | —                         |
| `coordinates.py`  | Global ↔ player-relative conversion, begin offsets   | `model.py`                |
| `dice.py`         | Seeded RNG, `roll_dice`                              | `model.py`                |
| `rules.py`        | Destination, occupancy/capture, legal actions, win   | `model.py`, `coordinates` |
| `engine.py`       | `new_game`, `apply_action`, game over, result, turn  | `rules.py`, `dice`        |
| `observation.py`  | Build player-relative `Observation`                  | `rules.py`, `model.py`    |
| `bots.py`         | Random + greedy `BotFn` closures                     | `model.py`                |
| `simulation.py`   | `run_simulation`, `run_batch`, `aggregate`, history  | engine, observation, bots |
| `competition/*`   | REST client, parsing, `run_competition`              | `ludo`, `urllib`          |

Dependency direction is strictly downward; nothing below depends on something
above.

## 10. Testing Boundary

- Tests target **rules**, not implementation details (spec 09).
- Randomness is controllable: `roll_dice(state, rng)` accepts an injected RNG,
  so tests use a seeded `random.Random` or a fixed-value dice source.
- Coverage targets per spec 09 §4.
- Invariants are checked by running many seeded games and asserting: at most one
  token per cell, no backward movement, legal actions always produce valid
  states, every game terminates, and same seed ⇒ same result.

## 11. RL Boundary

The engine exposes everything an RL adapter needs without knowing about RL:
immutable `GameState`, token-index actions, `get_legal_actions`, `apply_action`,
`get_observation`, and a seeded RNG. A future `src/rl/env.py` will build a
Gym-like `reset`/`step` closure pair from these (spec 07 §7) plus a pure
`compute_reward`. **None of this is implemented in the current scope.** The only
work done now is keeping the engine surface sufficient and deterministic for it.

## 12. Recorded Design Decisions

1. Per-player relative token storage; global frame only for cross-player checks.
2. `apply_action` does not roll dice (runner rolls at loop top).
3. Extra turn only for the first 6 in a sequence (`consecutive_sixes < max`).
4. Illegal action ⇒ record error + force pass (simulator default for OQ-11).
5. Random first player, chosen from the seed.
6. Bots are closures; random bot is `make_random_bot(seed=None)` so simulation
   can be deterministic (spec 06's module-level `random_bot` uses global state).
7. `tests/` at repo root (spec 09's `spec/tests/` is illustrative).
8. Competition client uses stdlib `urllib`; uses the literal `Borad` spelling
   (OQ-7) and accepts `address` as int or string (OQ-8).
