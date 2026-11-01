import argparse
import os
import sys
from pathlib import Path

from tw_general.repositories.orders_file import OrdersFileRepository
from tw_general.services.order_service import OrderService

_DEFAULT_GAME_DIR = Path(r"D:\SteamLibrary\steamapps\common\Napoleon Total War")


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Write one move order for the Lodi battle script.")
    parser.add_argument("--unit", type=int, required=True)
    parser.add_argument("--x", type=float, required=True)
    parser.add_argument("--z", type=float, required=True)
    parser.add_argument("--walk", action="store_true", help="Walk. The default is to run.")
    parser.add_argument(
        "--game-dir",
        default=None,
        help="Napoleon install folder. Defaults to TWLLM_GAME_DIR, else the Steam path.",
    )
    return parser


def _game_dir(argument: str | None) -> Path:
    if argument:
        return Path(argument)
    from_env = os.environ.get("TWLLM_GAME_DIR")
    if from_env:
        return Path(from_env)
    return _DEFAULT_GAME_DIR


def main(argv: list[str] | None = None) -> None:
    args = _parser().parse_args(argv)
    game_dir = _game_dir(args.game_dir)
    if not game_dir.is_dir():
        print(f"Game directory does not exist: {game_dir}", file=sys.stderr)
        raise SystemExit(2)

    order = OrderService(OrdersFileRepository(game_dir / "twllm_orders.txt")).send_move(
        args.unit,
        args.x,
        args.z,
        run=not args.walk,
    )
    pace = "running" if order.run else "walking"
    print(
        f"Sent order {order.seq}: unit {order.unit} -> ({order.x}, {order.z}), {pace}. "
        "Lua picks it up within 3 s."
    )


if __name__ == "__main__":
    main()
