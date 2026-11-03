from pathlib import Path

import pytest

from tw_general.models.battle_state import BattleState, Unit, UnitType
from tw_general.services.state_parser import parse_state

FIXTURES = Path(__file__).resolve().parents[2] / "fixtures"
V0 = FIXTURES / "state_v0_test1_tick20.txt"
V1 = FIXTURES / "state_v1_handwritten.txt"


def _unit(state: BattleState, alliance: int, index: int) -> Unit:
    for unit in state.units:
        if unit.alliance == alliance and unit.index == index:
            return unit
    raise AssertionError(f"missing unit alliance {alliance} index {index}")


def test_v0_fixture() -> None:
    text = V0.read_bytes().decode("ascii")
    assert "\r\n" in text
    state = parse_state(text)

    assert state.tick == 20
    assert state.last_seq == "1793570263771"
    assert isinstance(state.last_seq, str)
    assert len(state.last_seq) == 13
    assert len(state.units) == 13
    assert state.skipped_lines == 0

    beaulieu = _unit(state, alliance=2, index=1)
    assert beaulieu.army == 1
    assert beaulieu.x == pytest.approx(-1.6)
    assert beaulieu.z == pytest.approx(-8.7)
    assert beaulieu.men == 24
    assert beaulieu.initial_men is None
    assert beaulieu.bearing is None
    assert beaulieu.type is None
    assert beaulieu.routing is None
    assert beaulieu.shattered is None
    assert beaulieu.ammo is None


def test_v0_fixture_with_lf_line_endings() -> None:
    text = V0.read_bytes().decode("ascii").replace("\r\n", "\n")
    assert "\r" not in text
    state = parse_state(text)
    assert state.tick == 20
    assert state.last_seq == "1793570263771"
    assert len(state.units) == 13
    beaulieu = _unit(state, alliance=2, index=1)
    assert beaulieu.x == pytest.approx(-1.6)
    assert beaulieu.z == pytest.approx(-8.7)


def test_handwritten_v1_fixture() -> None:
    text = V1.read_bytes().decode("ascii")
    assert "\r\n" in text
    state = parse_state(text)

    assert state.tick == 20
    assert state.last_seq == "1793570263771"
    assert isinstance(state.last_seq, str)
    assert len(state.units) == 5
    assert state.skipped_lines == 0

    cavalry = _unit(state, alliance=1, index=2)
    assert cavalry.type is UnitType.cav
    assert cavalry.men == 40
    assert cavalry.initial_men == 60
    assert cavalry.bearing == pytest.approx(175.5)
    assert cavalry.routing is True
    assert cavalry.shattered is True
    assert cavalry.ammo == 0

    beaulieu = _unit(state, alliance=2, index=1)
    assert beaulieu.type is UnitType.inf
    assert beaulieu.bearing == pytest.approx(90.0)
    assert beaulieu.routing is False
    assert beaulieu.shattered is False
    assert beaulieu.ammo is None

    shifted = _unit(state, alliance=2, index=3)
    assert shifted.x == pytest.approx(10.0)
    assert shifted.z == pytest.approx(-5.0)
    assert shifted.men == 120
    assert shifted.initial_men == 160
    assert shifted.bearing is None
    assert shifted.type is UnitType.inf
    assert shifted.routing is False
    assert shifted.shattered is None
    assert shifted.ammo == 48

    untyped = _unit(state, alliance=2, index=7)
    assert untyped.type is None
    assert untyped.bearing == pytest.approx(10.0)
    assert untyped.routing is False
    assert untyped.shattered is False
    assert untyped.ammo == 5


def test_handwritten_v1_fixture_with_lf_line_endings() -> None:
    text = V1.read_bytes().decode("ascii").replace("\r\n", "\n")
    state = parse_state(text)
    assert len(state.units) == 5
    assert _unit(state, alliance=2, index=3).bearing is None
    assert _unit(state, alliance=2, index=3).shattered is None
    assert _unit(state, alliance=2, index=1).ammo is None


def test_bad_unit_line_among_good_ones() -> None:
    text = "\n".join(
        [
            "tick=4",
            "last_seq=1793570263771",
            "u=1,1,1,0.0,1.0,10",
            "u=1,1,2,nope,1.0,10",
            "u=1,1,3,0.0,1.0",
            "u=1,1,4,0.0,1.0,10,10,0,tank,0,0,1",
            "u=9,9,9,3.0,4.0,5",
            "end",
        ]
    )
    state = parse_state(text)
    assert [(unit.alliance, unit.index) for unit in state.units] == [(1, 1), (9, 9)]
    assert state.skipped_lines == 3
    assert state.last_seq == "1793570263771"


def test_nan_and_inf_positions_are_skipped() -> None:
    text = "\n".join(
        [
            "tick=1",
            "u=1,1,1,nan,-8.7,24",
            "u=2,1,1,-1.6,-8.7,24",
            "u=2,1,2,-1.6,inf,24",
            "u=2,1,3,-1.6,-8.7,24,24,nan,inf,0,0,1",
            "end",
        ]
    )
    state = parse_state(text)
    assert [(unit.alliance, unit.index) for unit in state.units] == [(2, 1)]
    assert state.skipped_lines == 3


def test_missing_tick_is_an_error() -> None:
    with pytest.raises(ValueError, match="tick"):
        parse_state("last_seq=1793570263771\nu=1,1,1,0,0,10\nend\n")


def test_tick_that_is_not_a_number_is_an_error() -> None:
    with pytest.raises(ValueError, match="tick"):
        parse_state("tick=abc\nend\n")


def test_unknown_keys_are_ignored() -> None:
    text = "\n".join(
        [
            "tick=8",
            "future=keep-going",
            "u=2,1,1,-1.6,-8.7,24",
            "not a unit",
            "end",
            "u=9,9,9,0,0,1",
        ]
    )
    state = parse_state(text)
    assert state.tick == 8
    assert state.last_seq is None
    assert len(state.units) == 1
    assert state.skipped_lines == 0
    assert state.units[0].alliance == 2


def test_empty_last_seq_is_none() -> None:
    state = parse_state("tick=1\nlast_seq=\nu=1,1,1,0.0,1.0,10\nend\n")
    assert state.last_seq is None
    assert len(state.units) == 1
