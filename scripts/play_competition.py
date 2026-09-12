"""Play a Ludo game against the competition server.

Usage:
    PYTHONPATH=src python3 scripts/play_competition.py --game-id game-room-1 \\
        --username MyTeam --password secret
    PYTHONPATH=src python3 scripts/play_competition.py --base-url http://localhost:8000 \\
        --game-id game-room-1 --username MyTeam --password secret --bot random
"""

import argparse
import logging

from ludo.bots import (
    make_greedy_bot,
    make_mcts_bot,
    make_mcts_evasive_bot,
    make_random_bot,
)
from ludo.model import GameConfig
from competition.runner import run_competition

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
    parser.add_argument(
        "--bot", choices=[*BOTS, "mcts", "evasive_mcts"], default="greedy"
    )
    parser.add_argument("--iterations", type=int, default=200)
    parser.add_argument("--seed", type=int, default=None)
    parser.add_argument("--players", type=int, default=2)
    parser.add_argument("--poll-interval", type=float, default=1.0)
    parser.add_argument(
        "--callback-url",
        default=None,
        help="Callback URL sent in the login request; {0} is replaced by the game state",
    )
    args = parser.parse_args()

    logging.basicConfig(level=logging.INFO)

    if args.bot == "mcts":
        bot = make_mcts_bot(iterations=args.iterations, seed=args.seed)
    elif args.bot == "evasive_mcts":
        bot = make_mcts_evasive_bot(iterations=args.iterations, seed=args.seed)
    else:
        bot = BOTS[args.bot]()

    result = run_competition(
        bot=bot,
        base_url=args.base_url,
        game_id=args.game_id,
        username=args.username,
        password=args.password,
        config=GameConfig(num_players=args.players),
        poll_interval=args.poll_interval,
        callback_url=args.callback_url,
    )
    print(
        f"game over: winner=p{result.winner} turns={result.turn_count} "
        f"errors={result.error_count}"
    )


if __name__ == "__main__":
    main()