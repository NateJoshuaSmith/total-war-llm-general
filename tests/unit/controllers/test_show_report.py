from pathlib import Path

import pytest

from tw_general.controllers.show_report import main
from tw_general.services.report import build_report
from tw_general.services.state_parser import parse_state

FIXTURES = Path(__file__).resolve().parents[2] / "fixtures"
V1 = FIXTURES / "state_v1_handwritten.txt"


def test_prints_the_report(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    text = V1.read_bytes().decode("ascii")
    (tmp_path / "twllm_state.txt").write_bytes(text.encode("ascii"))
    main(["--game-dir", str(tmp_path)])
    assert capsys.readouterr().out == build_report(parse_state(text))


def test_our_alliance_flag(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    body = "tick=1\nu=1,1,1,0,0,10,10,0,inf,0,0,10\nend\n"
    (tmp_path / "twllm_state.txt").write_bytes(body.encode("ascii"))
    main(["--game-dir", str(tmp_path), "--our-alliance", "1"])
    out = capsys.readouterr().out
    assert "ours a1 " in out
    assert "enemy men 0/0 units 0 skipped 0" in out


def test_missing_file_exits_1(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    with pytest.raises(SystemExit) as caught:
        main(["--game-dir", str(tmp_path)])
    assert caught.value.code == 1
    err = capsys.readouterr().err
    assert "missing or half-written" in err
    assert "twllm_state.txt" in err


def test_half_written_file_exits_1(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    (tmp_path / "twllm_state.txt").write_bytes(b"tick=1\n")
    with pytest.raises(SystemExit) as caught:
        main(["--game-dir", str(tmp_path)])
    assert caught.value.code == 1
    captured = capsys.readouterr()
    assert "missing or half-written" in captured.err
    assert captured.out == ""


def test_file_without_a_tick_exits_1(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    (tmp_path / "twllm_state.txt").write_bytes(b"end\n")
    with pytest.raises(SystemExit) as caught:
        main(["--game-dir", str(tmp_path)])
    assert caught.value.code == 1
    assert "not usable" in capsys.readouterr().err


def test_missing_game_dir_exits_2(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    missing = tmp_path / "no-such-game"
    with pytest.raises(SystemExit) as caught:
        main(["--game-dir", str(missing)])
    assert caught.value.code == 2
    assert "does not exist" in capsys.readouterr().err
