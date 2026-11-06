import argparse
import sys

from tw_general.controllers.game_dir import resolve_game_dir
from tw_general.repositories.orders_file import OrdersFileRepository
from tw_general.services.order_service import OrderService


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Write one order for the Lodi battle script.")
    parser.add_argument("--unit", type=int, required=True)
    parser.add_argument("--x", type=float)
    parser.add_argument("--z", type=float)
    parser.add_argument("--walk", action="store_true", help="Walk. The default is to run.")
    parser.add_argument(
        "--release",
        action="store_true",
        help="Hand the unit back to the game's AI. Only --unit is needed.",
    )
    parser.add_argument(
        "--game-dir",
        default=None,
        help="Napoleon install folder. Defaults to TWLLM_GAME_DIR, else the Steam path.",
    )
    return parser


def main(argv: list[str] | None = None) -> None:
    parser = _parser()
    args = parser.parse_args(argv)
    game_dir = resolve_game_dir(args.game_dir)
    if not game_dir.is_dir():
        print(f"Game directory does not exist: {game_dir}", file=sys.stderr)
        raise SystemExit(2)

    service = OrderService(OrdersFileRepository(game_dir / "twllm_orders.txt"))
    if args.release:
        order = service.send_release(args.unit)
        print(f"Sent order {order.seq}: released unit {order.unit}. Lua picks it up within 3 s.")
        return

    if args.x is None or args.z is None:
        parser.error("--x and --z are required unless --release is set")

    order = service.send_move(
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
