import argparse
import sys
from pathlib import Path

from tw_general.controllers.game_dir import resolve_game_dir, resolve_scripts_dir
from tw_general.repositories.user_script import UserScriptRepository
from tw_general.services.startup_service import (
    edit_startup_lines,
    is_startup_line,
    startup_line,
)


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Boot Napoleon into one of our battles, or back to the normal menu."
    )
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument(
        "--battle",
        help="Battle name, for example test1. The XML must already exist.",
    )
    mode.add_argument(
        "--off",
        action="store_true",
        help="Remove the startup line so the game opens its normal menu.",
    )
    parser.add_argument(
        "--scripts-dir",
        default=None,
        help=(
            "Folder containing user.script.txt. "
            "Defaults to TWLLM_SCRIPTS_DIR, else the Napoleon scripts folder under APPDATA."
        ),
    )
    parser.add_argument(
        "--game-dir",
        default=None,
        help="Napoleon install folder. Defaults to TWLLM_GAME_DIR, else the Steam path.",
    )
    return parser


def _read_or_exit(repository: UserScriptRepository) -> list[str] | None:
    try:
        return repository.read_lines()
    except UnicodeError:
        print(f"{repository.path} is not UTF-16 with a BOM.", file=sys.stderr)
        raise SystemExit(1) from None


def _remove_startup(repository: UserScriptRepository) -> None:
    current = _read_or_exit(repository)
    if current is None:
        print(f"No user.script.txt at {repository.path}")
        return
    removed = [line for line in current if is_startup_line(line)]
    if not removed:
        print(f"No game_startup_mode line in {repository.path}")
        return
    repository.write_lines(edit_startup_lines(current, None))
    for line in removed:
        print(f"Removed line: {line}")
    print(repository.path)


def _set_startup(repository: UserScriptRepository, battle: str, game_dir: Path) -> None:
    try:
        new_line = startup_line(battle)
    except ValueError as exc:
        print(exc, file=sys.stderr)
        raise SystemExit(2) from exc

    xml_path = game_dir / "data" / "twllm_battles" / battle / f"{battle}.xml"
    if not xml_path.is_file():
        print(
            f"Battle XML does not exist: {xml_path}. Run make_battle first.",
            file=sys.stderr,
        )
        raise SystemExit(2)

    current = _read_or_exit(repository)
    lines = [] if current is None else current
    repository.write_lines(edit_startup_lines(lines, battle))
    for line in lines:
        if is_startup_line(line) and line != new_line:
            print(f"Removed line: {line}")
    print(f"Added line: {new_line}")
    print(repository.path)


def main(argv: list[str] | None = None) -> None:
    parser = _parser()
    args = parser.parse_args(argv)
    repository = UserScriptRepository(resolve_scripts_dir(args.scripts_dir))
    if args.off or args.battle is None:
        _remove_startup(repository)
        return
    _set_startup(repository, args.battle, resolve_game_dir(args.game_dir))


if __name__ == "__main__":
    main()
