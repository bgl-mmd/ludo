# Game State Machine

## 1. Competition States

These are the states defined by the competition specification.

| State | Description | Who can act |
|-------|-------------|-------------|
| `NONE` | Lobby incomplete, at least two bots not yet registered | Nobody |
| `WAIT_FOR_START` | Game waiting for supervisor approval to start | Nobody |
| `WAIT_FOR_YOU` | Waiting for YOUR move (it is your bot's turn) | Your bot |
| `WAIT_FOR_MOVE` | Waiting for OPPONENT's move (opponent's turn) | Opponent bot |
| `END_YOU_WIN` | Game over, your bot won | Terminal |
| `END_YOU_LOST` | Game over, opponent bot won | Terminal |
| `END_EQUALS` | Game ended as a draw (not common in 1405) | Terminal |

## 2. State Transitions

```
                         ┌──────────┐
                         │   NONE   │
                         └────┬─────┘
                              │ (enough bots registered)
                              ▼
                     ┌────────────────┐
                     │ WAIT_FOR_START │
                     └────────┬───────┘
                              │ (supervisor approves)
                              ▼
                   ┌─────────────────────┐
              ┌───►│     WAIT_FOR_YOU    │◄───┐
              │    └─────────┬───────────┘    │
              │              │                 │
              │              │ (your bot      │ (dice = 6:
              │              │  makes move)   │  extra turn)
              │              ▼                │
              │    ┌─────────────────────┐    │
              │    │   WAIT_FOR_MOVE     │────┘
              │    └─────────┬───────────┘
              │              │
              │              │ (opponent makes move)
              │              │ (dice = 6: extra turn
              │              │  stays with opponent)
              │              ▼
              │    ┌─────────────────────┐
              │    │   WAIT_FOR_YOU      │
              │    └─────────────────────┘
              │
              │ (win/loss detected)
              │
    ┌─────────┴──────────┬──────────────────┐
    ▼                    ▼                  ▼
┌──────────┐   ┌──────────────┐   ┌──────────────┐
│END_YOU_WIN│   │ END_YOU_LOST │   │ END_EQUALS   │
└──────────┘   └──────────────┘   └──────────────┘
```

## 3. Detailed Transition Rules

### 3.1 Game Start

1. Bots register via Login. State is `NONE`.
2. When enough bots are registered (minimum 2), state → `WAIT_FOR_START`.
3. When supervisor approves, dice is rolled for the first player. State → `WAIT_FOR_YOU` or `WAIT_FOR_MOVE`.

**[DESIGN]** First player determination: random or fixed order? Not specified.

### 3.2 Normal Turn (No 6)

1. State is `WAIT_FOR_YOU`.
2. Dice is rolled (value 1–5, or 6 on first roll of a turn).
3. Bot receives observation with dice value and legal actions.
4. Bot makes a move (or `Move(0)` if no valid move).
5. Engine validates and applies the move.
6. State → `WAIT_FOR_MOVE` (opponent's turn).

### 3.3 Turn with Dice = 6

1. State is `WAIT_FOR_YOU`.
2. Dice is rolled, value = 6.
3. Bot makes a move.
4. **After the move, the same player gets another turn** (dice is rolled again).
5. State stays `WAIT_FOR_YOU` for the same player.
6. **If the second consecutive dice is also 6:** the extra turn is NOT granted. Turn passes to opponent.
7. **[DESIGN]** What happens on a third consecutive 6? The spec only mentions "second consecutive 6 has no reward." Options:
   - Third 6 is treated like a normal roll (most likely)
   - Third 6 also loses the turn
   - The spec implies only one replay is ever granted per "sequence" (i.e., max 2 rolls per turn: first 6 gets replay, second 6 does not)

### 3.4 No Valid Move

1. State is `WAIT_FOR_YOU`.
2. Dice is rolled.
3. No token can legally move with this dice value.
4. Bot must call `Move(0)`.
5. Turn passes to opponent.

### 3.5 Game End

1. After each move, the engine checks if any player has filled all 4 home stretch cells.
2. If yes: state → `END_YOU_WIN` or `END_YOU_LOST` for each player's perspective.
3. State → `END_EQUALS` only on server critical error (not through normal play in 1405).

## 4. Turn Lifecycle (Engine Internal)

The engine's internal turn lifecycle is richer than the competition states:

```
DICE_ROLLED
    │
    ├── Has legal moves?
    │   ├── Yes → AWAITING_ACTION
    │   └── No  → FORCED_PASS (Move(0) required)
    │
    ▼
ACTION_RECEIVED
    │
    ├── Action legal?
    │   ├── Yes → APPLY_MOVE
    │   │          │
    │   │          ├── Move resulted in 6?
    │   │          │   ├── First 6 in sequence → EXTRA_TURN
    │   │          │   └── Second+ consecutive 6 → END_TURN
    │   │          │
    │   │          └── Check win condition
    │   │               ├── Win → GAME_OVER
    │   │               └── No win → END_TURN or EXTRA_TURN
    │   │
    │   └── No  → ILLEGAL_ACTION (record error, re-prompt or force Move(0))
    │
    ▼
END_TURN
    │
    └── Switch to opponent
```

## 5. Dice Generation

- The dice is a standard 6-sided die (values 1–6).
- **[EXPLICIT]** Value 6 grants a replay, but only once per turn sequence.
- **[DESIGN]** Dice generation is random but should be seedable for deterministic simulation.
- The dice value is generated by the engine, not the bot.

## 6. Error Handling

- **Illegal action during WAIT_FOR_YOU:** The engine rejects the action and may:
  - Re-prompt the bot (competition behavior)
  - Force a `Move(0)` (simulator shortcut)
  - Record the error as a negative score event
- **Illegal action during WAIT_FOR_MOVE:** Not applicable (only the engine's turn logic triggers opponent).
- **[EXPLICIT]** Errors are recorded with negative score implications.

## 7. Observability

- Each bot only sees its own player-relative view.
- The bot does not know which global cell corresponds to which relative cell.
- The bot sees: its tokens, opponent tokens (in player-relative coordinates), dice value, and game state.
