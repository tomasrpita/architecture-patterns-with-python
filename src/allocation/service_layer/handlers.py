"""
Its job is to handle requests from the outside world and to orchestrate an
operation. What we mean is that the service layer drives the application by
following a bunch of simple steps:
    * Get some data from the database
    * Update the domain model
    * Persist any changes
"""

from dataclasses import asdict
from allocation.adapters import email
from allocation.adapters import redis_eventpublisher
from allocation.domain import commands
from allocation.domain import events
from allocation.domain import model
from allocation.service_layer import unit_of_work


class InvalidSku(Exception):
    pass


class InvalidBatchref(Exception):
    pass


def add_batch(
    cmd: commands.CreateBatch,
    uow: unit_of_work.AbstractUnitOfWork,
) -> None:
    with uow:
        product = uow.products.get(sku=cmd.sku)
        if product is None:
            product = model.Product(cmd.sku, batches=[])
            uow.products.add(product)
        product.batches.append(
            model.Batch(cmd.ref, cmd.sku, cmd.qty, cmd.eta)
        )
        uow.commit()


def allocate(
    cmd: commands.Allocate,
    uow: unit_of_work.AbstractUnitOfWork,
) -> str:
    line = model.OrderLine(cmd.orderid, cmd.sku, cmd.qty)
    with uow:
        product = uow.products.get(sku=line.sku)
        if product is None:
            raise InvalidSku(f"Invalid sku {cmd.sku}")
        product.allocate(line)
        uow.commit()


def reallocate(
    event: events.Deallocated,
    uow: unit_of_work.AbstractUnitOfWork,
):
    with uow:
        product = uow.products.get(sku=event.sku)
        product.events.append(commands.Allocate(**asdict(event)))
        uow.commit()


# def change_batch_quantity(
#     cmd: commands.ChangeBatchQuantity, uow: unit_of_work.AbstractUnitOfWork
# ):
#     with uow:
#         product = uow.products.get_by_batchref(cmd.ref)
#         if product is None:
#             raise InvalidBatchref(f"Invalid batch reference {cmd.ref}")
#         product.change_batch_quantity(ref=cmd.ref, qty=cmd.qty)
#         uow.commit()

def change_batch_quantity(
    cmd: commands.ChangeBatchQuantity,
    uow: unit_of_work.AbstractUnitOfWork,
):
    with uow:
        product = uow.products.get_by_batchref(batchref=cmd.ref)
        product.change_batch_quantity(ref=cmd.ref, qty=cmd.qty)
        uow.commit()


# pylint: disable=unused-argument
def send_out_stock_notification(
    event: events.OutOfStock,
    uow: unit_of_work.AbstractUnitOfWork,
) -> None:
    email.send("stock@made.com", f"Out of stock for {event.sku}")


def publish_allocated_event(
    event: events.Allocated,
    uow: unit_of_work,
):
    redis_eventpublisher.publish("line_allocated", event)


def add_allocation_to_read_model(
    event: events.Allocated,
    uow: unit_of_work.AbstractUnitOfWork,
):
    with uow:
        uow.session.execute(
            """
            INSERT INTO allocations_view (orderid, sku, batchref)
            VALUES (:orderid, :sku, :batchref)
            """,
            {"orderid": event.orderid, "sku": event.sku, "batchref": event.batchref},
        )
        uow.commit()


def remove_allocation_to_read_model(
    event: events.Deallocated,
    uow: unit_of_work.AbstractUnitOfWork,
):
    with uow:
        uow.session.execute(
            """
            DELETE FROM allocations_view
            WHERE orderid = :orderid AND sku = :sku AND batchref = :batchref
            """,
            {"orderid": event.orderid, "sku": event.sku, "batchref": event.batchref},
        )
        uow.commit()
