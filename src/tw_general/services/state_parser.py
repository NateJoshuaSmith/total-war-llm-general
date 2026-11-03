import math

from pydantic import ValidationError

from tw_general.models.battle_state import BattleState, Unit, UnitType

_OLD_FIELD_COUNT = 6
_NEW_FIELD_COUNT = 12


class _BadLine(Exception):
    pass


def parse_state(text: str) -> BattleState:
    tick: int | None = None
    last_seq: str | None = None
    units: list[Unit] = []
    skipped_lines = 0

    for raw_line in text.splitlines():
        line = raw_line.strip()
        if line == "":
            continue
        if line == "end":
            break
        key, sep, value = line.partition("=")
        if sep != "=":
            continue
        if key == "tick":
            tick = _parse_tick(value)
        elif key == "last_seq":
            last_seq = value if value != "" else None
        elif key == "u":
            unit = _parse_unit(value)
            if unit is None:
                skipped_lines += 1
            else:
                units.append(unit)

    if tick is None:
        raise ValueError("state file has no tick")
    return BattleState(
        tick=tick,
        last_seq=last_seq,
        units=units,
        skipped_lines=skipped_lines,
    )


def _parse_tick(value: str) -> int:
    try:
        return _require_int(value)
    except _BadLine:
        raise ValueError("state file tick is not a whole number") from None


def _parse_unit(value: str) -> Unit | None:
    fields = [field.strip() for field in value.split(",")]
    if len(fields) not in (_OLD_FIELD_COUNT, _NEW_FIELD_COUNT):
        return None
    try:
        return _unit(fields)
    except (_BadLine, ValidationError):
        return None


def _unit(fields: list[str]) -> Unit:
    alliance = _require_int(fields[0])
    army = _require_int(fields[1])
    index = _require_int(fields[2])
    x = _require_float(fields[3])
    z = _require_float(fields[4])
    men = _require_int(fields[5])
    if len(fields) == _OLD_FIELD_COUNT:
        return Unit(alliance=alliance, army=army, index=index, x=x, z=z, men=men)
    return Unit(
        alliance=alliance,
        army=army,
        index=index,
        x=x,
        z=z,
        men=men,
        initial_men=_optional_int(fields[6]),
        bearing=_optional_float(fields[7]),
        type=_optional_type(fields[8]),
        routing=_optional_flag(fields[9]),
        shattered=_optional_flag(fields[10]),
        ammo=_optional_int(fields[11]),
    )


def _require_int(value: str) -> int:
    if value.startswith(("+", "-")):
        digits = value[1:]
    else:
        digits = value
    if digits == "" or not digits.isdecimal():
        raise _BadLine
    return int(value)


def _optional_int(value: str) -> int | None:
    if value == "":
        return None
    return _require_int(value)


def _require_float(value: str) -> float:
    if value == "":
        raise _BadLine
    try:
        number = float(value)
    except ValueError:
        raise _BadLine from None
    if not math.isfinite(number):
        raise _BadLine
    return number


def _optional_float(value: str) -> float | None:
    if value == "":
        return None
    return _require_float(value)


def _optional_type(value: str) -> UnitType | None:
    if value == "":
        return None
    try:
        return UnitType(value)
    except ValueError:
        raise _BadLine from None


def _optional_flag(value: str) -> bool | None:
    if value == "":
        return None
    if value == "0":
        return False
    if value == "1":
        return True
    raise _BadLine
