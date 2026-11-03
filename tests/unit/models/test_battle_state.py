import pytest
from pydantic import ValidationError

from tw_general.models.battle_state import BattleState


def test_last_seq_stays_text() -> None:
    state = BattleState(tick=20, last_seq="1793570263771", units=[])
    assert state.last_seq == "1793570263771"
    assert isinstance(state.last_seq, str)
    assert len(state.last_seq) == 13
    with pytest.raises(ValidationError):
        state.tick = 21


def test_last_seq_may_be_missing() -> None:
    state = BattleState(tick=1, units=[])
    assert state.last_seq is None


@pytest.mark.parametrize("bad", [1793570263771, 1793570263771.0])
def test_last_seq_rejects_numbers(bad: object) -> None:
    with pytest.raises(ValidationError):
        BattleState.model_validate({"tick": 1, "last_seq": bad, "units": []})
