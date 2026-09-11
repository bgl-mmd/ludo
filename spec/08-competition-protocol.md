# Competition REST Protocol

## 1. Server

- **Base URL:** `https://rbc.sysx.ir`
- **Protocol:** RESTful, all endpoints use HTTP POST
- **Content-Type:** `application/json`
- **Accept:** `application/json`

## 2. Endpoints

| Endpoint | URL | Purpose |
|----------|-----|---------|
| Login | `/api/v1/Login` | Register bot with the game |
| Board | `/api/v1/Borad` | Get current game state and board |
| Move | `/api/v1/Move` | Submit a move |

**Note:** The board endpoint is spelled `Borad` (not `Board`). The implementation must use the exact spelling.

## 3. Login

**URL:** `http://<Domain>/api/v1/Login`

### Request

```json
{
  "gameID": "game-room-1",
  "engine": "ludo",
  "userName": "RayanBotTeam",
  "password": "123",
  "callbackUrl": "http://myBot.local/gamestatecallback?gamestate={0}"
}
```

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `gameID` | string | Yes | Game room name (for managing simultaneous isolated games) |
| `engine` | string | Yes | Fixed value: `"ludo"` (or `"Mensch"`) |
| `userName` | string | Yes | Bot team name |
| `password` | string | Yes | Bot password |
| `callbackUrl` | string | No | Optional callback URL for automatic state change notifications |

### Callback URL Behavior

The `{0}` placeholder in the callback URL is replaced with the game state value.

Example: `http://myBot.local/gamestatecallback?gamestate=WAIT_FOR_YOU`

The callback is a POST request to the specified URL with the state value.

**[DESIGN]** The callback URL must be accessible from the game server (which is on the internet).

### Response

```json
{
  "token": "ead0612d-6fb6-4043-a01a-b58a08638aa8"
}
```

| Field | Type | Description |
|-------|------|-------------|
| `token` | string | Authentication token for subsequent requests |

### HTTP Status Codes

| Code | Description |
|------|-------------|
| 200 | Success, JSON response |
| 204 | Success, no data to return |
| Other | Error, request is invalid or unauthorized |

## 4. Board (Get Game State)

**URL:** `http://<Domain>/api/v1/Borad`

### Request

```json
{
  "token": "ead0612d-6fb6-4043-a01a-b58a08638aa8"
}
```

| Field | Type | Description |
|-------|------|-------------|
| `token` | string | Authentication token from Login |

### Response

```json
{
  "gameID": "game-room-1",
  "state": "WAIT_FOR_YOU",
  "timestamp": "12345ABCD",
  "dice": 6,
  "users": [
    {
      "name": "RayanBotTeam1",
      "begin": 1,
      "end": 40,
      "tokens": [14, 0, 41, 43]
    },
    {
      "name": "RayanBotTeam2",
      "begin": 21,
      "end": 20,
      "tokens": [0, 42, 20, 0]
    }
  ]
}
```

| Field | Type | Description |
|-------|------|-------------|
| `gameID` | string | Game room name |
| `state` | string | Game state (see state table) |
| `timestamp` | string | Changes when the board changes |
| `dice` | int | Dice value ready for movement (0–6) |
| `users` | array | List of players |
| `users[].name` | string | Player name |
| `users[].begin` | int | Player's starting cell coordinate |
| `users[].end` | int | Player's ending cell coordinate |
| `users[].tokens` | int[4] | Token positions in player-relative coordinates |

### Token Position Values

| Value | Meaning |
|-------|---------|
| `0` | Token is in home yard (not on board) |
| `1..40` | Token is on the shared track |
| `41..44` | Token is in home stretch |

### Player Coordinates

- Player 1: `begin=1`, `end=40` (starts at cell 1, ends at cell 40)
- Player 2: `begin=21`, `end=20` (starts at cell 21, ends at cell 20)

**Note:** The `begin` and `end` values represent the player's start and end positions in the global board coordinate system. The `tokens` array is in the player's own relative coordinate system.

## 5. Move

**URL:** `http://<Domain>/api/v1/Move`

### Request

```json
{
  "token": "ead0612d-6fb6-4043-a01a-b58a08638aa8",
  "address": 14
}
```

| Field | Type | Description |
|-------|------|-------------|
| `token` | string | Authentication token |
| `address` | int | Source cell address of the token to move (player-relative) |

### Move(0) — No Valid Move

When no token can legally move:

```json
{
  "token": "ead0612d-6fb6-4043-a01a-b58a08638aa8",
  "address": "0"
}
```

**Note:** The `address` field is shown as an integer (`14`) for normal moves but as a string (`"0"`) for no-move. The implementation should handle both.

### Response

```
EMPTY
```

The response body is empty. Success is indicated by HTTP status code 200.

## 6. Game States (Competition)

| State | Description |
|-------|-------------|
| `NONE` | Lobby incomplete, at least two bots not yet completed |
| `WAIT_FOR_START` | Game waiting for supervisor approval to start |
| `WAIT_FOR_YOU` | Waiting for YOUR move (your bot's turn) |
| `WAIT_FOR_MOVE` | Waiting for opponent's move |
| `END_YOU_WIN` | Game over, your bot won |
| `END_YOU_LOST` | Game over, opponent bot won |
| `END_EQUALS` | Game ended as draw (not common in 1405) |

**Note:** If the game server has a critical error, state changes to `END_EQUALS` and the game stops.

## 7. Error Handling

### HTTP Errors

| Code | Meaning |
|------|---------|
| 200 | Success with JSON |
| 204 | Success, no data |
| Other | Error, invalid or unauthorized request |

### Bot Errors (Competition Rules)

The following are recorded as errors with negative score:
- Moving when it's not your turn
- Moving to an occupied cell
- Moving to an invalid cell
- Hanging (no response)
- Any other invalid command

## 8. Runner Layer Design

The competition **runner** is a function that owns the game loop and communicates with the real server. The bot code is identical whether using this runner or the simulation runner. IO (HTTP) is kept in small client functions; parsing and decision logic are pure.

```python
# ---- Pure layer: board parsing (no IO) ----

def parse_board(json: dict) -> BoardState:
    """Parse the Board response JSON into a typed BoardState. Pure."""

def parse_observation(board: BoardState) -> Observation:
    """Build a bot Observation from a parsed board. Pure."""

def parse_result(board: BoardState) -> GameResult:
    """Translate a terminal board into a GameResult. Pure."""

# ---- IO layer: HTTP client (impure, kept at the edge) ----

def login(base_url: str, game_id: str, username: str, password: str,
          callback_url: str = None) -> str:
    """Register with the game server. Returns auth token. IO."""

def get_board(base_url: str, token: str) -> BoardState:
    """Fetch current game state from server. IO."""

def make_move(base_url: str, token: str, address: int | str):
    """Submit a move to the server. IO."""

# ---- Runner: composes IO + pure functions ----

def run_competition(bot: BotFn,
                    base_url: str,
                    game_id: str,
                    username: str,
                    password: str,
                    config: GameConfig) -> GameResult:
    """
    Complete game loop — mirrors run_simulation().

    1. Login
    2. Poll Board endpoint until game starts
    3. Game loop:
       a. When state is WAIT_FOR_YOU:
          - Parse board response (server already rolled dice)
          - Build Observation from board state
          - Ask bot for action
          - Send move to server
       b. Poll for next state
    4. Game over — return result
    """
```

### What the competition runner delegates to the server

| Responsibility | Who does it |
|---------------|-------------|
| Dice rolls | Server |
| Turn tracking | Server |
| Rules enforcement | Server |
| Win detection | Server |
| Captures | Server |

### What the competition runner does locally

| Responsibility | Who does it |
|---------------|-------------|
| Parse board response | `parse_board` (pure) |
| Build Observation | `parse_observation` (pure) |
| Generate legal actions | Runner (or server, if available) |
| Call `bot(obs)` | Runner |
| Send move to server | `make_move` (IO) |

### State Mapping

The runner maps between competition states and the bot's view:

| Competition State | Bot Sees |
|------------------|----------|
| `NONE` | Pre-game (wait) |
| `WAIT_FOR_START` | Pre-game (wait) |
| `WAIT_FOR_YOU` | `is_your_turn = True` |
| `WAIT_FOR_MOVE` | `is_your_turn = False` |
| `END_YOU_WIN` | `game_over = True, winner = you` |
| `END_YOU_LOST` | `game_over = True, winner = opponent` |
| `END_EQUALS` | `game_over = True, winner = None` |

## 9. Callback Handler

For bots using the callback URL approach, the handler is a function:

```python
def handle_callback(state: str, bot: BotFn, base_url: str, token: str) -> None:
    """
    Called when the server POSTs to the callback URL.
    State is the value that replaced {0} in the callback URL.
    """
    if state == "WAIT_FOR_YOU":
        # Fetch board and make a move
        board = get_board(base_url, token)
        obs = parse_observation(board)
        action = bot(obs) if obs.legal_actions else None
        address = obs.own_tokens[action] if action is not None else "0"
        make_move(base_url, token, address)
    elif state in ("END_YOU_WIN", "END_YOU_LOST", "END_EQUALS"):
        # Game over
        pass
```
