# Scripts

Small command-line tools for running games with the example bots. All scripts
are thin wrappers over the pure functions in `src/ludo/` and `src/competition/`.

The package is not installed, so always run with `PYTHONPATH=src`:

```
PYTHONPATH=src python3 scripts/<script>.py ...
```

## `scripts/play.py` — local simulator games

Runs games locally with `run_simulation` / `run_batch` (SIM-001/002) and prints
`aggregate` statistics (SIM-003). Fully offline and deterministic.

### Usage

```
PYTHONPATH=src python3 scripts/play.py                    # one greedy vs random game
PYTHONPATH=src python3 scripts/play.py --bot0 greedy --bot1 greedy
PYTHONPATH=src python3 scripts/play.py --batch --games 50 --workers 4 --seed 0
```

### Options

| Option          | Default | Description                                        |
| --------------- | ------- | -------------------------------------------------- |
| `--bot0`        | `greedy`| Bot factory for player 0 (`greedy` or `random`)    |
| `--bot1`        | `random`| Bot factory for player 1 (`greedy` or `random`)    |
| `--seed`        | `42`    | RNG seed; also the first seed in batch mode        |
| `--players`     | `2`     | Number of players in the game                      |
| `--batch`       | off     | Run a batch of games instead of a single game      |
| `--games`       | `50`    | Number of games in batch mode                      |
| `--workers`     | `1`     | Parallel workers for `run_batch` (`>1` uses a pool)|

### Output

Single game:

```
game: winner=p0 turns=124 errors=0 moves=124
```

Batch mode:

```
games=20 draws=0
win_rate={0: 0.8, 1: 0.2}
avg_turns=146.2 avg_errors=0.00
```

Notes:

- Random bots need a seed (`make_random_bot(seed)`); results are
  deterministic for the same `bots + config + seed`.
- In batch mode with `--workers > 1`, bot factories must stay picklable —
  `scripts/play.py` uses module-level factories for this reason.

## `scripts/play_competition.py` — play against the competition server

Plays a single game against the live competition server using
`run_competition` (COMP-003). Uses the polling client (COMP-002). Requires a
running server, an existing game room, and valid credentials.

### Usage

```
PYTHONPATH=src python3 scripts/play_competition.py \
    --game-id game-room-1 --username MyTeam --password secret

PYTHONPATH=src python3 scripts/play_competition.py \
    --base-url http://localhost:8000 --game-id game-room-1 \
    --username MyTeam --password secret --bot random
```

### Options

| Option          | Default                | Description                                        |
| --------------- | ---------------------- | -------------------------------------------------- |
| `--base-url`    | `https://rbc.sysx.ir`  | Server base URL                                    |
| `--game-id`     | required               | Game room name (must exist on the server)          |
| `--username`    | required               | Bot team name                                      |
| `--password`    | required               | Bot password                                       |
| `--bot`         | `greedy`               | Bot used for this player (`greedy` or `random`)    |
| `--players`     | `2`                    | Number of players in the game                      |
| `--poll-interval`| `1.0`                 | Seconds between `get_board` polls                  |

### Output

```
game over: winner=p0 turns=124 errors=0
```

Notes:

- The game only starts once **at least two bots** have joined the room; while
  waiting, the script polls the board every `--poll-interval` seconds.
- `--base-url` may point at a local mock server for testing.
- Errors (bad login, non-200 response, timeout) raise
  `competition.client.CompetitionError`.
- The server owns the rules and dice; the bot only receives observations and
  makes moves.