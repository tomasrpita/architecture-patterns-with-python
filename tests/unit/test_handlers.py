# pylint: disable=no-self-use
from __future__ import annotations
from datetime import date
from unittest import mock
from collections import defaultdict
from typing import Dict, List

import pytest

from allocation.adapters import repository
from allocation.adapters import notifications
from allocation import bootstrap
from allocation.domain import commands
from allocation.domain import model
from allocation.service_layer import handlers
from allocation.service_layer import unit_of_work


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


class FakeNotifications(notifications.AbstractNotifications):
	def __init__(self) -> None:
		self.sent = defaultdict(list) # type: Dict[str, List[str]]

	def send(self, destination, message):
		self.sent[destination].append(message)


def bootstrap_test_app():
	return bootstrap.bootstrap(
		start_orm=False,
		uow=FakeUnitOfWork(),
		# send_mail=lambda *atgs: None,
		# notifications=FakeNotifications(), # Realmente este don lo utiliso no interesa
		notifications=lambda *atgs: None,
		publish=lambda *atgs: None
	)


class TestAddBatch:
	def test_for_new_product(self):
		bus = bootstrap_test_app()

		bus.handle(
			commands.CreateBatch("b1", "CRUNCHY-ARMCHAIR", 100, None)
		)

		assert bus.uow.products.get("CRUNCHY-ARMCHAIR") is not None
		assert bus.uow.committed

	def test_for_existing_product(self):
		bus = bootstrap_test_app()

		bus.handle(
			commands.CreateBatch("b1", "CRUNCHY-ARMCHAIR", 100, None)
		)
		bus.handle(
			commands.CreateBatch("b2", "CRUNCHY-ARMCHAIR", 100, None)
		)

		assert "b2" in [
			b.reference for b in bus.uow.products.get("CRUNCHY-ARMCHAIR").batches
		]


class TestAllocate:
	def test_allocates(self):
		bus = bootstrap_test_app()
		bus.handle(
			commands.CreateBatch("batch1", "COMPLICATED-LAMP", 100, None)
		)
		bus.handle(commands.Allocate("o1", "COMPLICATED-LAMP", 10))
		[batch] = bus.uow.products.get("COMPLICATED-LAMP").batches
		assert batch.available_quantity == 90

	def test_allocate_errors_for_invalid_sku(self):
		bus = bootstrap_test_app()

		bus.handle(
			commands.CreateBatch("batch-1", "sku-0", 100, "2011-01-01")
		)

		with pytest.raises(handlers.InvalidSku, match="Invalid sku sku-1"):
			bus.handle(commands.Allocate("order-1", "sku-1", 10))

	def test_commits(self):
		bus = bootstrap_test_app()

		bus.handle(
			commands.CreateBatch("batch-1", "sku-1", 100, "2011-01-01")
		)
		bus.handle(commands.Allocate("order-1", "sku-1", 10))

		assert bus.uow.committed is True

	# @pytest.mark.skip(reason="Don't work")
	def test_sends_email_on_out_of_stock_error(self):

		fake_notifs = FakeNotifications()
		bus = bootstrap.bootstrap(
			start_orm=False,
			uow=FakeUnitOfWork(),
			notifications=fake_notifs,
			publsh=lambda *args: None
		)

		# bus = bootstrap_test_app()

		bus.handle(
			commands.CreateBatch("batch-1", "POPULAR-CURTAINS", 9, "2011-01-01")
		)

		# with mock.patch("allocation.adapters.email.send") as mock_send_mail:
		# 	bus.handle(commands.Allocate("o1", "POPULAR-CURTAINS", 10))
		# 	assert mock_send_mail.call_args == mock.call(
		# 		"stock@made.com",
		# 		f"Out of stock for POPULAR-CURTAINS",
		# 	)
		bus.handle(commands.Allocate("o1", "POPULAR-CURTAINS", 10))
		assert fake_notifs.sent["stock@made.com"] == [f"Out of stock for POPULAR-CURTAINS"]


class TestChangeBatchQuantity:
	def test_changes_available_quantity(self):
		bus = bootstrap_test_app()
		bus.handle(
			commands.CreateBatch("batch1", "ADORABLE-SETTEE", 100, None)
		)
		[batch] = bus.uow.products.get(sku="ADORABLE-SETTEE").batches
		assert batch.available_quantity == 100

		bus.handle(commands.ChangeBatchQuantity("batch1", 50))

		assert batch.available_quantity == 50

	def test_reallocates_if_necessary(self):
		bus = bootstrap_test_app()
		history = [
			commands.CreateBatch("batch1", "INDIFFERENT-TABLE", 50, None),
			commands.CreateBatch("batch2", "INDIFFERENT-TABLE", 50, date.today()),
			commands.Allocate("order1", "INDIFFERENT-TABLE", 20),
			commands.Allocate("order2", "INDIFFERENT-TABLE", 20),
		]
		for msg in history:
			bus.handle(msg)
		[batch1, batch2] = bus.uow.products.get(sku="INDIFFERENT-TABLE").batches
		assert batch1.available_quantity == 10
		assert batch2.available_quantity == 50

		bus.handle(commands.ChangeBatchQuantity("batch1", 25))

		# order1 or order2 will be deallocated, so we'll have 25 - 20
		assert batch1.available_quantity == 5
		# and 20 will be reallocated to the next batch
		assert batch2.available_quantity == 30

# class TestAddBatch:
# 	def test_for_new_product(self):
# 		uow = FakeUnitOfWork()

# 		bus.handle(
# 			commands.CreateBatch("b1", "CRUNCHY-ARMCHAIR", 100, None)
# 		)

# 		assert uow.products.get("CRUNCHY-ARMCHAIR") is not None
# 		assert uow.committed

# 	def test_for_existing_product(self):
# 		uow = FakeUnitOfWork()

# 		bus.handle(
# 			commands.CreateBatch("b1", "CRUNCHY-ARMCHAIR", 100, None)
# 		)
# 		bus.handle(
# 			commands.CreateBatch("b2", "CRUNCHY-ARMCHAIR", 100, None)
# 		)

# 		assert "b2" in [
# 			b.reference for b in uow.products.get("CRUNCHY-ARMCHAIR").batches
# 		]


# class TestAllocate:
# 	def test_allocates(self):
# 		uow = FakeUnitOfWork()
# 		bus.handle(
# 			commands.CreateBatch("batch1", "COMPLICATED-LAMP", 100, None)
# 		)
# 		bus.handle(commands.Allocate("o1", "COMPLICATED-LAMP", 10))
# 		[batch] = uow.products.get("COMPLICATED-LAMP").batches
# 		assert batch.available_quantity == 90

# 	def test_allocate_errors_for_invalid_sku(self):
# 		uow = FakeUnitOfWork()

# 		bus.handle(
# 			commands.CreateBatch("batch-1", "sku-0", 100, "2011-01-01")
# 		)

# 		with pytest.raises(handlers.InvalidSku, match="Invalid sku sku-1"):
# 			bus.handle(commands.Allocate("order-1", "sku-1", 10))

# 	def test_commits(self):
# 		uow = FakeUnitOfWork()

# 		bus.handle(
# 			commands.CreateBatch("batch-1", "sku-1", 100, "2011-01-01")
# 		)
# 		bus.handle(commands.Allocate("order-1", "sku-1", 10))

# 		assert uow.committed is True

# 	# @pytest.mark.skip(reason="Don't work")
# 	def test_sends_email_on_out_of_stock_error(self):
# 		uow = FakeUnitOfWork()

# 		bus.handle(
# 			commands.CreateBatch("batch-1", "POPULAR-CURTAINS", 9, "2011-01-01")
# 		)

# 		with mock.patch("allocation.adapters.email.send") as mock_send_mail:
# 			bus.handle(commands.Allocate("o1", "POPULAR-CURTAINS", 10))
# 			assert mock_send_mail.call_args == mock.call(
# 				"stock@made.com",
# 				f"Out of stock for POPULAR-CURTAINS",
# 			)


# class TestChangeBatchQuantity:
# 	def test_changes_available_quantity(self):
# 		uow = FakeUnitOfWork()
# 		bus.handle(
# 			commands.CreateBatch("batch1", "ADORABLE-SETTEE", 100, None)
# 		)
# 		[batch] = uow.products.get(sku="ADORABLE-SETTEE").batches
# 		assert batch.available_quantity == 100

# 		bus.handle(commands.ChangeBatchQuantity("batch1", 50))

# 		assert batch.available_quantity == 50

# 	def test_reallocates_if_necessary(self):
# 		uow = FakeUnitOfWork()
# 		history = [
# 			commands.CreateBatch("batch1", "INDIFFERENT-TABLE", 50, None),
# 			commands.CreateBatch("batch2", "INDIFFERENT-TABLE", 50, date.today()),
# 			commands.Allocate("order1", "INDIFFERENT-TABLE", 20),
# 			commands.Allocate("order2", "INDIFFERENT-TABLE", 20),
# 		]
# 		for msg in history:
# 			bus.handle(msg)
# 		[batch1, batch2] = uow.products.get(sku="INDIFFERENT-TABLE").batches
# 		assert batch1.available_quantity == 10
# 		assert batch2.available_quantity == 50

# 		bus.handle(commands.ChangeBatchQuantity("batch1", 25))

# 		# order1 or order2 will be deallocated, so we'll have 25 - 20
# 		assert batch1.available_quantity == 5
# 		# and 20 will be reallocated to the next batch
# 		assert batch2.available_quantity == 30


