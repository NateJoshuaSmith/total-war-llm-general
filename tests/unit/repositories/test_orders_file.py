import os
from pathlib import Path

import pytest

import tw_general.repositories.orders_file as orders_file
from tw_general.models.order import MoveOrder
from tw_general.repositories.orders_file import OrdersFileRepository

FIXTURE = Path(__file__).resolve().parents[2] / "fixtures" / "orders_example.txt"
EXAMPLE = MoveOrder(seq=1730400000000, unit=1, x=536.0, z=363.0, run=True)


def test_matches_fixture_bytes(tmp_path: Path) -> None:
    destination = tmp_path / "twllm_orders.txt"
    OrdersFileRepository(destination).write(EXAMPLE)
    assert destination.read_bytes() == FIXTURE.read_bytes()
    assert not Path(str(destination) + ".tmp").exists()


def test_second_write_replaces_the_first(tmp_path: Path) -> None:
    destination = tmp_path / "twllm_orders.txt"
    repository = OrdersFileRepository(destination)
    repository.write(EXAMPLE)
    repository.write(MoveOrder(seq=2, unit=3, x=-4.5, z=6.0, run=False))
    assert destination.read_bytes() == b"seq=2\nunit=3\nx=-4.5\nz=6.0\nrun=0\nend\n"
    assert not Path(str(destination) + ".tmp").exists()


def test_retries_permission_error_on_replace(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    destination = tmp_path / "twllm_orders.txt"
    real_replace = os.replace
    calls = {"n": 0}
    sleeps: list[float] = []

    def flaky(src: str, dst: str) -> None:
        calls["n"] += 1
        if calls["n"] == 1:
            raise PermissionError("locked")
        real_replace(src, dst)

    monkeypatch.setattr(orders_file.os, "replace", flaky)
    monkeypatch.setattr(orders_file.time, "sleep", sleeps.append)
    OrdersFileRepository(destination).write(EXAMPLE)

    assert calls["n"] == 2
    assert sleeps == [0.05]
    assert destination.read_bytes() == FIXTURE.read_bytes()
    assert not Path(str(destination) + ".tmp").exists()
