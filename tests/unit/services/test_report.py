import math
from pathlib import Path

import pytest

from tw_general.models.battle_state import BattleState, Unit, UnitType
from tw_general.services.report import AMMO_LOW_AT, build_report, direction, distance
from tw_general.services.state_parser import parse_state

FIXTURES = Path(__file__).resolve().parents[2] / "fixtures"
REPORTS = FIXTURES / "reports"


def _unit(
    alliance: int,
    index: int,
    x: float,
    z: float,
    *,
    kind: UnitType | None = UnitType.inf,
    men: int = 100,
    initial_men: int | None = 100,
    army: int = 1,
    ammo: int | None = None,
) -> Unit:
    return Unit(
        alliance=alliance,
        army=army,
        index=index,
        x=x,
        z=z,
        men=men,
        initial_men=initial_men,
        type=kind,
        ammo=ammo,
    )


def _flag(report: str, name: str) -> str:
    prefix = f"{name}:"
    for line in report.splitlines():
        if line.startswith(prefix):
            return line
    raise AssertionError(f"missing {name}")


@pytest.mark.parametrize(
    ("dx", "dz", "point"),
    [
        (0, 1, "N"),
        (1, 1, "NE"),
        (1, 0, "E"),
        (1, -1, "SE"),
        (0, -1, "S"),
        (-1, -1, "SW"),
        (-1, 0, "W"),
        (-1, 1, "NW"),
    ],
)
def test_eight_compass_directions(dx: float, dz: float, point: str) -> None:
    assert direction(dx, dz) == point


def test_zero_step_has_no_direction() -> None:
    assert direction(0, 0) == "-"


@pytest.mark.parametrize(
    ("degrees", "point"),
    [
        (22.5, "NE"),
        (67.5, "E"),
        (112.5, "SE"),
        (157.5, "S"),
        (202.5, "SW"),
        (247.5, "W"),
        (292.5, "NW"),
        (337.5, "N"),
    ],
)
def test_exact_boundaries_go_clockwise(degrees: float, point: str) -> None:
    radians = math.radians(degrees)
    assert direction(math.sin(radians), math.cos(radians)) == point


def test_just_inside_a_boundary_stays_put() -> None:
    radians = math.radians(22.5 - 0.01)
    assert direction(math.sin(radians), math.cos(radians)) == "N"


def test_distance_is_straight_line_meters() -> None:
    assert distance(0, 0, 3, 4) == 5
    assert distance(-2, -2, -2, 2) == 4


def test_zero_distance() -> None:
    assert distance(5, -3, 5, -3) == 0


@pytest.mark.parametrize("degrees", [0, 45, 90, 135, 180, 225, 270, 315])
def test_distance_along_each_compass_direction(degrees: float) -> None:
    radians = math.radians(degrees)
    assert distance(0, 0, math.sin(radians), math.cos(radians)) == pytest.approx(1)


def test_each_state_fixture_matches_its_snapshot() -> None:
    paths = sorted(FIXTURES.glob("state_*.txt"))
    assert [path.name for path in paths] == [
        "state_v0_test1_tick20.txt",
        "state_v1_handwritten.txt",
    ]
    for path in paths:
        report = build_report(parse_state(path.read_bytes().decode("ascii")))
        snapshot = (REPORTS / path.name).read_bytes()
        assert snapshot.decode("ascii") == report
        assert b"\r" not in snapshot


def test_forty_unit_report_stays_under_8000_characters() -> None:
    units: list[Unit] = []
    for index in range(1, 21):
        units.append(
            Unit(
                alliance=2,
                army=1,
                index=index,
                x=-1500.0 + index,
                z=800.0 - index * 3,
                men=40,
                initial_men=160,
                type=UnitType.inf,
                routing=True,
                shattered=True,
                ammo=0,
            )
        )
        units.append(
            Unit(
                alliance=1,
                army=1,
                index=index,
                x=1500.0 - index,
                z=-800.0 + index * 3,
                men=12,
                initial_men=60,
                type=UnitType.cav,
                routing=True,
                ammo=1,
            )
        )
    report = build_report(BattleState(tick=99, units=units))
    assert len(report) < 8000
    assert sum(line.startswith("a") for line in report.splitlines()) == 40


@pytest.mark.parametrize(
    ("gap", "raised"),
    [(250, True), (300, True), (350, False)],
)
def test_enemy_cavalry_near_our_infantry(gap: float, raised: bool) -> None:
    state = BattleState(
        tick=1,
        units=[
            _unit(2, 1, 0, 0, kind=UnitType.inf),
            _unit(1, 1, gap, 0, kind=UnitType.cav),
        ],
    )
    line = _flag(build_report(state), "cav300")
    assert line == ("cav300: a2.1.1" if raised else "cav300: none")


def test_cavalry_flag_ignores_other_pairings() -> None:
    state = BattleState(
        tick=1,
        units=[
            _unit(2, 1, 0, 0, kind=UnitType.cav),
            _unit(1, 1, 250, 0, kind=UnitType.inf),
        ],
    )
    assert _flag(build_report(state), "cav300") == "cav300: none"


@pytest.mark.parametrize(("gap", "raised"), [(150, True), (151, False)])
def test_enemies_within_150m(gap: float, raised: bool) -> None:
    state = BattleState(
        tick=1,
        units=[
            _unit(2, 1, 0, 0),
            _unit(1, 1, gap, 0, kind=UnitType.art),
        ],
    )
    line = _flag(build_report(state), "within150")
    assert line == ("within150: a2.1.1" if raised else "within150: none")


def test_below_half_strength() -> None:
    state = BattleState(
        tick=1,
        units=[
            _unit(2, 1, 0, 0, men=49, initial_men=100),
            _unit(2, 2, 10, 0, men=50, initial_men=100),
            _unit(2, 3, 20, 0, men=10, initial_men=None),
            _unit(1, 1, 1000, 0),
        ],
    )
    assert _flag(build_report(state), "below50") == "below50: a2.1.1"


def test_ammo_at_the_threshold_is_low() -> None:
    state = BattleState(
        tick=1,
        units=[
            _unit(2, 1, 0, 0, ammo=AMMO_LOW_AT),
            _unit(2, 2, 10, 0, ammo=AMMO_LOW_AT + 1),
            _unit(2, 3, 20, 0, ammo=None),
            _unit(1, 1, 500, 0),
        ],
    )
    report = build_report(state)
    assert "a2.1.1 inf 100% (0,0) ammo-low" in report
    assert "a2.1.2 inf 100% (10,0) ok" in report
    assert "a2.1.3 inf 100% (20,0) ok" in report


def test_dead_units_are_skipped_and_counted() -> None:
    state = BattleState(
        tick=1,
        units=[
            _unit(2, 1, 0, 0, men=10, initial_men=100),
            _unit(2, 2, 5, 0, men=0, initial_men=100),
            _unit(1, 1, 10, 0, men=0, initial_men=80, kind=UnitType.cav),
        ],
    )
    report = build_report(state)
    assert "a2.1.2" not in report
    assert "a1.1.1" not in report
    assert "ours a2 men 10/200 units 1 skipped 1" in report
    assert "enemy a1 men 0/80 units 0 skipped 1" in report
    assert _flag(report, "within150") == "within150: none"
    assert _flag(report, "cav300") == "cav300: none"


def test_nearest_enemy_is_north_when_z_increases() -> None:
    state = BattleState(
        tick=1,
        units=[
            _unit(2, 1, 0, 0),
            _unit(1, 1, 0, 100),
            _unit(1, 2, 300, 0),
        ],
    )
    assert "near a1.1.1 100m N" in build_report(state)


def test_equal_distance_picks_the_lower_index() -> None:
    state = BattleState(
        tick=1,
        units=[
            _unit(2, 1, 0, 0),
            _unit(1, 2, 100, 0),
            _unit(1, 1, -100, 0),
        ],
    )
    assert "near a1.1.1 100m W" in build_report(state)


def test_no_living_enemy() -> None:
    state = BattleState(tick=1, units=[_unit(2, 1, 0, 0)])
    report = build_report(state)
    assert "near none" in report
    assert "enemy men 0/0 units 0 skipped 0" in report


def test_positions_round_to_the_nearest_meter() -> None:
    state = BattleState(
        tick=1,
        units=[
            _unit(2, 1, 1.5, -1.5),
            _unit(1, 1, 1000, 0),
        ],
    )
    assert "a2.1.1 inf 100% (2,-2)" in build_report(state)


def test_unknown_starting_strength_is_called_out() -> None:
    state = BattleState(
        tick=1,
        units=[
            _unit(2, 1, 0, 0, men=80, initial_men=100),
            _unit(2, 2, 10, 0, men=40, initial_men=None),
            _unit(1, 1, 500, 0, men=10, initial_men=10),
        ],
    )
    assert "ours a2 men 120/100 unk 1 units 2 skipped 0" in build_report(state)


def test_unreadable_lines_are_noted() -> None:
    state = BattleState(tick=4, units=[_unit(2, 1, 0, 0)], skipped_lines=2)
    assert build_report(state).startswith("tick 4 unreadable 2\n")
