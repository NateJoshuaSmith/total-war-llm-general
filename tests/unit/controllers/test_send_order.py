from pathlib import Path

import pytest

from tw_general.controllers.send_order import main


def _fields(path: Path) -> dict[str, str]:
    text = path.read_text(encoding="ascii")
    assert "\r" not in text
    assert text.endswith("end\n")
    return dict(line.split("=", 1) for line in text.splitlines() if line != "end")


def test_writes_the_orders_file(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    main(["--unit", "1", "--x", "536", "--z", "363", "--game-dir", str(tmp_path)])
    fields = _fields(tmp_path / "twllm_orders.txt")
    assert int(fields["seq"]) > 0
    assert fields["unit"] == "1"
    assert fields["x"] == "536.0"
    assert fields["z"] == "363.0"
    assert fields["run"] == "1"
    assert not (tmp_path / "twllm_orders.txt.tmp").exists()
    message = capsys.readouterr().out
    assert f"Sent order {fields['seq']}: unit 1 -> (536.0, 363.0), running." in message


def test_walk_flag_writes_run_zero(tmp_path: Path) -> None:
    main(["--unit", "1", "--x", "283.5", "--z", "212.7", "--walk", "--game-dir", str(tmp_path)])
    fields = _fields(tmp_path / "twllm_orders.txt")
    assert fields["run"] == "0"
    assert fields["x"] == "283.5"
    assert fields["z"] == "212.7"


def test_missing_game_dir_exits_2(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    missing = tmp_path / "no-such-game"
    with pytest.raises(SystemExit) as caught:
        main(["--unit", "1", "--x", "1", "--z", "1", "--game-dir", str(missing)])
    assert caught.value.code == 2
    assert "does not exist" in capsys.readouterr().err
    assert not (tmp_path / "twllm_orders.txt").exists()


def test_release_writes_a_release_order(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    main(["--unit", "1", "--release", "--game-dir", str(tmp_path)])
    fields = _fields(tmp_path / "twllm_orders.txt")
    assert int(fields["seq"]) > 0
    assert fields["unit"] == "1"
    assert fields["action"] == "release"
    assert "x" not in fields
    assert "z" not in fields
    assert "run" not in fields
    message = capsys.readouterr().out
    assert f"Sent order {fields['seq']}: released unit 1." in message


def test_missing_x_without_release_errors(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    with pytest.raises(SystemExit) as caught:
        main(["--unit", "1", "--z", "1", "--game-dir", str(tmp_path)])
    assert caught.value.code == 2
    assert "--x" in capsys.readouterr().err
    assert not (tmp_path / "twllm_orders.txt").exists()
