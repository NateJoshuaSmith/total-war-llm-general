import math

import pytest
from pydantic import ValidationError

from tw_general.models.order import MoveOrder


def test_valid_order() -> None:
    order = MoveOrder(seq=1730400000000, unit=1, x=536.0, z=363.0, run=True)
    assert order.seq == 1730400000000
    assert order.unit == 1
    assert order.x == 536.0
    assert order.z == 363.0
    assert order.run is True
    with pytest.raises(ValidationError):
        order.seq = 2


def test_rejects_seq_zero() -> None:
    with pytest.raises(ValidationError):
        MoveOrder(seq=0, unit=1, x=0.0, z=0.0, run=True)


def test_rejects_unit_zero() -> None:
    with pytest.raises(ValidationError):
        MoveOrder(seq=1, unit=0, x=0.0, z=0.0, run=False)


@pytest.mark.parametrize("field", ["x", "z"])
@pytest.mark.parametrize("bad", [math.nan, math.inf, -math.inf])
def test_rejects_non_finite_coordinates(field: str, bad: float) -> None:
    values: dict[str, object] = {"seq": 1, "unit": 1, "x": 0.0, "z": 0.0, "run": True}
    values[field] = bad
    with pytest.raises(ValidationError):
        MoveOrder(**values)
