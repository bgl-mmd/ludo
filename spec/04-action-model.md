# Action Model

## 1. Competition Action Format

The competition uses a `Move` command with an `address` field:

```json
{
  "token": "auth-token",
  "address": 14
}
```

The `address` is the **source cell** (the cell where the token currently is), not the destination.

## 2. Move(0) — No Valid Move

When no token can legally move with the current dice value:

```json
{
  "token": "auth-token",
  "address": 0
}
```

## 3. Internal Action Model

In the functional engine, an action is a plain **token index**:

```python
# An action is simply an int: which token (0-3) to move.
# None means "no valid move" (the runner sends address "0" to the server).
Action = int | None
```

### Why this representation?

- The action is a plain value — the smallest possible data. No class, no wrapper.
- The competition `address` (the token's current source position) is **derived** by the runner from the observation when building the `Move` request: `address = obs.own_tokens[action]`.
- `None` cleanly represents the "no valid move" case without colliding with token index 0.

## 4. Action → Competition Address Mapping

The competition `address` field corresponds to the token's `source_position` in player-relative coordinates.

| Internal Action | Competition Address |
|----------------|-------------------|
| Move token index `i` | `address = own_tokens[i]` (the token's current position) |
| No valid move (`None`) | `address = "0"` |

## 5. Legal Action Generation

The engine generates legal actions (token indices) for the current player and dice value:

```python
def generate_legal_actions(state, player, dice_value) -> tuple[int, ...]:
    actions = []
    for token_idx, pos in enumerate(state.tokens[player]):
        if pos == 0:
            # Token in home yard: can only enter if dice = 6
            if dice_value == 6:
                actions.append(token_idx)
        elif pos >= 41:
            # Token in home stretch
            new_pos = pos + dice_value
            if new_pos <= 44:
                # Check if destination is occupied by same player
                if not occupied_by_same_player(state, player, new_pos):
                    actions.append(token_idx)
        elif pos >= 1 and pos <= 40:
            # Token on main track
            new_pos = pos + dice_value
            if new_pos <= 40:
                # Check destination
                dest_occupant = get_occupant(state, player, new_pos)
                if dest_occupant != SAME_PLAYER:
                    actions.append(token_idx)
            elif new_pos <= 44:
                # Transitioning to home stretch
                home_pos = new_pos  # 41-44
                if not occupied_by_same_player(state, player, home_pos):
                    actions.append(token_idx)
            else:
                # Would overshoot home stretch — illegal
                pass
    return tuple(actions)
```

## 6. Action Validation

Before executing an action, the engine validates:

1. **Turn check:** Is it this player's turn?
2. **Token existence:** Does the token exist at the specified source position?
3. **Legal move:** Does the dice value allow this move?
4. **Destination check:** Is the destination valid (not occupied by same player, within bounds)?

If validation fails → illegal action → error recorded.

## 7. Action Execution

```
execute_action(state, action, dice_value):
    1. Validate action
    2. Compute destination position
    3. If destination occupied by opponent:
         - Remove opponent token (set to 0)
    4. Move token from source to destination
    5. Check win condition
    6. Update state
    7. Return new state + metadata (captured opponent, won, etc.)
```

## 8. Edge Cases

### 8.1 Entering the Board (Dice = 6)

When a token is at position 0 (home yard) and dice = 6:
- The token enters the board at the player's starting position (relative position 1).
- [IMPLIED] The destination (position 1) must not be occupied by the same player's token.

### 8.2 Home Stretch Transition

When a token is on the main track and the dice would move it past position 40:
- The token enters the home stretch at position `40 + (dice_value - distance_to_40)`.
- Example: Token at position 39, dice = 3 → new position = 42 (home stretch).
- If the dice overshoots the home stretch (beyond 44), the move is illegal.

### 8.3 Overshooting Home Stretch

If a token is in the home stretch and the dice would move it past position 44:
- The move is illegal.
- Another token must be moved, or `Move(0)` if no other legal moves exist.

**[DESIGN]** Overshooting is not explicitly addressed. This is a common Ludo rule.

### 8.4 Capturing on Position 1

Can a token be captured immediately upon entering the board (at position 1)?

**[DESIGN]** Safe squares are not specified. Position 1 is treated like any other cell.

## 9. Summary Table

| Scenario | Source Position | Dice | Destination | Action |
|----------|----------------|------|-------------|--------|
| Enter board | 0 | 6 | 1 | Move from 0 |
| Normal move | 1–40 | 1–6 | source + dice | Move from source |
| Capture | 1–40 | any | opponent on dest | Move + remove opponent |
| Home stretch | 1–40 | leads to 41–44 | dest in 41–44 | Move to home stretch |
| Home stretch move | 41–43 | 1–6 | source + dice ≤ 44 | Move within home stretch |
| Finish | 41–44 | exact to 44 | 44 | Token finished |
| Overshoot | 41–44 | source + dice > 44 | illegal | Cannot move this token |
| Blocked by self | any | dest occupied by self | illegal | Cannot move this token |
| No valid move | any | all tokens blocked | N/A | Move(0) |
