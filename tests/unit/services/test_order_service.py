from tw_general.models.order import MoveOrder, ReleaseOrder
from tw_general.services.order_service import OrderService


class _Repository:
    def __init__(self) -> None:
        self.orders: list[MoveOrder | ReleaseOrder] = []

    def write(self, order: MoveOrder | ReleaseOrder) -> None:
        self.orders.append(order)


def test_seq_comes_from_the_clock() -> None:
    repository = _Repository()
    service = OrderService(repository, clock=lambda: 1730400000000)
    order = service.send_move(1, 536.0, 363.0, True)
    assert order.seq == 1730400000000
    assert repository.orders == [order]


def test_same_clock_gives_increasing_seqs() -> None:
    service = OrderService(_Repository(), clock=lambda: 1000)
    first = service.send_move(1, 1.0, 2.0, True)
    second = service.send_move(1, 3.0, 4.0, False)
    assert first.seq == 1000
    assert second.seq == 1001


def test_repository_receives_the_arguments() -> None:
    repository = _Repository()
    service = OrderService(repository, clock=lambda: 50)
    service.send_move(2, -10.5, 4.0, False)
    assert repository.orders == [MoveOrder(seq=50, unit=2, x=-10.5, z=4.0, run=False)]


def test_send_release_gives_an_increasing_seq() -> None:
    repository = _Repository()
    service = OrderService(repository, clock=lambda: 1000)
    move = service.send_move(1, 1.0, 2.0, True)
    first = service.send_release(1)
    second = service.send_release(2)
    assert move.seq == 1000
    assert first.seq == 1001
    assert second.seq == 1002
    assert repository.orders == [
        move,
        ReleaseOrder(seq=1001, unit=1),
        ReleaseOrder(seq=1002, unit=2),
    ]
