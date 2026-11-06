import math

from tw_general.models.battle_state import BattleState, Unit, UnitType

# Shots still left. Line infantry usually start near 10, so 3 means nearly empty.
AMMO_LOW_AT = 3
WITHIN_METERS = 150
CAVALRY_THREAT_METERS = 300
WEAK_BELOW_PERCENT = 50

_COMPASS = ("N", "NE", "E", "SE", "S", "SW", "W", "NW")
# atan2 can fall a hair short of an exact boundary (202.5 came back as 202.49999999999997).
_BOUNDARY_SLOP_DEGREES = 1e-8


def distance(x1: float, z1: float, x2: float, z2: float) -> float:
    return math.hypot(x2 - x1, z2 - z1)


def direction(dx: float, dz: float) -> str:
    # dx is east, dz is north. An exact boundary belongs to the clockwise side.
    if dx == 0.0 and dz == 0.0:
        return "-"
    degrees = math.degrees(math.atan2(dx, dz))
    if degrees < 0.0:
        degrees += 360.0
    sector = math.floor((degrees + 22.5 + _BOUNDARY_SLOP_DEGREES) / 45.0)
    return _COMPASS[sector % 8]


def build_report(state: BattleState, our_alliance: int = 2) -> str:
    ours = [unit for unit in state.units if unit.alliance == our_alliance]
    enemies = [unit for unit in state.units if unit.alliance != our_alliance]
    ours_alive = [unit for unit in ours if unit.men > 0]
    enemies_alive = [unit for unit in enemies if unit.men > 0]

    lines = [_tick_line(state)]
    lines.append(_header(_ours_title(our_alliance), ours, ours_alive))
    lines.extend(_our_unit_line(unit, enemies_alive) for unit in ours_alive)
    lines.append(_header(_enemy_title(enemies), enemies, enemies_alive))
    lines.extend(_enemy_unit_line(unit) for unit in enemies_alive)
    lines.append("within150: " + _ids(_within(ours_alive, enemies_alive, WITHIN_METERS)))
    lines.append("cav300: " + _ids(_cavalry_threats(ours_alive, enemies_alive)))
    lines.append("below50: " + _ids(_weak(ours_alive)))
    return "\n".join(lines) + "\n"


def _tick_line(state: BattleState) -> str:
    line = f"tick {state.tick}"
    if state.skipped_lines:
        line += f" unreadable {state.skipped_lines}"
    return line


def _ours_title(our_alliance: int) -> str:
    return f"ours a{our_alliance}"


def _enemy_title(enemies: list[Unit]) -> str:
    alliances = sorted({unit.alliance for unit in enemies})
    if not alliances:
        return "enemy"
    return "enemy " + " ".join(f"a{alliance}" for alliance in alliances)


def _header(title: str, units: list[Unit], alive: list[Unit]) -> str:
    skipped = len(units) - len(alive)
    return f"{title} {_men(units)} units {len(alive)} skipped {skipped}"


def _men(units: list[Unit]) -> str:
    now = sum(unit.men for unit in units)
    known = [unit.initial_men for unit in units if unit.initial_men is not None]
    if len(known) == len(units):
        return f"men {now}/{sum(known)}"
    if not known:
        return f"men {now}/?"
    return f"men {now}/{sum(known)} unk {len(units) - len(known)}"


def _ids(units: list[Unit]) -> str:
    if not units:
        return "none"
    return " ".join(_unit_id(unit) for unit in units)


def _unit_id(unit: Unit) -> str:
    return f"a{unit.alliance}.{unit.army}.{unit.index}"


def _type_name(unit: Unit) -> str:
    if unit.type is None:
        return "?"
    return unit.type.value


def _percent(unit: Unit) -> int | None:
    initial = unit.initial_men
    if initial is None or initial <= 0:
        return None
    return (unit.men * 100 + initial // 2) // initial


def _strength(unit: Unit) -> str:
    percent = _percent(unit)
    if percent is None:
        return f"{unit.men} men"
    return f"{percent}%"


def _status(unit: Unit) -> str:
    parts: list[str] = []
    if unit.routing:
        parts.append("routing")
    if unit.shattered:
        parts.append("shattered")
    if unit.ammo is not None and unit.ammo <= AMMO_LOW_AT:
        parts.append("ammo-low")
    if not parts:
        return "ok"
    return " ".join(parts)


def _meters(value: float) -> int:
    if value >= 0:
        return math.floor(value + 0.5)
    return -math.floor(-value + 0.5)


def _our_unit_line(unit: Unit, enemies: list[Unit]) -> str:
    return f"{_body(unit)} {_near(unit, enemies)}"


def _enemy_unit_line(unit: Unit) -> str:
    return _body(unit)


def _body(unit: Unit) -> str:
    place = f"({_meters(unit.x)},{_meters(unit.z)})"
    return f"{_unit_id(unit)} {_type_name(unit)} {_strength(unit)} {place} {_status(unit)}"


def _near(unit: Unit, enemies: list[Unit]) -> str:
    nearest = _nearest(unit, enemies)
    if nearest is None:
        return "near none"
    meters = _meters(distance(unit.x, unit.z, nearest.x, nearest.z))
    facing = direction(nearest.x - unit.x, nearest.z - unit.z)
    return f"near {_unit_id(nearest)} {meters}m {facing}"


def _nearest(unit: Unit, enemies: list[Unit]) -> Unit | None:
    best: Unit | None = None
    best_key: tuple[float, int, int, int] | None = None
    for enemy in enemies:
        key = (
            distance(unit.x, unit.z, enemy.x, enemy.z),
            enemy.alliance,
            enemy.army,
            enemy.index,
        )
        if best_key is None or key < best_key:
            best_key = key
            best = enemy
    return best


def _within(units: list[Unit], others: list[Unit], limit: float) -> list[Unit]:
    return [unit for unit in units if _any_within(unit, others, limit)]


def _any_within(unit: Unit, others: list[Unit], limit: float) -> bool:
    return any(distance(unit.x, unit.z, other.x, other.z) <= limit for other in others)


def _cavalry_threats(ours: list[Unit], enemies: list[Unit]) -> list[Unit]:
    cavalry = [unit for unit in enemies if unit.type is UnitType.cav]
    infantry = [unit for unit in ours if unit.type is UnitType.inf]
    return _within(infantry, cavalry, CAVALRY_THREAT_METERS)


def _weak(units: list[Unit]) -> list[Unit]:
    weak: list[Unit] = []
    for unit in units:
        percent = _percent(unit)
        if percent is not None and percent < WEAK_BELOW_PERCENT:
            weak.append(unit)
    return weak
