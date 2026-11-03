import argparse
import sys
from pathlib import Path

from pydantic import ValidationError

from tw_general.controllers.game_dir import resolve_game_dir
from tw_general.repositories.battle_files import (
    BattleOutputRepository,
    BattleRepository,
    UnitCatalogueRepository,
)
from tw_general.services.battle_service import BattleService, UnknownUnitTypeError

# This file is src/tw_general/controllers/make_battle.py, four levels under the repo root.
_REPO_ROOT = Path(__file__).resolve().parents[3]
_BATTLES_DIR = _REPO_ROOT / "eval" / "battles"
_CATALOGUE_PATH = Path(__file__).resolve().parents[1] / "data" / "napoleon_units.json"
_SCRIPT_SOURCE = _REPO_ROOT / "game" / "napoleon" / "lodi_battle.battle_script"


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Write a battle XML and script into the Napoleon data folder."
    )
    parser.add_argument("--battle", required=True, help="Battle name, for example test1.")
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

    battle_path = _BATTLES_DIR / f"{args.battle}.json"
    if not battle_path.is_file():
        print(f"Battle file does not exist: {battle_path}", file=sys.stderr)
        raise SystemExit(2)

    try:
        battle = BattleRepository().read(battle_path)
        service = BattleService(
            UnitCatalogueRepository(_CATALOGUE_PATH),
            BattleOutputRepository(),
        )
        xml_path, script_path = service.write(
            battle,
            _SCRIPT_SOURCE,
            game_dir / "data" / "twllm_battles" / battle.name,
        )
    except (ValidationError, UnknownUnitTypeError) as exc:
        print(exc, file=sys.stderr)
        raise SystemExit(1) from exc

    print(xml_path)
    print(script_path)


if __name__ == "__main__":
    main()
