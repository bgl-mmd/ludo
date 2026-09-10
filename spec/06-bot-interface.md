# Bot Interface and Observation Model

## 1. Bot Interface

A bot is any class that implements the `Bot` interface:

```python
class Bot(ABC):
    @abstractmethod
    def reset(self, player_id: int):
        """Called at the start of a new game.告知 the bot its player index."""
        pass

    @abstractmethod
    def choose_action(self, observation: Observation, legal_actions: list[Action]) -> Action:
        """
        Given an observation and legal actions, return the chosen action.
        Must return exactly one action from legal_actions.
        """
        pass

    def on_game_end(self, result: GameResult):
        """Called when the game ends. Optional override for learning bots."""
        pass
```

### Interface requirements:
- A bot **cannot** mutate game state.
- A bot **must** return an action from the provided `legal_actions` list.
- A bot **must** handle any observation the engine provides.
- The same bot instance can be used across multiple games (reset between games).

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
    own_tokens: list[int]     # 4 positions, each 0-44+
    opponent_tokens: list[list[int]]  # [opponent][token] = position

    # Game state
    game_state: str           # "WAIT_FOR_YOU", "WAIT_FOR_MOVE", etc.
    game_over: bool
    is_your_turn: bool

    # Derived info (computed by engine, not bot)
    legal_actions: list[Action]  # all legal actions for this turn
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

**Source:** [EXPLICIT] "سرور مرکزی بازی اعداد خانهها را جداگانه و به صورت نسبی از زاویه دید هر ربات پردازش میکند"

## 4. Observation for Different Bot Types

### 4.1 Random Bot
```python
class RandomBot(Bot):
    def choose_action(self, observation, legal_actions):
        return random.choice(legal_actions)
```

### 4.2 Greedy/Rule-Based Bot
```python
class GreedyBot(Bot):
    def choose_action(self, observation, legal_actions):
        # Priorities:
        # 1. Capture opponent if possible
        # 2. Enter new token on 6
        # 3. Move token closest to home
        # 4. Move any token
        for action in sorted(legal_actions, key=self._score):
            return action
```

### 4.3 MCTS Bot
```python
class MCTSBot(Bot):
    def choose_action(self, observation, legal_actions):
        # Uses observation to build internal simulation
        # Runs N simulations from current state
        # Returns action with highest win rate
        pass
```

### 4.4 RL Bot
```python
class RLBot(Bot):
    def __init__(self, model):
        self.model = model

    def choose_action(self, observation, legal_actions):
        obs_tensor = self._encode(observation)
        q_values = self.model(obs_tensor)
        # Mask illegal actions
        masked_q = mask(q_values, legal_actions)
        return legal_actions[argmax(masked_q)]
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
1. Bot.__init__()           — bot is created
2. Bot.reset(player_id)     — game starts, bot learns its player index
3. Bot.choose_action(obs)   — called each turn when it's the bot's move
   (repeat step 3 until game ends)
4. Bot.on_game_end(result)  — game over, bot receives final result
5. (optional) Bot.learn()   — for RL bots, update policy after game
```

## 8. Bot as a Plugin

The simulator treats bots as black boxes:

```python
# Create bots
bot1 = RandomBot()
bot2 = GreedyBot()

# Run game
sim = Simulator()
result = sim.run_game([bot1, bot2])
```

No bot-specific code enters the engine. The engine queries the bot via the interface, receives an action, validates it, and applies it.
