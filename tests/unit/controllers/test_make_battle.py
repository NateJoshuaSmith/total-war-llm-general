import xml.etree.ElementTree as ET
from pathlib import Path

import pytest

from tw_general.controllers.make_battle import main

_REPO = Path(__file__).resolve().parents[3]
_SCRIPT = _REPO / "game" / "napoleon" / "lodi_battle.battle_script"
_FIXTURE = _REPO / "tests" / "fixtures" / "battles" / "test1.xml"


def _signature(element: ET.Element) -> tuple[object, ...]:
    text = (element.text or "").strip()
    attributes = tuple(element.attrib.items())
    children = tuple(_signature(child) for child in element)
    return (element.tag, attributes, text, children)


def test_writes_xml_and_a_byte_copy_of_the_script(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    main(["--battle", "test1", "--game-dir", str(tmp_path)])
    folder = tmp_path / "data" / "twllm_battles" / "test1"
    xml_path = folder / "test1.xml"
    script_path = folder / "test1.battle_script"
    assert script_path.read_bytes() == _SCRIPT.read_bytes()
    written = xml_path.read_text(encoding="utf-8")
    expected = _FIXTURE.read_text(encoding="utf-8")
    assert _signature(ET.fromstring(written)) == _signature(ET.fromstring(expected))
    message = capsys.readouterr().out
    assert str(xml_path) in message
    assert str(script_path) in message


def test_missing_game_dir_exits_2(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    missing = tmp_path / "no-such-game"
    with pytest.raises(SystemExit) as caught:
        main(["--battle", "test1", "--game-dir", str(missing)])
    assert caught.value.code == 2
    assert "does not exist" in capsys.readouterr().err
    assert not (tmp_path / "data").exists()


def test_missing_battle_file_exits_2(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    with pytest.raises(SystemExit) as caught:
        main(["--battle", "no-such-battle", "--game-dir", str(tmp_path)])
    assert caught.value.code == 2
    assert "no-such-battle.json" in capsys.readouterr().err
    assert not (tmp_path / "data").exists()
