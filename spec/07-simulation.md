# Simulation and RL Architecture

## 1. Simulator

The simulator orchestrates complete games without any HTTP dependency:

```python
class Simulator:
    def __init__(self, config: GameConfig):
        self.config = config

    def run_game(self, bots: list[Bot], seed: int = None) -> GameResult:
        """Run a single game with the given bots. Returns the result."""
        rng = Random(seed)
        engine = GameEngine(self.config, rng)
        state = engine.new_game([type(b).__name__ for b in bots])

        for bot in bots:
            bot.reset(state.current_player)

        while not engine.is_game_over(state):
            dice_val, state = engine.roll_dice(state)
            obs = engine.get_observation(state, state.current_player)
            legal = engine.get_legal_actions(state, state.current_player)

            bot = bots[state.current_player]
            action = bot.choose_action(obs, legal)

            state = engine.apply_action(state, action)

        result = engine.get_result(state)
        for bot in bots:
            bot.on_game_end(result)
        return result
```

## 2. Batch Simulation

```python
class BatchSimulator:
    def __init__(self, config: GameConfig, num_workers: int = 1):
        self.config = config
        self.num_workers = num_workers

    def run_batch(self, bots: list[Bot], num_games: int,
                  seeds: list[int] = None) -> list[GameResult]:
        """Run many games, optionally in parallel."""
        if seeds is None:
            seeds = list(range(num_games))

        if self.num_workers == 1:
            return [self._run_single(bots, s) for s in seeds]
        else:
            return self._run_parallel(bots, seeds)

    def _run_parallel(self, bots, seeds):
        """Use multiprocessing to run games in parallel."""
        # Each worker gets its own engine instance
        # Bots must be process-safe or cloned per worker
        pass
```

## 3. Deterministic Reproducibility

Every game is reproducible given the same seed:

```python
# Same seed → same dice rolls → same game
result1 = simulator.run_game([bot_a, bot_b], seed=42)
result2 = simulator.run_game([bot_a, bot_b], seed=42)
assert result1 == result2
```

The seed controls:
- Dice rolls
- Turn order (if randomized)
- Any other source of randomness

## 4. Statistics Collection

```python
class Statistics:
    def __init__(self):
        self.games_played: int = 0
        self.wins: dict[str, int] = defaultdict(int)
        self.losses: dict[str, int] = defaultdict(int)
        self.draws: int = 0
        self.total_turns: list[int] = []
        self.error_counts: list[int] = []
        self.capture_counts: list[int] = []

    def record(self, result: GameResult):
        self.games_played += 1
        if result.winner is not None:
            self.wins[result.winner_name] += 1
        else:
            self.draws += 1
        self.total_turns.append(result.turn_count)
        self.error_counts.append(result.error_count)

    def summary(self) -> dict:
        return {
            "games": self.games_played,
            "win_rate": {k: v / self.games_played for k, v in self.wins.items()},
            "avg_turns": sum(self.total_turns) / len(self.total_turns),
            "avg_errors": sum(self.error_counts) / len(self.error_counts),
        }
```

## 5. Game Recording and Replay

```python
class GameRecorder:
    """Records all actions during a game for later replay."""

    def __init__(self):
        self.frames: list[GameState] = []

    def snapshot(self, state: GameState):
        self.frames.append(deepcopy(state))

    def replay(self) -> list[GameState]:
        return list(self.frames)

    def export(self) -> dict:
        """Export game as JSON for external analysis."""
        pass

class ReplayLoader:
    """Load and replay a recorded game."""

    def load(self, data: dict) -> list[GameState]:
        pass

    def step_through(self, frames: list[GameState]):
        """Iterate through frames, allowing inspection at each step."""
        pass
```

## 6. RL Training Architecture

### 6.1 Environment Interface

The simulator can act as an RL environment:

```python
class LudoEnv:
    """Gym-like interface for RL training."""

    def __init__(self, config: GameConfig):
        self.engine = GameEngine(config)
        self.state = None

    def reset(self, seed=None) -> Observation:
        """Reset the environment and return initial observation."""
        self.state = self.engine.new_game(["rl_bot", "random_bot"])
        return self.engine.get_observation(self.state, 0)

    def step(self, action: Action) -> tuple[Observation, float, bool, dict]:
        """
        Take an action and return (obs, reward, done, info).
        """
        old_state = self.state
        self.state = self.engine.apply_action(self.state, action)
        obs = self.engine.get_observation(self.state, self.state.current_player)
        reward = self._compute_reward(old_state, self.state)
        done = self.engine.is_game_over(self.state)
        return obs, reward, done, {}

    def _compute_reward(self, old: GameState, new: GameState) -> float:
        """Reward function for RL."""
        # Options:
        # +1 for win, -1 for loss, 0 otherwise
        # +0.1 for capture, -0.1 for being captured
        # +0.01 for advancing tokens
        # Shaped reward for progress toward home
        pass
```

### 6.2 Training Loop (Pseudocode)

```python
def train_rl_bot(config, num_episodes=100000):
    env = LudoEnv(config)
    bot = RLBot(model=NeuralNetwork())
    optimizer = Adam(bot.model.parameters())

    for episode in range(num_episodes):
        obs = env.reset(seed=episode)
        done = False

        while not done:
            legal = env.engine.get_legal_actions(env.state, env.state.current_player)
            action = bot.choose_action(obs, legal)
            obs, reward, done, info = env.step(action)

            # Store transition for training
            bot.remember(obs, action, reward, done)

        # Train after each episode (or batch of episodes)
        if episode % batch_size == 0:
            loss = bot.train_step()
            log(episode, loss)
```

### 6.3 Self-Play

For self-play training:
1. Two instances of the same bot play against each other.
2. Both bots learn from the game outcome.
3. Opponent pool stores historical versions of the bot.

```python
class SelfPlayTrainer:
    def __init__(self, config):
        self.opponent_pool = []

    def train(self, num_episodes):
        for ep in range(num_episodes):
            opponent = random.choice(self.opponent_pool) or RandomBot()
            result = simulator.run_game([main_bot, opponent])
            main_bot.learn_from_game(result)
            self.opponent_pool.append(clone(main_bot))
```

## 7. Performance Considerations

### 7.1 In-Memory Simulation
- For small batches (< 10k games): single-process, pure Python
- For medium batches (10k–1M): multiprocessing with shared state
- For large batches (> 1M): consider C extension or Rust engine

### 7.2 Minimizing Overhead
- Pre-compute coordinate conversions
- Use numpy arrays for token positions
- Avoid object creation in hot loops
- Cache legal action computations

### 7.3 Parallel Game Execution
```
┌──────────────┐  ┌──────────────┐  ┌──────────────┐
│   Worker 1   │  │   Worker 2   │  │   Worker N   │
│  Game 1-100  │  │ Game 101-200 │  │ Game ...     │
└──────┬───────┘  └──────┬───────┘  └──────┬───────┘
       │                 │                 │
       └─────────────────┼─────────────────┘
                         │
                ┌────────▼────────┐
                │   Statistics    │
                │   Aggregator    │
                └─────────────────┘
```
