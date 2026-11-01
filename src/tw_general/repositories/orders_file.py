import os
import time
from pathlib import Path

from tw_general.models.order import MoveOrder, ReleaseOrder

_ATTEMPTS = 10
_RETRY_WAIT_S = 0.05


def _render(order: MoveOrder | ReleaseOrder) -> bytes:
    if isinstance(order, ReleaseOrder):
        lines = (
            f"seq={order.seq}",
            f"unit={order.unit}",
            "action=release",
            "end",
        )
    else:
        lines = (
            f"seq={order.seq}",
            f"unit={order.unit}",
            f"x={order.x}",
            f"z={order.z}",
            f"run={1 if order.run else 0}",
            "end",
        )
    return ("\n".join(lines) + "\n").encode("ascii")


class OrdersFileRepository:
    def __init__(self, path: Path) -> None:
        self._path = Path(path)

    def write(self, order: MoveOrder | ReleaseOrder) -> None:
        temporary = Path(str(self._path) + ".tmp")
        temporary.write_bytes(_render(order))
        for attempt in range(1, _ATTEMPTS + 1):
            try:
                os.replace(temporary, self._path)
                return
            except PermissionError:
                if attempt == _ATTEMPTS:
                    raise
                time.sleep(_RETRY_WAIT_S)
