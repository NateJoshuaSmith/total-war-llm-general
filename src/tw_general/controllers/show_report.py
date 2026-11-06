import argparse
import sys

from tw_general.controllers.game_dir import resolve_game_dir
from tw_general.repositories.state_file import StateFileRepository
from tw_general.services.report import build_report
from tw_general.services.state_parser import parse_state


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Print the battlefield report from the live state file."
    )
    parser.add_argument(
        "--game-dir",
        default=None,
        help="Napoleon install folder. Defaults to TWLLM_GAME_DIR, else the Steam path.",
    )
    parser.add_argument(
        "--our-alliance",
        type=int,
        default=2,
        help="Alliance we command. Defaults to 2, the same as Lodi and generated battles.",
    )
    return parser


def main(argv: list[str] | None = None) -> None:
    parser = _parser()
    args = parser.parse_args(argv)
    game_dir = resolve_game_dir(args.game_dir)
    if not game_dir.is_dir():
        print(f"Game directory does not exist: {game_dir}", file=sys.stderr)
        raise SystemExit(2)

    path = game_dir / "twllm_state.txt"
    text = StateFileRepository(path).read()
    if text is None:
        print(f"State file is missing or half-written: {path}", file=sys.stderr)
        raise SystemExit(1)
    try:
        state = parse_state(text)
    except ValueError as err:
        print(f"State file is not usable: {path} ({err})", file=sys.stderr)
        raise SystemExit(1) from err
    print(build_report(state, our_alliance=args.our_alliance), end="")


if __name__ == "__main__":
    main()
