# Competition REST Protocol

Source: Competition PDF (`document-v2.pdf`). All details are [EXPLICIT] unless noted.

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

**Note:** The PDF spells the board endpoint as `Borad` (not `Board`). The implementation must use the exact spelling from the PDF.

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

**Note:** The PDF shows `address` as a string `"0"` for the no-move case, but as an integer `14` for normal moves. The implementation should handle both.

**Source:** [EXPLICIT] "باید تابع Move با نشانی "0" فراخوانی گردد"

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

**Source:** [EXPLICIT] "هرگونه ارسال فرمان اشتباه، مانند حرکت در زمانی که نوبت ربات شما نیست یا حرکت به خانه‌ای که پیشتر اشغال شده و ... ثبت شده و به عنوان نمره منفی در نظر گرفته میشود"

## 8. Adapter Layer Design

The competition adapter wraps the core engine to communicate with the real server:

```python
class CompetitionAdapter:
    def __init__(self, base_url: str):
        self.base_url = base_url
        self.token = None

    def login(self, game_id: str, username: str, password: str,
              callback_url: str = None) -> str:
        """Register with the game server. Returns auth token."""
        pass

    def get_board(self) -> BoardState:
        """Fetch current game state from server."""
        pass

    def make_move(self, address: int):
        """Submit a move to the server."""
        pass

    def run(self, bot: Bot):
        """
        Main game loop:
        1. Login
        2. Poll Board endpoint
        3. When state is WAIT_FOR_YOU:
           - Parse board response
           - Convert to engine state
           - Generate legal actions
           - Ask bot for action
           - Convert action to address
           - Call Move endpoint
        4. Repeat until game over
        """
        pass
```

### State Mapping

The adapter maps between competition states and engine states:

| Competition State | Engine State |
|------------------|--------------|
| `NONE` | `PRE_GAME` |
| `WAIT_FOR_START` | `WAITING_TO_START` |
| `WAIT_FOR_YOU` | `YOUR_TURN` |
| `WAIT_FOR_MOVE` | `OPPONENTS_TURN` |
| `END_YOU_WIN` | `GAME_OVER_WIN` |
| `END_YOU_LOST` | `GAME_OVER_LOSS` |
| `END_EQUALS` | `GAME_OVER_DRAW` |

### Coordinate Conversion

The adapter handles conversion between:
- Server's player-relative coordinates (what the API returns)
- Engine's internal coordinate system
- Bot's observation coordinates

This is a thin mapping layer. The core engine's coordinate system is the source of truth.

## 9. Callback Handler

For bots using the callback URL approach:

```python
class CallbackHandler:
    """Handles incoming state change notifications from the server."""

    def handle(self, state: str):
        """
        Called when the server POSTs to the callback URL.
        State is the value that replaced {0} in the callback URL.
        """
        if state == "WAIT_FOR_YOU":
            # Fetch board and make a move
            board = adapter.get_board()
            action = bot.choose_action(board)
            adapter.make_move(action.address)
        elif state in ("END_YOU_WIN", "END_YOU_LOST", "END_EQUALS"):
            # Game over
            pass
```
