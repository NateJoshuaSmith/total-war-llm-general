def _check_battle_name(battle: str) -> None:
    if not battle or not all(c.isascii() and (c.isalnum() or c == "_") for c in battle):
        raise ValueError("name may only contain letters, digits and _")


def startup_line(battle: str) -> str:
    _check_battle_name(battle)
    return f"game_startup_mode battle data/twllm_battles/{battle}/{battle}.xml;"


def is_startup_line(line: str) -> bool:
    stripped = line.lstrip()
    prefix = "game_startup_mode"
    if not stripped.startswith(prefix):
        return False
    rest = stripped[len(prefix) :]
    return rest == "" or rest[0].isspace() or rest[0] == ";"


def edit_startup_lines(lines: list[str], battle: str | None) -> list[str]:
    """Return lines with the startup command set to `battle`, or removed when `battle` is None."""
    if battle is None:
        return [line for line in lines if not is_startup_line(line)]

    new_line = startup_line(battle)
    edited: list[str] = []
    placed = False
    for line in lines:
        if is_startup_line(line):
            if not placed:
                edited.append(new_line)
                placed = True
            continue
        edited.append(line)
    if not placed:
        edited.append(new_line)
    return edited
