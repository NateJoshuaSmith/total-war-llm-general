import os
from pathlib import Path

import pytest

import tw_general.repositories.user_script as user_script
from tw_general.repositories.user_script import UserScriptRepository

_TEXT = "mod twllm_probe.pack;\r\nvfs_log_level 1;\r\n"
_LINES = ["mod twllm_probe.pack;", "vfs_log_level 1;"]


def _utf16(text: str) -> bytes:
    return b"\xff\xfe" + text.encode("utf-16-le")


def test_writes_utf16_le_bom_and_crlf(tmp_path: Path) -> None:
    repository = UserScriptRepository(tmp_path)
    repository.write_lines(_LINES)
    path = tmp_path / "user.script.txt"
    data = path.read_bytes()
    assert data.startswith(b"\xff\xfe")
    assert b"\r\x00\n\x00" in data
    assert data.decode("utf-16") == _TEXT
    assert repository.read_lines() == _LINES
    assert not Path(str(path) + ".tmp").exists()
    assert not Path(str(path) + ".twllm-backup").exists()


def test_round_trip_keeps_crlf_bytes(tmp_path: Path) -> None:
    path = tmp_path / "user.script.txt"
    original = _utf16(_TEXT)
    path.write_bytes(original)
    repository = UserScriptRepository(tmp_path)
    repository.write_lines(repository.read_lines() or [])
    assert path.read_bytes() == original


def test_backup_is_made_once_and_not_overwritten(tmp_path: Path) -> None:
    path = tmp_path / "user.script.txt"
    original = _utf16(_TEXT)
    path.write_bytes(original)
    repository = UserScriptRepository(tmp_path)
    repository.write_lines(
        [*_LINES, "game_startup_mode battle data/twllm_battles/test1/test1.xml;"]
    )
    backup = Path(str(path) + ".twllm-backup")
    assert backup.read_bytes() == original
    repository.write_lines(["mod other.pack;"])
    assert backup.read_bytes() == original
    assert path.read_bytes() == _utf16("mod other.pack;\r\n")
    assert not Path(str(path) + ".tmp").exists()


def test_rejects_a_file_without_a_bom(tmp_path: Path) -> None:
    path = tmp_path / "user.script.txt"
    path.write_bytes(b"mod twllm_probe.pack;\r\n")
    with pytest.raises(UnicodeError):
        UserScriptRepository(tmp_path).read_lines()
    assert path.read_bytes() == b"mod twllm_probe.pack;\r\n"


def test_retries_permission_error_on_replace(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    path = tmp_path / "user.script.txt"
    real_replace = os.replace
    calls = {"n": 0}
    sleeps: list[float] = []

    def flaky(src: str, dst: str) -> None:
        calls["n"] += 1
        if calls["n"] == 1:
            raise PermissionError("locked")
        real_replace(src, dst)

    monkeypatch.setattr(user_script.os, "replace", flaky)
    monkeypatch.setattr(user_script.time, "sleep", sleeps.append)
    UserScriptRepository(tmp_path).write_lines(_LINES)

    assert calls["n"] == 2
    assert sleeps == [0.05]
    assert path.read_bytes() == _utf16(_TEXT)
    assert not Path(str(path) + ".tmp").exists()
