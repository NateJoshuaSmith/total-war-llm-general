import math
import xml.etree.ElementTree as ET
from collections.abc import Mapping
from dataclasses import dataclass
from pathlib import Path

from tw_general.models.battle import Battle, BattleSide, BattleUnit, General
from tw_general.models.unit_type import UnitType
from tw_general.repositories.battle_files import BattleOutputRepository, UnitCatalogueRepository

_XSI = "http://www.w3.org/2001/XMLSchema-instance"


# Cameras, weather, and victory conditions are copied from the battle that
# worked in game. A later ticket can move them into the JSON.
@dataclass(frozen=True)
class _AllianceDefaults:
    time_period: str | None
    non_playable: bool
    camera_start: tuple[int, int, int]
    camera_target: tuple[int, int, int]
    aggression: str
    rout_x: str
    rout_y: str


_ALLIANCES = (
    _AllianceDefaults("late", False, (0, 150, 650), (0, 30, 380), "1", "0.0", "-2000.0"),
    _AllianceDefaults(None, True, (0, 150, -650), (0, 30, -380), "0", "2000.0", "2000.0"),
)


class UnknownUnitTypeError(ValueError):
    def __init__(self, unit_type: str) -> None:
        self.unit_type = unit_type
        super().__init__(f"Unknown unit type: {unit_type}")


def _number(value: float) -> str:
    as_int = round(value)
    if math.isclose(value, as_int, abs_tol=1e-6):
        return str(as_int)
    return f"{value:.6f}".rstrip("0").rstrip(".")


def _metres(value: float) -> str:
    return f"{value:.2f}"


def _add(
    parent: ET.Element,
    tag: str,
    text: str | None = None,
    attrs: dict[str, str] | None = None,
) -> ET.Element:
    element = ET.SubElement(parent, tag, attrs or {})
    if text is not None:
        element.text = text
    return element


def _lookup(catalogue: Mapping[str, UnitType], unit_type: str) -> UnitType:
    try:
        return catalogue[unit_type]
    except KeyError as exc:
        raise UnknownUnitTypeError(unit_type) from exc


def _add_general(parent: ET.Element, general: General) -> None:
    attrs: dict[str, str] = {}
    if general.category is not None:
        attrs["general_category"] = general.category
    element = _add(parent, "general", attrs=attrs)
    _add(element, "name", general.name)
    _add(element, "experience", str(general.experience))
    _add(element, "portrait", general.portrait)


def _add_unit(
    army: ET.Element,
    unit: BattleUnit,
    side: BattleSide,
    catalogue: Mapping[str, UnitType],
) -> None:
    spec = _lookup(catalogue, unit.type)
    element = _add(
        army,
        "unit",
        attrs={
            "unit_category": spec.unit_category,
            "num_soldiers": str(spec.num_soldiers),
        },
    )
    _add(element, "unit_type", attrs={"type": unit.type})
    _add(element, "position", attrs={"x": _number(unit.x), "y": _number(unit.z)})
    _add(element, "orientation", attrs={"radians": _number(side.facing)})
    width = spec.width if unit.width is None else unit.width
    _add(element, "width", attrs={"metres": _metres(width)})
    if unit.general is not None:
        _add_general(element, unit.general)
    capabilities = _add(element, "unit_capabilities")
    for capability in spec.capabilities:
        _add(capabilities, capability.tag, capability.text)
    _add(element, "unit_experience", attrs={"level": str(unit.experience)})


def _add_deployment(army: ET.Element, side: BattleSide) -> None:
    area = _add(army, "deployment_area")
    zone = side.zone
    _add(area, "centre", attrs={"x": _number(zone.x), "y": _number(zone.z)})
    _add(area, "width", attrs={"metres": _number(zone.width)})
    _add(area, "height", attrs={"metres": _number(zone.height)})
    _add(area, "orientation", attrs={"radians": _number(side.facing)})


def _add_camera(army: ET.Element, tag: str, coords: tuple[int, int, int]) -> None:
    x, y, z = coords
    _add(army, tag, attrs={"x": str(x), "y": str(y), "z": str(z)})


def _add_alliance(
    root: ET.Element,
    index: int,
    side: BattleSide,
    catalogue: Mapping[str, UnitType],
) -> None:
    defaults = _ALLIANCES[index]
    alliance = _add(root, "alliance", attrs={"id": str(index)})
    if defaults.non_playable:
        _add(alliance, "non_playable")
    army = _add(alliance, "army")
    if defaults.time_period is not None:
        _add(army, "time_period", defaults.time_period)
    _add(army, "faction", side.faction)
    _add_deployment(army, side)
    _add_camera(army, "camera_start_position", defaults.camera_start)
    _add_camera(army, "camera_target_position", defaults.camera_target)
    _add(army, "campaign_ai_battle_hints", attrs={"aggression": defaults.aggression})
    for unit in side.units:
        _add_unit(army, unit, side, catalogue)
    victory = _add(alliance, "victory_condition")
    _add(victory, "kill_or_rout_enemy")
    _add(alliance, "rout_position", attrs={"x": defaults.rout_x, "y": defaults.rout_y})


def _add_description(root: ET.Element, battle: Battle) -> None:
    description = _add(root, "battle_description")
    _add(description, "battle_script", battle.name)
    _add(description, "time_of_day", "midday")
    _add(description, "type", "land_normal")
    _add(description, "duration", "1800")
    _add(description, "timeout_winning_alliance_index", "1")


def _add_environment(root: ET.Element, battle: Battle) -> None:
    weather = _add(root, "weather")
    _add(weather, "prevailing_wind", attrs={"x": "0", "y": "9"})
    _add(weather, "lighting", "default")
    _add(root, "sea_surface_name", "wind_level_2")
    climate = _add(root, "Climate")
    _add(climate, "name", battle.climate)
    season = _add(root, "Season")
    _add(season, "name", "season_summer")
    _add(root, "use_deployment_radar_on_loading_screen", "false")
    battle_map = _add(root, "battle_map_definition")
    _add(battle_map, "name", battle.map)


def build_battle_xml(battle: Battle, catalogue: Mapping[str, UnitType]) -> str:
    ET.register_namespace("xsi", _XSI)
    root = ET.Element(
        "battle",
        {f"{{{_XSI}}}noNamespaceSchemaLocation": "battle.xsd"},
    )
    for index, side in enumerate(battle.sides):
        _add_alliance(root, index, side, catalogue)
    _add_description(root, battle)
    _add_environment(root, battle)
    ET.indent(root, space="\t")
    body = ET.tostring(root, encoding="unicode")
    return "<?xml version='1.0' encoding='UTF-8'?>\n" + body + "\n"


class BattleService:
    def __init__(
        self,
        catalogue: UnitCatalogueRepository,
        output: BattleOutputRepository,
    ) -> None:
        self._catalogue = catalogue
        self._output = output

    def write(self, battle: Battle, script_source: Path, output_dir: Path) -> tuple[Path, Path]:
        xml_text = build_battle_xml(battle, self._catalogue.read())
        return self._output.write(output_dir, battle.name, xml_text, script_source)
