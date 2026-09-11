# Bot Interface and Observation Model (Functional)

## 1. Bot Interface

A bot is any **callable** that maps an observation to an action:

```python
from typing import Callable

# A bot is a function: observation -> token index (0-3), or None for no valid move.
BotFn = Callable[[Observation], int | None]
```

There is no `Bot` base class, no `reset()`, no `on_game_end()`. A bot is just a function with the signature `Observation -> action`. `None` means "no valid move" (the runner sends `address: "0"` in competition mode).

### Simple bots are pure functions

```python
def random_bot(obs: Observation) -> int | None:
    """Always picks a legal action (or None if none)."""
    import random
    return random.choice(obs.legal_actions) if obs.legal_actions else None

def greedy_bot(obs: Observation) -> int | None:
    """Priorities: capture, enter on 6, move closest to home, move any."""
    legal = obs.legal_actions
    return sorted(legal, key=lambda a: _score(a, obs))[0] if legal else None
```

### Stateful bots are factory closures

Bots that need state (RL models, MCTS, counters) are created by a **factory function** that returns a closure. The state lives in the closure, invisible to the runner:

```python
def make_rl_bot(model, player_id: int) -> BotFn:
    """Factory: returns a bot closure that owns its model + player index."""
    def bot(obs: Observation) -> int:
        obs_tensor = _encode(observation=obs, player_id=player_id)
        q_values = model(obs_tensor)
        masked_q = _mask(q_values, obs.legal_actions)
        return obs.legal_actions[argmax(masked_q)]
    return bot
```

The factory parameter `player_id` replaces the old `Bot.reset(player_id)` call — the player index is bound at creation time.

### Learning bots use caller-side learning

The old `Bot.on_game_end(result)` hook is removed. Instead:

- The runner returns `(result, history)` where `history` is the full event log.
- The **caller** owns learning: after the game, it calls `bot.learn(result)` itself.

```python
result, history = run_simulation(bots, config, seed=42)
main_bot.learn(result)          # caller-side learning
```

This keeps the runner a pure function of its inputs and leaves all side effects (gradient updates, model saving) to the caller.

### Interface requirements:
- A bot **cannot** mutate game state (it never receives it).
- A bot **must** return an action from the provided `legal_actions` list, or `None` if empty.
- A bot **must** handle any observation the runner provides.
- A bot is a pure decision function: `observation → action`. Any memory lives in its closure.
- A bot **never knows** whether it's talking to a real server or a local engine.

### Who owns the game loop?

The **runner** owns the game loop, not the bot. The runner is responsible for:

1. Rolling dice (or receiving dice from server)
2. Building the observation
3. Calling `bot(obs)`
4. Applying the action (to engine or sending to server)
5. Detecting win/loss
6. Advancing turns

## 2. Observation

```python
@dataclass(frozen=True)
class Observation:
    # Game identification
    game_id: str
    turn_number: int

    # Player info
    player_id: int            # this bot's player index
    num_players: int

    # Dice
    dice_value: int           # current dice value (1-6)
    consecutive_sixes: int    # how many consecutive 6s this turn

    # Token positions (player-relative coordinates)
    own_tokens: tuple[int, ...]           # 4 positions, each 0-44+
    opponent_tokens: tuple[tuple[int, ...], ...]  # [opponent][token] = position

    # Game state
    game_state: str           # "WAIT_FOR_YOU", "WAIT_FOR_MOVE", etc.
    game_over: bool
    is_your_turn: bool

    # Derived info (computed by engine, not bot)
    legal_actions: tuple[int, ...]  # legal token indices for this turn (empty = no valid move)
```

## 3. Coordinate System for Bots

All positions in the observation are in **player-relative coordinates**:

- Position `0`: token is in home yard
- Positions `1–40`: token is on the shared track (1 = your start, 40 = your end)
- Positions `41–44`: token is in your home stretch
- Position `> 44`: token has finished

Opponent tokens are also converted to your player-relative view. This means:
- You see opponent tokens as if you were looking from your perspective.
- You cannot directly determine the opponent's true global position.

## 4. Bots as Functions

### 4.1 Random Bot
```python
def random_bot(obs: Observation) -> int | None:
    import random
    return random.choice(obs.legal_actions) if obs.legal_actions else None
```

### 4.2 Greedy/Rule-Based Bot
```python
def make_greedy_bot() -> BotFn:
    def bot(obs: Observation) -> int | None:
        legal = obs.legal_actions
        if not legal:
            return None
        # Priorities:
        # 1. Capture opponent if possible
        # 2. Enter new token on 6
        # 3. Move token closest to home
        # 4. Move any token
        return max(legal, key=lambda a: _score(a, obs))
    return bot
```

### 4.3 MCTS Bot
```python
def make_mcts_bot(iterations: int = 100) -> BotFn:
    """Uses observation to build internal simulations, returns best action."""
    def bot(obs: Observation) -> int | None:
        tree = _build_tree(obs, iterations)
        return tree.best_action()
    return bot
```

### 4.4 RL Bot
```python
def make_rl_bot(model, player_id: int = 0) -> BotFn:
    def bot(obs: Observation) -> int | None:
        obs_tensor = _encode(observation=obs, player_id=player_id)
        q_values = model(obs_tensor)
        masked_q = _mask(q_values, obs.legal_actions)
        return obs.legal_actions[argmax(masked_q)] if obs.legal_actions else None
    return bot
```

## 5. Observation Encoding for RL

The observation should be encoded as a fixed-size tensor for neural network input:

### 5.1 Feature Vector (flat)

```
[own_token_0_pos, own_token_1_pos, own_token_2_pos, own_token_3_pos,   # 4 floats
 opp_token_0_pos, opp_token_1_pos, opp_token_2_pos, opp_token_3_pos,   # 4 floats
 dice_value / 6.0,                                                         # 1 float
 consecutive_sixes / 2.0,                                                  # 1 float
 is_my_turn,                                                               # 1 float
 game_over,                                                                # 1 float
 turn_number / max_turns]                                                  # 1 float
```

Total: 13 features

### 5.2 Alternative: Board-based encoding

```
# 45 cells (0-44), 3 channels:
# Channel 0: own tokens (1 if occupied, 0 otherwise)
# Channel 1: opponent tokens (1 if occupied, 0 otherwise)
# Channel 2: cell type (0=home yard, 1=track, 2=home stretch)
# Shape: (3, 45)
# Plus dice features: (3,) — dice value, consecutive sixes, is_my_turn
```

**[DESIGN]** The specific encoding is left to the implementation. The interface guarantees that the bot receives the same logical observation regardless of encoding.

## 6. Information Asymmetry

What each bot can see:

| Information | Visible? | Notes |
|-------------|----------|-------|
| Own token positions | Yes | In player-relative coordinates |
| Opponent token positions | Yes | Converted to player's view |
| Dice value | Yes | Only when it's your turn |
| Legal actions | Yes | Computed by engine |
| Game state | Yes | State enum |
| Turn number | Yes | Global turn count |
| Opponent's strategy | No | Bot cannot observe opponent's thought process |
| Dice seed | No | Bot cannot predict future rolls |
| Global positions | No | Only player-relative view |

## 7. Bot Lifecycle

```
1. make_<bot_type>(...)      — factory creates the bot closure, binds config
2. bot(obs)                  — called each turn when it's the bot's move
   (repeat step 2 until game ends)
3. run_simulation returns (result, history) — runner is done
4. caller passes result to bot.learn(result) — caller-side learning
```

The runner treats bots as black-box callables. It calls `bot(obs)` with an observation and receives an action. Nothing else.

## 8. Bot as a Plugin

```python
# Create bots
bot1 = make_greedy_bot()
bot2 = make_rl_bot(model, player_id=1)

# Run game
result, history = run_simulation((bot1, bot2), config, seed=42)
```

No bot-specific code enters the engine. The runner queries the bot via the callable, receives an action, validates it, and applies it.