# Ludo

## `play_competition.py` — Polling Mode

The bot polls the server at a fixed interval for game state updates.

**Linux (source):**
```bash
PYTHONPATH=src python3 scripts/play_competition.py --game-id game06 --username bot1 --password 123 --bot evasive_mcts --iterations 200 --poll-interval 2
```

**Windows (executable):**
```powershell
play_competition.exe --game-id game06 --username bot1 --password 123 --bot evasive_mcts --iterations 200 --poll-interval 2
```

| Flag | Default | Description |
|------|---------|-------------|
| `--base-url` | `https://rbc.sysx.ir` | Server URL |
| `--game-id` | required | Room name |
| `--username` | required | Your team name |
| `--password` | required | Room password |
| `--bot` | `greedy` | `random`, `greedy`, `mcts`, or `evasive_mcts` |
| `--iterations` | `200` | MCTS iterations (only for `mcts`/`evasive_mcts`) |
| `--seed` | `None` | Random seed (only for `mcts`/`evasive_mcts`) |
| `--players` | `2` | Number of players |
| `--poll-interval` | `1.0` | Seconds between polls |
| `--callback-url` | `None` | Optional callback URL sent with login |

---

## `play_callback.py` — Callback Mode

The server POSTs the game state to your callback URL. This script runs a small HTTP server to receive those callbacks and reply with moves.

**Linux (source):**
```bash
PYTHONPATH=src python3 scripts/play_callback.py --game-id game06 --username bot1 --password 123 --callback-url "http://45.82.138.21:8000/?gamestate={0}" --bot evasive_mcts --iterations 200
```

**Windows (executable):**
```powershell
play_callback.exe --game-id game06 --username bot1 --password 123 --callback-url "http://45.82.138.21:8000/?gamestate={0}" --bot evasive_mcts --iterations 200
```

| Flag | Default | Description |
|------|---------|-------------|
| `--base-url` | `https://rbc.sysx.ir` | Server URL |
| `--game-id` | required | Room name |
| `--username` | required | Your team name |
| `--password` | required | Room password |
| `--callback-url` | required | URL with `{0}` placeholder (replaced by gamestate) |
| `--host` | `0.0.0.0` | Local bind address |
| `--bot` | `greedy` | `random`, `greedy`, `mcts`, or `evasive_mcts` |
| `--iterations` | `200` | MCTS iterations (only for `mcts`/`evasive_mcts`) |
| `--seed` | `None` | Random seed (only for `mcts`/`evasive_mcts`) |
| `--players` | `2` | Number of players |

> The `{0}` in `--callback-url` is required — the server replaces it with the encoded game state. The port in the callback URL determines which port the local server listens on (default `8000`).

---

## Building executables with PyInstaller

Build a single-file executable for each script:

```bash
pyinstaller --onefile --paths src scripts/play_competition.py
pyinstaller --onefile --paths src scripts/play_callback.py
```

The executables are written to `dist/` as `play_competition` / `play_competition.exe` and `play_callback` / `play_callback.exe`. The `--paths src` flag is required so PyInstaller can find the `ludo` package. They accept the same flags as the scripts above.