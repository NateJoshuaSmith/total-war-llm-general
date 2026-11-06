import json
from pathlib import Path

from pydantic import TypeAdapter

from tw_general.models.battle import Battle
from tw_general.models.unit_type import UnitType

_CATALOGUE = TypeAdapter(dict[str, UnitType])


class BattleRepository:
    def read(self, path: Path) -> Battle:
        return Battle.model_validate_json(Path(path).read_text(encoding="utf-8"))


class UnitCatalogueRepository:
    def __init__(self, path: Path) -> None:
        self._path = Path(path)

    def read(self) -> dict[str, UnitType]:
        raw = json.loads(self._path.read_text(encoding="utf-8"))
        return _CATALOGUE.validate_python(raw)


class BattleOutputRepository:
    def write(
        self,
        folder: Path,
        name: str,
        xml_text: str,
        script_source: Path,
    ) -> tuple[Path, Path]:
        folder = Path(folder)
        folder.mkdir(parents=True, exist_ok=True)
        xml_path = folder / f"{name}.xml"
        script_path = folder / f"{name}.battle_script"
        xml_path.write_text(xml_text, encoding="utf-8", newline="\n")
        script_path.write_bytes(Path(script_source).read_bytes())
        return xml_path, script_path
