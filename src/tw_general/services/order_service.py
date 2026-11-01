import time
from collections.abc import Callable

from tw_general.models.order import MoveOrder, ReleaseOrder
from tw_general.repositories.orders_file import OrdersFileRepository


def _now_ms() -> int:
    return time.time_ns() // 1_000_000


class OrderService:
    def __init__(
        self,
        repository: OrdersFileRepository,
        clock: Callable[[], int] | None = None,
    ) -> None:
        self._repository = repository
        self._clock = _now_ms if clock is None else clock
        self._last_seq = 0

    def send_move(self, unit: int, x: float, z: float, run: bool) -> MoveOrder:
        seq = max(self._clock(), self._last_seq + 1)
        order = MoveOrder(seq=seq, unit=unit, x=x, z=z, run=run)
        self._repository.write(order)
        self._last_seq = seq
        return order

    def send_release(self, unit: int) -> ReleaseOrder:
        seq = max(self._clock(), self._last_seq + 1)
        order = ReleaseOrder(seq=seq, unit=unit)
        self._repository.write(order)
        self._last_seq = seq
        return order
