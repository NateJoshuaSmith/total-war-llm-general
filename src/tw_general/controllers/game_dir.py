import os
from pathlib import Path

DEFAULT_GAME_DIR = Path(r"D:\SteamLibrary\steamapps\common\Napoleon Total War")


def resolve_game_dir(argument: str | None) -> Path:
    if argument:
        return Path(argument)
    from_env = os.environ.get("TWLLM_GAME_DIR")
    if from_env:
        return Path(from_env)
    return DEFAULT_GAME_DIR


def resolve_scripts_dir(argument: str | None) -> Path:
    if argument:
        return Path(argument)
    from_env = os.environ.get("TWLLM_SCRIPTS_DIR")
    if from_env:
        return Path(from_env)
    appdata = os.environ.get("APPDATA", "")
    return Path(appdata) / "The Creative Assembly" / "Napoleon" / "scripts"
