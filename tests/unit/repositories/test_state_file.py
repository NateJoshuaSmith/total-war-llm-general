from pathlib import Path

import pytest

from tw_general.repositories.state_file import StateFileRepository

V0 = Path(__file__).resolve().parents[2] / "fixtures" / "state_v0_test1_tick20.txt"


def test_reads_complete_file(tmp_path: Path) -> None:
    payload = b"tick=1\r\nlast_seq=1793570263771\r\nu=1,1,1,0.0,1.0,10\r\nend\r\n"
    path = tmp_path / "twllm_state.txt"
    path.write_bytes(payload)
    assert StateFileRepository(path).read() == payload.decode("ascii")


def test_reads_v0_fixture() -> None:
    text = StateFileRepository(V0).read()
    assert text == V0.read_bytes().decode("ascii")
    assert text is not None
    assert text.splitlines()[-1] == "end"


def test_end_without_trailing_newline(tmp_path: Path) -> None:
    path = tmp_path / "twllm_state.txt"
    path.write_bytes(b"tick=2\nend")
    assert StateFileRepository(path).read() == "tick=2\nend"


def test_missing_file_returns_none(tmp_path: Path) -> None:
    assert StateFileRepository(tmp_path / "twllm_state.txt").read() is None


def test_no_end_line_returns_none(tmp_path: Path) -> None:
    path = tmp_path / "twllm_state.txt"
    path.write_bytes(b"tick=1\r\nu=1,1,1,0.0,1.0,10\r\n")
    assert StateFileRepository(path).read() is None


def test_empty_file_returns_none(tmp_path: Path) -> None:
    path = tmp_path / "twllm_state.txt"
    path.write_bytes(b"")
    assert StateFileRepository(path).read() is None


def test_locked_file_returns_none(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    path = tmp_path / "twllm_state.txt"
    path.write_bytes(b"tick=1\r\nend\r\n")

    def locked(*args: object, **kwargs: object) -> bytes:
        raise PermissionError("locked")

    monkeypatch.setattr(Path, "read_bytes", locked)
    assert StateFileRepository(path).read() is None
