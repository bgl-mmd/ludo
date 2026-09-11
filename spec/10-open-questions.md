# Open Questions and Ambiguities

This document lists all rules or behaviors that are ambiguous, unspecified, or could not be definitively determined from the competition specification. Each item includes a recommended default for the simulator.

---

## OQ-1: Board Cell Layout

**Question:** What is the exact physical layout of cells on the board? The board diagram shows cells ID:1 through ID:44, but the exact path topology (which cells are adjacent, how the home stretch connects) is not fully described in text.

**Status:** Partially resolved from diagram. Exact adjacency list requires careful visual inspection.

**Recommended default:** Reconstruct the board from the diagram. Mark as [OPEN] until verified against the actual competition server behavior.

---

## OQ-2: Home Stretch Cell Ownership

**Question:** Are cells 41–44 shared among all players, or does each player have their own private set of home stretch cells?

**Status:** Ambiguous. The competition may use a shared global numbering for home stretch cells (e.g., yellow=41–44, red=45–48, etc.) or each player may see their home stretch as 41–44 regardless of global position.

**Recommended default:** Each player's home stretch is their own private cells 41–44. The engine maps these to global positions internally. This matches the player-relative coordinate philosophy.

---

## OQ-3: Entering the Board on a 6

**Question:** When a player rolls a 6 and has tokens in the home yard, must they enter a new token, or may they move an existing on-board token instead?

**Status:** Implied but not explicit. The rule says "if any token can move, you must move." This suggests entering a new token on a 6 is mandatory if no other token can move, but optional if other tokens can also move.

**Recommended default:** Entering a new token on a 6 is optional. The player can choose to enter or move an existing token. If no other move is possible, entering is mandatory.

---

## OQ-4: Maximum Consecutive 6s

**Question:** What happens on the third (or more) consecutive 6? The spec says "a dice with 6 only once includes the replay reward" and "consecutive dice 6 second will not have a reward."

**Status:** Two interpretations:
1. After 2 consecutive 6s, the turn ends (most common in Ludo variants)
2. After 1st 6 you get an extra turn; 2nd 6 you don't; 3rd 6 you do again (unlikely)

**Recommended default:** Maximum 1 extra turn per turn sequence. After 2 consecutive 6s, the turn ends. This is the standard Ludo behavior and matches the "only once" phrasing.

---

## OQ-5: Safe Squares

**Question:** Are there any safe squares where tokens cannot be captured?

**Status:** Not specified. Standard Ludo has safe squares (typically the starting positions of each color).

**Recommended default:** No safe squares. All cells on the shared track are vulnerable to capture. This is the simplest interpretation and matches the competition's simplified rules.

---

## OQ-6: Turn Order

**Question:** How is the first player determined? Is it random, fixed, or based on Login order?

**Status:** Not specified.

**Recommended default:** First player is determined randomly (coin flip or dice roll). For deterministic simulation, use the seed.

---

## OQ-7: Board Response Typo

**Question:** The Board endpoint is spelled `Borad`. Is this the actual spelling, or is it a typo?

**Status:** Ambiguous. Could be intentional (competition server uses this spelling) or a typo.

**Recommended default:** Use `Borad` (match the specification exactly). If the real server uses `Board`, the runner can be configured.

---

## OQ-8: Move Address Type

**Question:** The Move request shows `address` as an integer (14) for normal moves but as a string ("0") for no-move. Should the implementation accept both types?

**Status:** Ambiguous. The specification is inconsistent.

**Recommended default:** Accept both integer and string for the address field. Send as integer for normal moves, send as string "0" for no-move (match specification exactly).

---

## OQ-9: Callback URL Mechanics

**Question:** What is the exact format of the callback POST request? What body is sent? What headers?

**Status:** Partially specified. The state replaces `{0}` in the URL, but the POST body and headers are not described.

**Recommended default:** POST to the callback URL with an empty body or JSON body containing the state. The state is also in the URL query parameter.

---

## OQ-10: dice=0 in Board Response

**Question:** The Board response shows `"dice": 6` as an example. What does `dice: 0` mean? Is it a valid value before rolling?

**Status:** The spec says dice can be 0–6. A value of 0 likely means "no dice rolled yet" or "waiting for dice."

**Recommended default:** dice=0 means no dice has been rolled for the current turn. The bot should wait for a non-zero dice value.

---

## OQ-11: Error Recovery

**Question:** When a bot makes an invalid move, does the game:
1. Re-prompt the bot for a valid move?
2. Force Move(0) and continue?
3. End the game immediately?

**Status:** The competition records errors as negative score, but the exact recovery behavior is not specified.

**Recommended default:** For the simulator: re-prompt the bot once, then force Move(0). For competition mode: match the server's behavior (likely similar).

---

## OQ-12: Number of Players

**Question:** The competition example shows 2 players. Can there be 3 or 4 players?

**Status:** Likely 2 players only, but not explicitly limited.

**Recommended default:** Support 2 players. Allow configuration for more, but the rules are written for 2-player games.

---

## OQ-13: Home Stretch Path

**Question:** Is the path through cells 41–44 sequential (41→42→43→44), or is there a different path?

**Status:** Implied but not explicit.

**Recommended default:** Sequential path: 41→42→43→44→finished. A token at position 44 has reached the final destination.

---

## OQ-14: Token at Position 44

**Question:** What exactly happens when a token reaches position 44? Is it "finished" and removed from play, or does it stay at 44?

**Status:** Implied. Position 44 is the last cell; filling all four means having a token at each of 41, 42, 43, and 44 simultaneously.

**Recommended default:** Token at 44 is "finished" and stays there. Win condition is having all 4 tokens at positions 41–44 (one per cell).

---

## OQ-15: Token Distribution on Win

**Question:** For a player to win, must they have exactly one token at each of positions 41, 42, 43, and 44? Or can they have multiple tokens at the same home stretch position?

**Status:** Implied. Since only one token per cell is allowed, and there are exactly 4 home stretch cells, each cell must have exactly one token.

**Recommended default:** Win = one token at each of positions 41, 42, 43, and 44. No two tokens can share a home stretch cell.

---

## OQ-16: Capture on Home Stretch

**Question:** Can tokens on the home stretch (41–44) be captured by opponents?

**Status:** Unknown. Standard Ludo varies on this.

**Recommended default:** Tokens on the home stretch CANNOT be captured. The home stretch is private to each player. This is the safer assumption and matches standard Ludo.

---

## OQ-17: Move(0) Timing

**Question:** When the bot calls Move(0), does the turn immediately end, or does the engine still process something?

**Status:** Implied. Move(0) signals "I cannot move" and the turn passes.

**Recommended default:** Move(0) ends the turn immediately. No dice roll, no extra turn, even if the dice was 6.

---

## OQ-18: Dice Roll Timing

**Question:** When is the dice rolled? Before the bot is prompted, or after?

**Status:** Implied. The dice is rolled before the bot is prompted. The Board response includes a `dice` field, and the state `WAIT_FOR_YOU` implies the dice is ready when the bot is asked to move.

**Recommended default:** Roll dice first, then prompt bot with dice value and legal actions.
