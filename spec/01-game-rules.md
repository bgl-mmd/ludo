# Game Rules

Each rule is classified as:
- **[EXPLICIT]** — directly stated in the competition specification
- **[IMPLIED]** — logically follows from explicit rules
- **[DESIGN]** — decision required by our simulator
- **[UNKNOWN]** — unspecified, requires clarification

---

## 1. Players and Tokens

| Property | Value | Source |
|----------|-------|--------|
| Number of players | 2 | [EXPLICIT] Competition is head-to-head |
| Tokens per player | 4 | [EXPLICIT] Board diagram shows 4 tokens per player at ID:0 |

## 2. Board Layout

The board is a cross-shaped track with numbered cells.

- Cells are numbered `ID:1` through `ID:44` on the board diagram.
- `ID:0` represents the home yard (starting area) where tokens begin.
- The main shared track consists of cells 1–40.
- Cells 41–44 are the final "home" cells (one per player, leading to the center).

## 3. Player-Relative Coordinates

The server presents the board **from each bot's perspective**:

- Each bot's starting cell is labeled `1`.
- Each bot's ending cell is labeled `40`.
- The server translates global positions to each player's relative view.

## 4. Token States

Each token is in one of these states:

| State | Representation | Description |
|-------|---------------|-------------|
| Home yard | `0` | Token is in the starting yard, not yet on the board |
| On track | `1..40` | Token is on the shared track at the player-relative position |
| Home stretch | `41..44` | Token is in the final cells approaching the center |
| Finished | Beyond `44` | Token has reached the final destination |

## 5. Movement Rules

### 5.1 Dice

- The dice produces values 1–6.
- A dice value of 6 grants a replay reward only once. A consecutive second 6 does not grant a replay.
- Second consecutive 6 has no reward.

### 5.2 Entering the Board

- [IMPLIED] A token can only leave the home yard (position 0) when the dice shows 6.
- [DESIGN] Need to confirm: does a 6 always allow entering, or can it be declined?

### 5.3 Movement on Track

- Tokens move forward by the dice value.
- If any token can move with the current dice value, the move must be made.
- There is no possibility to ignore/skip a move.

### 5.4 Capturing

- Going to a cell occupied by an opponent removes the opponent's token and returns it to id:0.
- If the cell is occupied by the same bot's token, other tokens of that bot cannot move to that destination.
- In each cell, exactly one token can be placed.

### 5.5 Home Stretch and Winning

- If the four final cells are filled by a bot, that bot is the winner.
- Each player's 4 final cells are their home stretch (cells 41–44 in player-relative coordinates).

### 5.6 No Valid Move

- If it is a bot's turn but no practical move is possible, the Move function must be called with address "0".

## 6. Invalid Actions and Penalties

- Bot error moves (hanging, going to wrong cell, etc.) are recorded as errors with negative score.
- Any wrong command (moving when not your turn, moving to an occupied cell, etc.) is recorded as negative score.

## 7. Game Termination

- **Win:** A player fills all 4 home stretch cells.
- **Loss:** The opponent fills all 4 home stretch cells.
- **Draw (`END_EQUALS`):** Game ends as a draw without a winner (not common in the 1405 game).
- **Server error:** If the game server has a critical error, state changes to `END_EQUALS` and the game stops.

## 8. Summary of Rules by Source

### Explicitly stated:
- 2 players, 4 tokens each
- Board cells numbered 1–40 (player-relative), plus 0 (home) and 41–44 (home stretch)
- Only one token per cell
- Capturing: opponent token returns to 0; own tokens block each other
- Move mandatory when any token can move; no skipping
- Dice 6 grants extra turn, but only once (consecutive second 6 = no extra turn)
- Move(0) when no move possible
- Errors result in negative score
- Win: fill 4 home cells

### Implied:
- Tokens leave home yard on a dice value of 6
- Movement is forward only (no backward movement)

### Design decisions required:
- Exact mechanics of "entering the board" on a 6
- Whether a player can decline to enter a new token when rolling 6
- Turn order: fixed or random first player
- How many consecutive 6s before losing turn (the spec says "only one replay" — does a 3rd consecutive 6 also lose the turn, or just the 2nd?)
- Whether tokens on the home stretch can be captured
- Whether tokens on the home stretch block same-player tokens

### Unknown / requires clarification:
- Safe squares (if any)
- Maximum number of consecutive turns after rolling 6
- Exact path through home stretch cells
- Whether the home stretch cells are shared or private per player
- Starting player determination
