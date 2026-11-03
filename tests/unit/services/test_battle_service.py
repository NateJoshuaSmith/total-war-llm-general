import xml.etree.ElementTree as ET
from pathlib import Path

import pytest

from tw_general.models.battle import Battle
from tw_general.repositories.battle_files import BattleRepository, UnitCatalogueRepository
from tw_general.services.battle_service import UnknownUnitTypeError, build_battle_xml

_REPO = Path(__file__).resolve().parents[3]


def _signature(element: ET.Element) -> tuple[object, ...]:
    text = (element.text or "").strip()
    attributes = tuple(element.attrib.items())
    children = tuple(_signature(child) for child in element)
    return (element.tag, attributes, text, children)


def test_test1_xml_matches_the_fixture() -> None:
    battle = BattleRepository().read(_REPO / "eval" / "battles" / "test1.json")
    catalogue = UnitCatalogueRepository(
        _REPO / "src" / "tw_general" / "data" / "napoleon_units.json"
    ).read()
    generated = build_battle_xml(battle, catalogue)
    expected = (_REPO / "tests" / "fixtures" / "battles" / "test1.xml").read_text(encoding="utf-8")
    assert _signature(ET.fromstring(generated)) == _signature(ET.fromstring(expected))


def test_unknown_unit_type_names_the_type() -> None:
    battle = Battle.model_validate(
        {
            "name": "tiny",
            "map": "BattleTerrain/presets/nap_mp_grassy_flatlands/",
            "climate": "lc_eu_central_humid",
            "sides": [
                {
                    "faction": "ita_french_republic",
                    "zone": {"x": 0, "z": 0, "width": 10, "height": 10},
                    "facing": 0,
                    "units": [{"type": "Not_A_Real_Unit", "x": 1, "z": 2, "experience": 0}],
                },
                {
                    "faction": "ita_austrian_alliance",
                    "zone": {"x": 0, "z": -10, "width": 10, "height": 10},
                    "facing": 0,
                    "units": [{"type": "Gen_Johann_Beaulieu", "x": 0, "z": -1, "experience": 0}],
                },
            ],
        }
    )
    with pytest.raises(UnknownUnitTypeError) as caught:
        build_battle_xml(battle, {})
    assert str(caught.value) == "Unknown unit type: Not_A_Real_Unit"
    assert caught.value.unit_type == "Not_A_Real_Unit"
