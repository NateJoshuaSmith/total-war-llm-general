import math

import pytest
from pydantic import ValidationError

from tw_general.models.battle import Battle


def _unit(**overrides: object) -> dict[str, object]:
    unit: dict[str, object] = {"type": "Gen_Early_Napoleon", "x": 0, "z": 450, "experience": 2}
    unit.update(overrides)
    return unit


def _side(**overrides: object) -> dict[str, object]:
    side: dict[str, object] = {
        "faction": "ita_french_republic",
        "zone": {"x": 0, "z": 400, "width": 800, "height": 200},
        "facing": 3.14,
        "units": [_unit()],
    }
    side.update(overrides)
    return side


def _battle(**overrides: object) -> dict[str, object]:
    battle: dict[str, object] = {
        "name": "test1",
        "map": "BattleTerrain/presets/nap_mp_grassy_flatlands/",
        "climate": "lc_eu_central_humid",
        "sides": [_side(), _side(faction="ita_austrian_alliance")],
    }
    battle.update(overrides)
    return battle


def test_rejects_a_missing_side() -> None:
    with pytest.raises(ValidationError) as caught:
        Battle.model_validate(_battle(sides=[_side()]))
    assert "exactly two sides" in str(caught.value)


@pytest.mark.parametrize("field", ["x", "z"])
@pytest.mark.parametrize("bad", [math.nan, math.inf, -math.inf])
def test_rejects_a_non_finite_position(field: str, bad: float) -> None:
    sides = [_side(units=[_unit(**{field: bad})]), _side()]
    with pytest.raises(ValidationError) as caught:
        Battle.model_validate(_battle(sides=sides))
    assert "finite" in str(caught.value)


def test_rejects_a_side_with_no_units() -> None:
    with pytest.raises(ValidationError) as caught:
        Battle.model_validate(_battle(sides=[_side(units=[]), _side()]))
    assert "at least one unit" in str(caught.value)


@pytest.mark.parametrize("field", ["width", "height"])
@pytest.mark.parametrize("bad", [0, -10])
def test_rejects_a_non_positive_zone_size(field: str, bad: int) -> None:
    zone = {"x": 0, "z": 0, "width": 800, "height": 200, field: bad}
    with pytest.raises(ValidationError) as caught:
        Battle.model_validate(_battle(sides=[_side(zone=zone), _side()]))
    assert "greater than 0" in str(caught.value)
