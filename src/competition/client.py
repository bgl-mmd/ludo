import json
import logging
import time
import urllib.error
import urllib.request

from competition.parsing import BoardState, parse_board

TIMEOUT = None
BOARD_ENDPOINT = "/api/v1/Board"
MODEL = "ludo"

logger = logging.getLogger(__name__)


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
    start = time.monotonic()
    logger.info("request: POST %s", endpoint)
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
    elapsed_ms = (time.monotonic() - start) * 1000
    logger.info("response: %s status=%s elapsed=%.0fms", endpoint, status, elapsed_ms)
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
    response = _post(base_url, BOARD_ENDPOINT, {"token": token, "model": MODEL})
    if response is None:
        raise CompetitionError("Board returned an empty response")
    return parse_board(response)


def make_move(base_url: str, token: str, address: int | str) -> None:
    _post(base_url, "/api/v1/Move", {"token": token, "address": address})
