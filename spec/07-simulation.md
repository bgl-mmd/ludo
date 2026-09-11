# Simulation and RL Architecture (Functional)

## 1. Simulation Runner

The simulation runner is a **function** that wraps the engine and owns the game loop. It does everything the competition server does, but locally. It threads immutable state through the loop and returns `(result, history)` — nothing is mutated, nothing is hidden.

```python
def run_simulation(bots: tuple[BotFn, ...],
                   config: GameConfig,
                   seed: int | None = None) -> tuple[GameResult, tuple[MoveRecord, ...]]:
    """
    Run a complete local game. Returns (result, history).
    Pure with respect to its inputs: same bots + config + seed -> same result.
    """
    rng = create_rng(seed)
    state = new_game(config, tuple(b.__name__ for b in bots))
    log: tuple[MoveRecord, ...] = ()

    # Game loop — the runner owns this completely.
    # Each iteration rebinds `state` and `log` to new values; nothing is mutated.
    while not is_game_over(state):
        # 1. Roll dice (local, seeded)
        state, _ = roll_dice(state, rng)

        # 2. Build observation for current player
        player = state.current_player
        obs = get_observation(state, player, config)

        # 3. Ask bot for action (legal actions are inside the observation)
        action = bots[player](obs)

        # 4. Apply action to engine -> new state + move record
        state, record = apply_action(state, action, config)
        log = (*log, record)

    # 5. Game over — collect result
    result = get_result(state, tuple(b.__name__ for b in bots))
    return result, log
```

The same bot code works against the real server runner:

```python
def run_competition(bot: BotFn,
                    base_url: str,
                    game_id: str,
                    username: str,
                    password: str,
                    config: GameConfig) -> GameResult:
    """
    Run a complete game against the server.
    IO (HTTP) happens inside this function; game logic stays pure.
    """
    # 1. Login
    token = login(base_url, game_id, username, password)

    # 2. Poll until game starts
    board = get_board(base_url, token)
    while board.state in ("NONE", "WAIT_FOR_START"):
        board = get_board(base_url, token)

    # 3. Game loop
    while board.state not in ("END_YOU_WIN", "END_YOU_LOST", "END_EQUALS"):
        if board.state == "WAIT_FOR_YOU":
            # Server already rolled dice — it's in the board response
            obs = parse_observation(board)          # pure: board json -> observation
            legal = obs.legal_actions
            action = bot(obs) if legal else None     # pure: observation -> action

            # Convert token index -> competition address (source position), then send (IO)
            address = obs.own_tokens[action] if action is not None else "0"
            make_move(base_url, token, address)

        # Poll for next state (IO)
        board = get_board(base_url, token)

    return parse_result(board)                       # pure: board -> result
```

**Key insight:** Both runners have the same structure. The difference:
- `run_simulation`: calls `roll_dice()`, `get_observation()`, `apply_action()`
- `run_competition`: calls `get_board()`, `make_move()`

The bot sees the same `Observation` and `Action` in both cases.

## 2. What the Runner Owns

| Responsibility | Simulation Runner | Competition Runner |
|---------------|-------------------|-------------------|
| Dice rolls | `roll_dice(state, rng)` | Server generates dice |
| Turn tracking | engine tracks `current_player` | Server tracks turns |
| Legal actions | `get_legal_actions(state, config)` | Server knows legal moves |
| Observation | `get_observation(state, player, config)` | `parse_observation(board)` |
| Action apply | `apply_action(state, action, config)` | `make_move(base_url, token, addr)` |
| Win detection | `is_game_over(state)` | Server sets state to `END_*` |
| Captures | engine handles internally | Server handles internally |

## 3. Batch Simulation

```python
def run_batch(bot_factories: tuple[Callable[[int], BotFn], ...],
              config: GameConfig,
              seeds: tuple[int, ...],
              num_workers: int = 1) -> tuple[GameResult, ...]:
    """Run many games, optionally in parallel. Pure composition of run_simulation."""
    run_one = lambda seed: run_simulation(
        tuple(f(i) for i, f in enumerate(bot_factories)), config, seed
    )[0]

    if num_workers == 1:
        return tuple(run_one(seed) for seed in seeds)
    else:
        with multiprocessing.Pool(num_workers) as pool:
            return tuple(pool.map(run_one, seeds))
```

Each worker gets its own RNG (seeded) and engine functions; bots are recreated per game by the factories. Parallelism is `map` over seeds — a pure functional pattern.

## 4. Deterministic Reproducibility

Every game is reproducible given the same seed:

```python
result1, _ = run_simulation((bot_a, bot_b), config, seed=42)
result2, _ = run_simulation((bot_a, bot_b), config, seed=42)
assert result1 == result2
```

The seed controls:
- Dice rolls
- Turn order (if randomized)
- Any other source of randomness

## 5. Statistics Collection

```python
def aggregate(results: tuple[GameResult, ...]) -> dict:
    """
    Fold a collection of results into aggregate statistics.
    Pure: results -> summary dict.
    """
    n = len(results)
    wins: dict[str, int] = defaultdict(int)
    draws = 0
    total_turns = 0
    total_errors = 0

    for r in results:
        if r.winner is not None:
            wins[r.winner_name] += 1
        else:
            draws += 1
        total_turns += r.turn_count
        total_errors += r.error_count

    return {
        "games": n,
        "win_rate": {k: v / n for k, v in wins.items()},
        "draws": draws,
        "avg_turns": total_turns / n,
        "avg_errors": total_errors / n,
    }
```

No `Statistics` class — aggregation is a fold (`reduce`) over the results.

## 6. Game Recording and Replay

Recording needs no special class. The runner already returns the event log as an immutable tuple:

```python
def export_history(log: tuple[MoveRecord, ...]) -> dict:
    """Export a game history as JSON for external analysis. Pure."""

def import_history(data: dict) -> tuple[MoveRecord, ...]:
    """Load a previously exported history. Pure."""

def step_through(log: tuple[MoveRecord, ...]):
    """Iterate through records, allowing inspection at each step."""
    return iter(log)   # or any other pure traversal
```

## 7. RL Training Architecture

### 7.1 Environment Interface

The simulation runner can act as an RL environment via a **closure pair** produced by a factory:

```python
def make_env(config: GameConfig, seed: int | None = None) -> tuple[Callable, Callable]:
    """
    Factory returning (reset_fn, step_fn) — a Gym-like interface built from closures.
    The RNG and current state live inside the closures.
    """
    rng = create_rng(seed)
    state = None

    def reset(seed: int | None = None) -> Observation:
        nonlocal rng, state
        rng = create_rng(seed)
        state = new_game(config, ("rl_bot", "random_bot"))
        return get_observation(state, 0, config)

    def step(action: int | None) -> tuple[Observation, float, bool, dict]:
        nonlocal state
        old_state = state
        state, _ = apply_action(state, action, config)
        obs = get_observation(state, state.current_player, config)
        reward = compute_reward(old_state, state)
        done = is_game_over(state)
        return obs, reward, done, {}

    return reset, step
```

### 7.2 Reward Function (pure)

```python
def compute_reward(old: GameState, new: GameState) -> float:
    """Reward function for RL. Pure: (old, new) -> float."""
    # Options:
    # +1 for win, -1 for loss, 0 otherwise
    # +0.1 for capture, -0.1 for being captured
    # +0.01 for advancing tokens
    # Shaped reward for progress toward home
```

### 7.3 Training Loop (Pseudocode)

```python
def train_rl_bot(config, num_episodes=100000):
    model = NeuralNetwork()
    bot = make_rl_bot(model, player_id=0)
    optimizer = Adam(model.parameters())
    reset_env, step_env = make_env(config)

    for episode in range(num_episodes):
        obs = reset_env(seed=episode)
        done = False

        while not done:
            legal = obs.legal_actions
            action = bot(obs)
            obs, reward, done, info = step_env(action)

            # Store transition for training
            remember(obs, action, reward, done)

        # Train after each episode (or batch of episodes)
        if episode % batch_size == 0:
            loss = train_step(model, optimizer)
            log(episode, loss)
```

### 7.4 Self-Play

For self-play training:
1. Two instances of the same bot play against each other.
2. Both bots learn from the game outcome (caller-side learning).
3. Opponent pool stores historical versions of the bot.

```python
def self_play_train(config, main_bot: BotFn, num_episodes: int, opponent_pool: list):
    for ep in range(num_episodes):
        opponent = random.choice(opponent_pool) or make_random_bot()
        result, _ = run_simulation((main_bot, opponent), config, seed=ep)
        main_bot.learn(result)              # caller-side learning
        opponent_pool.append(clone(main_bot))
```

## 8. Performance Considerations

### 8.1 In-Memory Simulation
- For small batches (< 10k games): single-process, pure Python
- For medium batches (10k–1M): multiprocessing with shared state
- For large batches (> 1M): consider C extension or Rust engine

### 8.2 Minimizing Overhead
- Pre-compute coordinate conversions
- Use numpy arrays for token positions
- Avoid object creation in hot loops
- Cache legal action computations

### 8.3 Parallel Game Execution
```
┌──────────────┐  ┌──────────────┐  ┌──────────────┐
│   Worker 1   │  │   Worker 2   │  │   Worker N   │
│  Game 1-100  │  │ Game 101-200 │  │ Game ...     │
└──────┬───────┘  └──────┬───────┘  └──────┬───────┘
       │                 │                 │
       └─────────────────┼─────────────────┘
                         │
                ┌────────▼────────┐
                │   aggregate()   │
                │   (pure fold)   │
                └─────────────────┘
```