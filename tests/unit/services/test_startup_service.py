import pytest

from tw_general.services.startup_service import edit_startup_lines

_LINE = "game_startup_mode battle data/twllm_battles/test1/test1.xml;"
_OTHER = ["mod twllm_probe.pack;", "vfs_log_level 1;"]


def test_adds_a_startup_line_after_other_lines() -> None:
    original = list(_OTHER)
    assert edit_startup_lines(original, "test1") == [*_OTHER, _LINE]
    assert original == _OTHER


def test_replaces_an_existing_startup_line() -> None:
    lines = [
        "mod twllm_probe.pack;",
        "game_startup_mode battle data/twllm_battles/old/old.xml;",
        "vfs_log_level 1;",
    ]
    assert edit_startup_lines(lines, "test1") == [
        "mod twllm_probe.pack;",
        _LINE,
        "vfs_log_level 1;",
    ]


def test_several_startup_lines_become_one() -> None:
    lines = [
        "game_startup_mode battle data/twllm_battles/old/old.xml;",
        "mod twllm_probe.pack;",
        "game_startup_mode battle data/twllm_battles/older/older.xml;",
    ]
    assert edit_startup_lines(lines, "test1") == [_LINE, "mod twllm_probe.pack;"]


def test_off_removes_the_startup_line_and_keeps_the_rest() -> None:
    assert edit_startup_lines([*_OTHER, _LINE], None) == _OTHER


def test_other_lines_stay_character_for_character() -> None:
    lines = ["mod twllm_probe.pack;", "  vfs_log_level 1;  ", ""]
    updated = edit_startup_lines(lines, "test1")
    assert updated[:-1] == lines
    assert edit_startup_lines(updated, None) == lines


def test_setting_a_battle_twice_leaves_one_startup_line() -> None:
    once = edit_startup_lines(_OTHER, "test1")
    twice = edit_startup_lines(once, "test1")
    assert twice == [*_OTHER, _LINE]
    assert edit_startup_lines(twice, "lodi") == [
        *_OTHER,
        "game_startup_mode battle data/twllm_battles/lodi/lodi.xml;",
    ]


@pytest.mark.parametrize("name", ["", "../test1", "test-1", "test 1", "a/b"])
def test_name_must_be_a_plain_token(name: str) -> None:
    with pytest.raises(ValueError):
        edit_startup_lines(_OTHER, name)
