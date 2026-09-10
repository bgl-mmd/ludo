# Board and Coordinate Model

## 1. Two Coordinate Systems

The system uses two coordinate representations:

| System | Purpose | Range |
|--------|---------|-------|
| **Global** | Internal engine representation | Unique absolute cell IDs |
| **Player-relative** | Competition API / bot observation | 0–44 per player |

## 2. Global Board Layout

The board is a cross-shaped track. Based on the board diagram in the PDF:

```
            HOME (Yellow)
            [Y0][Y0]
            [Y0][Y0]

     ╔═══════════════════════════════════╗
     ║  ID:9    ID:10   ID:11          ║
     ║           ↓                      ║
     ║  ID:8   [RED]   ID:12          ║
     ║           ↓                      ║
     ║  ID:7   [RED]   ID:13          ║
     ║           ↓                      ║
     ║  ID:6   [RED]   ID:14          ║
     ║           ↓                      ║
     ║  ID:1→ID:2→ID:3→ID:4→ID:5 [RED] ║
     ║  ID:40 [Y41][Y42][Y43][Y44] ID:15→...→ID:19 ║
     ║  ID:39 ID:38 ID:37 ID:36 ID:35 [GRN] ID:25→ID:24→ID:23→ID:22 ID:21 ║
     ║           ↑                      ║
     ║  ID:34  [GRN]  ID:26           ║
     ║           ↑                      ║
     ║  ID:33  [GRN]  ID:27           ║
     ║           ↑                      ║
     ║  ID:32  [GRN]  ID:28           ║
     ║                                   ║
     ║  [G0][G0]   ID:31→ID:30→ID:29  [B0][B0] ║
     ║  [G0][G0]                        [B0][B0] ║
     ╚═══════════════════════════════════╝
```

### Simplified global cell map (from diagram):

The 40 shared track cells form a loop. The44 total labeled cells are:

- **ID:0** — Home yard (4 tokens per player start here)
- **ID:1 through ID:40** — Shared track cells (circular)
- **ID:41 through ID:44** — Home stretch cells (colored by player)

### Direction of travel (from arrows):

The arrows on the board show the path proceeds:
- Left to right across the top arm (cells 1→5)
- Top to bottom down the right arm (cells 9→5, then 15→19)
- Right to left across the bottom arm (cells 19→21, then 25→35)
- Bottom to top up the left arm (cells 35→31, then 29→1)

**Source:** [EXPLICIT] Board diagram with numbered cells and directional arrows.

## 3. Player-Relative Coordinates (Competition View)

Each player sees the board from their own perspective:

| Player | Begin (relative) | End (relative) | Begin (global) | End (global) |
|--------|-----------------|----------------|----------------|--------------|
| Player A | 1 | 40 | 1 | 40 |
| Player B | 21 | 20 | 21 | 20 |

**Source:** [EXPLICIT] Board response example shows:
```json
{
  "name": "RayanBotTeam1",
  "begin": 1,
  "end": 40,
  "tokens": [14, 0, 41, 43]
}
```
and
```json
{
  "name": "RayanBotTeam2",
  "begin": 21,
  "end": 20,
  "tokens": [0, 42, 20, 0]
}
```

## 4. Coordinate Conversion

### Global to Player-Relative

```
player_relative = ((global - begin + 40) mod 40) + 1
```

Where `begin` is the player's starting global cell.

**Special cases:**
- Position 0 (home yard) stays 0
- Positions 41–44 (home stretch) remain as-is (they are player-specific)

### Player-Relative to Global

```
global = ((player_relative - 1 + begin - 1) mod 40) + 1
```

**Special cases:**
- 0 stays 0
- 41–44 remain as-is

### Examples

For Player A (begin=1):
| Global | Player-Relative |
|--------|----------------|
| 1 | 1 |
| 20 | 20 |
| 40 | 40 |
| 0 | 0 |
| 41 | 41 |

For Player B (begin=21):
| Global | Player-Relative |
|--------|----------------|
| 21 | 1 |
| 40 | 20 |
| 1 | 21 |
| 20 | 40 |
| 0 | 0 |
| 42 | 42 |

## 5. Home Stretch Representation

Each player has4 home stretch cells (41–44 in player-relative coordinates). In global coordinates, these are mapped to specific cells.

**Open question:** How are global cell IDs 41–44 mapped to players? The diagram shows:
- Yellow home stretch: global cells near the yellow player's end
- Red home stretch: global cells near the red player's end
- Green home stretch: global cells near the green player's end
- Blue home stretch: global cells near the blue player's end

**[DESIGN]** The simulator must define the global ↔ player home stretch mapping.

## 6. Token Position Semantics

| Value | Meaning |
|-------|---------|
| `0` | Token is in home yard (not on board) |
| `1..40` | Token is on the shared track at player-relative position |
| `41..44` | Token is in player's home stretch |
| `> 44` | Token has finished (reached final destination) |

**Source:** [EXPLICIT] Board response example shows token values of 0, 14, 20, 41, 42, 43.

## 7. Collision Rules (Coordinate Level)

Two tokens cannot occupy the same cell, with these rules:

1. **Opponent on cell:** Moving onto a cell occupied by an opponent sends the opponent's token back to 0.
2. **Same player on cell:** A token cannot move to a cell occupied by another token of the same player.

**Source:** [EXPLICIT] "در هر خانه فقط و فقط یک مهره قرار خواهد گرفت"

## 8. Invariants

1. At most one token occupies any cell at any time (across all players).
2. A token at position 0 is always in its owner's home yard.
3. Tokens at positions 41–44 belong to a specific player (determined by the player's begin offset).
4. Token positions never decrease (movement is always forward).
