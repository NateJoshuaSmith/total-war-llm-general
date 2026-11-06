from pathlib import Path

import pytest

from tw_general.controllers.battle_startup import main

_TEXT = "mod twllm_probe.pack;\r\nvfs_log_level 1;\r\n"
_LINE = "game_startup_mode battle data/twllm_battles/test1/test1.xml;"


def _utf16(text: str) -> bytes:
    return b"\xff\xfe" + text.encode("utf-16-le")


def _layout(tmp_path: Path, *, xml: bool) -> tuple[Path, Path]:
    scripts = tmp_path / "scripts"
    scripts.mkdir()
    game = tmp_path / "game"
    if xml:
        folder = game / "data" / "twllm_battles" / "test1"
        folder.mkdir(parents=True)
        (folder / "test1.xml").write_text("<battle />\n", encoding="utf-8")
    else:
        game.mkdir()
    return scripts, game


def test_missing_battle_xml_exits_2_and_leaves_the_script(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    scripts, game = _layout(tmp_path, xml=False)
    script = scripts / "user.script.txt"
    original = _utf16(_TEXT)
    script.write_bytes(original)

    with pytest.raises(SystemExit) as caught:
        main(["--battle", "test1", "--game-dir", str(game), "--scripts-dir", str(scripts)])

    assert caught.value.code == 2
    assert "make_battle" in capsys.readouterr().err
    assert script.read_bytes() == original
    assert not Path(str(script) + ".twllm-backup").exists()


def test_battle_then_off_restores_the_original_bytes(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    scripts, game = _layout(tmp_path, xml=True)
    script = scripts / "user.script.txt"
    original = _utf16(_TEXT)
    script.write_bytes(original)

    main(["--battle", "test1", "--game-dir", str(game), "--scripts-dir", str(scripts)])
    added = capsys.readouterr().out
    assert f"Added line: {_LINE}" in added
    assert str(script) in added
    assert _LINE in script.read_bytes().decode("utf-16")

    main(["--off", "--scripts-dir", str(scripts)])
    removed = capsys.readouterr().out
    assert f"Removed line: {_LINE}" in removed
    assert str(script) in removed
    assert script.read_bytes() == original
    assert Path(str(script) + ".twllm-backup").read_bytes() == original


def test_off_leaves_a_missing_file_missing(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    scripts, _game = _layout(tmp_path, xml=False)
    main(["--off", "--scripts-dir", str(scripts)])
    script = scripts / "user.script.txt"
    assert not script.exists()
    assert str(script) in capsys.readouterr().out


def test_off_with_no_startup_line_does_not_rewrite(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    scripts, _game = _layout(tmp_path, xml=False)
    script = scripts / "user.script.txt"
    original = _utf16(_TEXT)
    script.write_bytes(original)
    main(["--off", "--scripts-dir", str(scripts)])
    message = capsys.readouterr().out
    assert "No game_startup_mode line" in message
    assert script.read_bytes() == original
    assert not Path(str(script) + ".twllm-backup").exists()


def test_bad_name_exits_2_and_leaves_the_script(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    scripts, game = _layout(tmp_path, xml=True)
    script = scripts / "user.script.txt"
    original = _utf16(_TEXT)
    script.write_bytes(original)
    with pytest.raises(SystemExit) as caught:
        main(["--battle", "../test1", "--game-dir", str(game), "--scripts-dir", str(scripts)])
    assert caught.value.code == 2
    assert "letters" in capsys.readouterr().err
    assert script.read_bytes() == original


def test_file_without_bom_exits_1_and_is_unchanged(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    scripts, game = _layout(tmp_path, xml=True)
    script = scripts / "user.script.txt"
    script.write_bytes(b"mod twllm_probe.pack;\r\n")
    with pytest.raises(SystemExit) as caught:
        main(["--battle", "test1", "--game-dir", str(game), "--scripts-dir", str(scripts)])
    assert caught.value.code == 1
    assert "UTF-16" in capsys.readouterr().err
    assert script.read_bytes() == b"mod twllm_probe.pack;\r\n"
    assert not Path(str(script) + ".twllm-backup").exists()


def test_scripts_dir_can_come_from_the_environment(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    scripts, _game = _layout(tmp_path, xml=False)
    monkeypatch.setenv("TWLLM_SCRIPTS_DIR", str(scripts))
    main(["--off"])
    assert not (scripts / "user.script.txt").exists()
