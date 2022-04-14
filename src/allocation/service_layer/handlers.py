"""
Its job is to handle requests from the outside world and to orchestrate an
operation. What we mean is that the service layer drives the application by
following a bunch of simple steps:
    * Get some data from the database
    * Update the domain model
    * Persist any changes
"""

from src.allocation.adapters import email
from src.allocation.domain import commands
from src.allocation.domain import events
from src.allocation.domain import model
from src.allocation.service_layer import unit_of_work


class InvalidSku(Exception):
    pass


class InvalidBatchref(Exception):
    pass


def add_batch(
    command: commands.CreateBatch,
    uow: unit_of_work.AbstractUnitOfWork,
) -> None:
    with uow:
        product = uow.products.get(sku=command.sku)
        if product is None:
            product = model.Product(command.sku, batches=[])
            uow.products.add(product)
        product.batches.append(
            model.Batch(command.ref, command.sku, command.qty, command.eta)
        )
        uow.commit()


def allocate(
    command: commands.Allocate,
    uow: unit_of_work.AbstractUnitOfWork,
) -> str:
    line = model.OrderLine(command.orderid, command.sku, command.qty)
    with uow:
        product = uow.products.get(sku=line.sku)
        if product is None:
            raise InvalidSku(f"Invalid sku {command.sku}")
        batchref = product.allocate(line)
        uow.commit()
        return batchref


def change_batch_quantity(
    command: commands.ChangeBatchQuantity, uow: unit_of_work.AbstractUnitOfWork
):
    with uow:
        product = uow.products.get_by_batchref(command.ref)
        if product is None:
            raise InvalidBatchref(f"Invalid batch reference {command.ref}")
        product.change_batch_quantity(ref=command.ref, qty=command.qty)
        uow.commit()


# pylint: disable=unused-argument
def send_out_stock_notification(
    event: events.OutOfStock,
    uow: unit_of_work.AbstractUnitOfWork,
) -> None:
    email.send("stock@made.com", f"Out of stock for {event.sku}")
