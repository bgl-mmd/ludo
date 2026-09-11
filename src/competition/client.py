import json
import urllib.error
import urllib.request

from competition.parsing import BoardState, parse_board

TIMEOUT = 10


class CompetitionError(Exception):
    pass


def _post(base_url: str, endpoint: str, payload: dict) -> dict | None:
    body = json.dumps(payload).encode("utf-8")
    request = urllib.request.Request(
        f"{base_url}{endpoint}",
        data=body,
        method="POST",
        headers={
            "Content-Type": "application/json",
            "Accept": "application/json",
            "Content-Length": str(len(body)),
        },
    )
    try:
        response = urllib.request.urlopen(request, timeout=TIMEOUT)
    except urllib.error.HTTPError as error:
        raise CompetitionError(
            f"HTTP {error.code} from {endpoint}: {error.reason}"
        ) from error
    except urllib.error.URLError as error:
        raise CompetitionError(f"Request to {endpoint} failed: {error.reason}") from error
    status = getattr(response, "status", 200)
    data = response.read()
    if status == 204 or not data:
        return None
    if status != 200:
        raise CompetitionError(f"HTTP {status} from {endpoint}")
    return json.loads(data.decode("utf-8"))


def login(
    base_url: str,
    game_id: str,
    username: str,
    password: str,
    callback_url: str | None = None,
) -> str:
    payload = {
        "gameID": game_id,
        "engine": "ludo",
        "userName": username,
        "password": password,
    }
    if callback_url is not None:
        payload["callbackUrl"] = callback_url
    response = _post(base_url, "/api/v1/Login", payload)
    if response is None:
        raise CompetitionError("Login returned an empty response")
    return response["token"]


def get_board(base_url: str, token: str) -> BoardState:
    response = _post(base_url, "/api/v1/Borad", {"token": token})
    if response is None:
        raise CompetitionError("Board returned an empty response")
    return parse_board(response)


def make_move(base_url: str, token: str, address: int | str) -> None:
    _post(base_url, "/api/v1/Move", {"token": token, "address": address})
