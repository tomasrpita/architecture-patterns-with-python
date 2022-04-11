from datetime import date
from unittest import mock

import pytest

import src.allocation.adapters.repository as repository
import src.allocation.domain.events as events
import src.allocation.domain.model as model
import src.allocation.service_layer.messagebus as messagebus
import src.allocation.service_layer.unit_of_work as unit_of_work
from src.allocation.service_layer import handlers


class FakeRepository(repository.AbstractRepository):
    def __init__(self, products):
        super().__init__()
        self._products = set(products)

    def _add(self, product: model.Product):
        self._products.add(product)

    def _get(self, sku) -> model.Product:
        return next((p for p in self._products if p.sku == sku), None)

    def _get_by_batchref(self, batchref: str) -> model.Product:
        return next(
            (p for p in self._products for b in p.batches if b.reference == batchref),
            None,
        )


class FakeUnitOfWork(unit_of_work.AbstractUnitOfWork):
    def __init__(self):
        self.products = FakeRepository([])
        self.committed = False

    def _commit(self):
        self.committed = True

    def rollback(self):
        pass


# Optionally: Unit Testing Event Handlers in Isolation with a Fake Message Bus
# which is unnecessarily complicated and violates the SRP.
# If we change the message bus to being a class,[3] then building
# a FakeMessageBus is more straightforward:
class FakeUnitOfWorkWithFakeMessageBus(FakeUnitOfWork):
    def __init__(self):
        super().__init__()
        self.events_published = []  # type: list[events.Event]

    # I send an empty list, because for these tests I don't care if the events
    # are executed, only if the right ones are called with the right parameters.
    def collect_new_events(self):
        for product in self.products.seen:
            while product.events:
                self.events_published.append(product.events.pop(0))
        return []


class TestAddBatch:
    def test_for_new_product(self):
        uow = FakeUnitOfWork()

        messagebus.handle(events.BatchCreated("b1", "CRUNCHY-ARMCHAIR", 100, None), uow)

        assert uow.products.get("CRUNCHY-ARMCHAIR") is not None
        assert uow.committed

    def test_for_existing_product(self):
        uow = FakeUnitOfWork()

        messagebus.handle(events.BatchCreated("b1", "CRUNCHY-ARMCHAIR", 100, None), uow)
        messagebus.handle(events.BatchCreated("b2", "CRUNCHY-ARMCHAIR", 100, None), uow)

        assert "b2" in [
            b.reference for b in uow.products.get("CRUNCHY-ARMCHAIR").batches
        ]


class TestAllocate:
    def test_returns_allocation(self):
        uow = FakeUnitOfWork()
        # handlers.add_batch("batch1", "COMPLICATED-LAMP", 100, None, uow)
        messagebus.handle(
            events.BatchCreated("batch1", "COMPLICATED-LAMP", 100, None), uow
        )

        # result = handlers.allocate("ord-1", "COMPLICATED-LAMP", 10, uow)
        results = messagebus.handle(
            events.AllocationRequired("o1", "COMPLICATED-LAMP", 10), uow
        )
        assert "batch1" == results.pop(0)

    def test_allocate_errors_for_invalid_sku(self):
        uow = FakeUnitOfWork()

        messagebus.handle(
            events.BatchCreated("batch-1", "sku-0", 100, "2011-01-01"), uow
        )

        with pytest.raises(handlers.InvalidSku, match="Invalid sku sku-1"):
            messagebus.handle(events.AllocationRequired("order-1", "sku-1", 10), uow)

    def test_commits(self):
        uow = FakeUnitOfWork()

        messagebus.handle(
            events.BatchCreated("batch-1", "sku-1", 100, "2011-01-01"), uow
        )
        messagebus.handle(events.AllocationRequired("order-1", "sku-1", 10), uow)

        assert uow.committed is True


class TestChangeBatchQuantity:
    def test_changes_available_quantity(self):
        uow = FakeUnitOfWork()
        messagebus.handle(
            events.BatchCreated("batch1", "ADORABLE-SETTEE", 100, None), uow
        )
        [batch] = uow.products.get(sku="ADORABLE-SETTEE").batches
        assert batch.available_quantity == 100

        messagebus.handle(events.BatchQuantityChanged("batch1", 50), uow)

        assert batch.available_quantity == 50

    def test_reallocates_if_necessary(self):
        uow = FakeUnitOfWork()
        event_history = [
            events.BatchCreated("batch1", "INDIFFERENT-TABLE", 50, None),
            events.BatchCreated("batch2", "INDIFFERENT-TABLE", 50, date.today()),
            events.AllocationRequired("order1", "INDIFFERENT-TABLE", 20),
            events.AllocationRequired("order2", "INDIFFERENT-TABLE", 20),
        ]
        for e in event_history:
            messagebus.handle(e, uow)
        [batch1, batch2] = uow.products.get(sku="INDIFFERENT-TABLE").batches
        assert batch1.available_quantity == 10
        assert batch2.available_quantity == 50

        messagebus.handle(events.BatchQuantityChanged("batch1", 25), uow)

        # order1 or order2 will be deallocated, so we'll have 25 - 20
        assert batch1.available_quantity == 5
        # and 20 will be reallocated to the next batch
        assert batch2.available_quantity == 30

    # @pytest.mark.skip(reason="Don't work")
    def test_sends_email_on_out_of_stock_error(self):
        uow = FakeUnitOfWork()

        messagebus.handle(
            events.BatchCreated("batch-1", "POPULAR-CURTAINS", 9, "2011-01-01"), uow
        )

        with mock.patch("src.allocation.adapters.email.send") as mock_send_mail:
            messagebus.handle(
                events.AllocationRequired("o1", "POPULAR-CURTAINS", 10), uow
            )
            assert mock_send_mail.call_args == mock.call(
                "stock@made.com",
                f"Out of stock for POPULAR-CURTAINS",
            )


# Optionally: Unit Testing Event Handlers in Isolation with a Fake Message Bus
def test_reallocates_if_necessary_isolated():
    uow = FakeUnitOfWorkWithFakeMessageBus()

    # test setup as before
    event_history = [
        events.BatchCreated("batch1", "INDIFFERENT-TABLE", 50, None),
        events.BatchCreated("batch2", "INDIFFERENT-TABLE", 50, date.today()),
        events.AllocationRequired("order1", "INDIFFERENT-TABLE", 20),
        events.AllocationRequired("order2", "INDIFFERENT-TABLE", 20),
    ]
    for e in event_history:
        messagebus.handle(e, uow)
    [batch1, batch2] = uow.products.get(sku="INDIFFERENT-TABLE").batches

    assert batch1.available_quantity == 10
    assert batch2.available_quantity == 50

    messagebus.handle(events.BatchQuantityChanged("batch1", 25), uow)

    # assert on new events emitted rather than downstream side-effects
    [reallocation_event] = uow.events_published
    assert isinstance(reallocation_event, events.AllocationRequired)
    assert reallocation_event.orderid in {"order1", "order2"}
    assert reallocation_event.sku == "INDIFFERENT-TABLE"
