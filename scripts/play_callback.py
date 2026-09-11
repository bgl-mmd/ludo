"""Play a Ludo game against the competition server using the callback mode.

The game server POSTs the game state to the callback URL on every change;
this script runs a small HTTP server that receives those callbacks and makes
a move whenever it is the bot's turn.

Usage:
    PYTHONPATH=src python3 scripts/play_callback.py --game-id game-room-1 \\
        --username MyTeam --password secret \\
        --callback-url "http://45.82.138.21:8000/?gamestate={0}"
"""

import argparse
import logging
from urllib.parse import urlparse

from ludo.bots import make_greedy_bot, make_random_bot
from ludo.model import GameConfig
from competition.callback_server import run_callback_server
from competition.client import login

BOTS = {
    "random": lambda: make_random_bot(seed=42),
    "greedy": make_greedy_bot,
}


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--base-url", default="https://rbc.sysx.ir")
    parser.add_argument("--game-id", required=True)
    parser.add_argument("--username", required=True)
    parser.add_argument("--password", required=True)
    parser.add_argument("--bot", choices=BOTS, default="greedy")
    parser.add_argument(
        "--callback-url",
        required=True,
        help="Callback URL sent in the login request; {0} is replaced by the game state",
    )
    parser.add_argument("--host", default="0.0.0.0", help="Local bind address for the callback server")
    parser.add_argument("--players", type=int, default=2)
    args = parser.parse_args()

    logging.basicConfig(level=logging.INFO)

    parsed = urlparse(args.callback_url)
    port = parsed.port or 8000
    if "{0}" not in args.callback_url:
        parser.error("--callback-url must contain the {0} placeholder (replaced by the game state)")

    config = GameConfig(num_players=args.players)
    token = login(args.base_url, args.game_id, args.username, args.password, args.callback_url)
    result = run_callback_server(
        host=args.host,
        port=port,
        bot=BOTS[args.bot](),
        base_url=args.base_url,
        token=token,
        username=args.username,
    )
    print(
        f"game over: winner=p{result.winner} turns={result.turn_count} "
        f"errors={result.error_count}"
    )


if __name__ == "__main__":
    main()