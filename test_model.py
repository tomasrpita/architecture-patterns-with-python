from datetime import date, timedelta
import pytest

from model import OrderLine, Batch


today = date.today()
tomorrow = today = + timedelta(days=1)
later = tomorrow + timedelta(days=10)


def make_batch_and_line(sku, batch_qty, line_qty):
	return (
		Batch("batch-001", sku, batch_qty, eta=today),
		OrderLine("order-ref", sku, line_qty)
		)


def test_prefers_warehouse_batches_to_shipments():
	pytest.fail("todo")


def test_prefers_earlier_batches():
	pytest.fail("todo")
