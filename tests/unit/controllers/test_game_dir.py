from pathlib import Path

import pytest

from tw_general.controllers.game_dir import DEFAULT_GAME_DIR, resolve_game_dir


def test_argument_wins(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    monkeypatch.setenv("TWLLM_GAME_DIR", str(tmp_path))
    assert resolve_game_dir(r"D:\custom") == Path(r"D:\custom")


def test_env_when_argument_is_missing(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    monkeypatch.setenv("TWLLM_GAME_DIR", str(tmp_path))
    assert resolve_game_dir(None) == tmp_path


def test_steam_path_when_unset(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("TWLLM_GAME_DIR", raising=False)
    assert resolve_game_dir(None) == DEFAULT_GAME_DIR
