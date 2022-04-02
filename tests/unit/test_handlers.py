import pytest
import src.allocation.adapters.repository as repository
import src.allocation.domain.model as model
import src.allocation.domain.events as events
# import allocation.service_layer.handlers as handlers
import src.allocation.service_layer.unit_of_work as unit_of_work
import src.allocation.service_layer.messagebus as messagebus

class FakeRepository(repository.AbstractRepository):
    def __init__(self, products):
        super().__init__()
        self._products = set(products)

    def _add(self, product: model.Product):
        self._products.add(product)

    def _get(self, sku) -> model.Product:
        return next((p for p in self._products if p.sku == sku), None)


class FakeUnitOfWork(unit_of_work.AbstractUnitOfWork):
    def __init__(self):
        self.products = FakeRepository([])
        self.committed = False

    def _commit(self):
        self.committed = True

    def rollback(self):
        pass


class TestAddBatch:
    def test_add_batch_for_new_product(self):
        uow = FakeUnitOfWork()

        messagebus.handle(
            events.BatchCreated("b1", "CRUNCHY-ARMCHAIR", 100, None),
            uow
        )

        assert uow.products.get("CRUNCHY-ARMCHAIR") is not None
        assert uow.committed


# def test_add_batch_for_existing_product():
#     uow = FakeUnitOfWork()

#     handlers.add_batch("b1", "CRUNCHY-ARMCHAIR", 100, None, uow)
#     handlers.add_batch("b2", "CRUNCHY-ARMCHAIR", 99, None, uow)

#     assert "b2" in [b.reference for b in uow.products.get("CRUNCHY-ARMCHAIR").batches]


class TestAllocate:
    def test_returns_allocation(self):
        uow = FakeUnitOfWork()
        # handlers.add_batch("batch1", "COMPLICATED-LAMP", 100, None, uow)
        messagebus.handle(
            events.BatchCreated("batch1", "COMPLICATED-LAMP", 100, None),
            uow
        )

        # result = handlers.allocate("ord-1", "COMPLICATED-LAMP", 10, uow)
        result = messagebus.handle(
            events.AllocationRequired("o1", "COMPLICATED-LAMP", 10),
            uow
        )[0] # A Temporary Ugly Hack: The Message Bus Has to Return Results
        assert "batch1" == result


# def test_allocate_errors_for_invalid_sku():
#     uow = FakeUnitOfWork()
#     handlers.add_batch("batch-1", "sku-2", 100, "2011-01-01", uow)

#     with pytest.raises(handlers.InvalidSku, match="Invalid sku sku-1"):
#         handlers.allocate("order-1", "sku-1", 10, uow)


# def test_allocate_commits():
#     uow = FakeUnitOfWork()
#     handlers.add_batch("batch-1", "sku-1", 100, "2011-01-01", uow)
#     handlers.allocate("order-1", "sku-1", 10, uow)
#     assert uow.committed is True


# Why do we do this test? and using mock? and ussing unittest???
# from unittest import mock
# def test_sends_email_on_out_of_stock_error():
#     uow = FakeUnitOfWork()
#     handlers.add_batch("b1", "POPULAR-CURTAINS", 9, None, uow)
#     with mock.patch("src.allocation.adapters.email.send_mail") as mock_send_mail:
#         handlers.allocate("o1", "POPULAR-CURTAINS", 10, uow)
#         assert mock_send_mail.call_args == mock.call(
#             "stock@made.com",
#             f"Out of stock for POPULAR-CURTAINS",
#         )
