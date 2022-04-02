"""
Its job is to handle requests from the outside world and to orchestrate an
operation. What we mean is that the service layer drives the application by
following a bunch of simple steps:
    * Get some data from the database
    * Update the domain model
    * Persist any changes
"""

from datetime import date
from typing import Optional

import src.allocation.adapters.email as email
import src.allocation.domain.model as model
import src.allocation.domain.events as events
import src.allocation.service_layer.unit_of_work as unit_of_work


class InvalidSku(Exception):
    pass


def is_valid_sku(sku, batches):
    return sku in {b.sku for b in batches}


# def add_batch(
#         batchref: str, sku: str, qty: int, eta: Optional[date],
#         uow: unit_of_work.AbstractUnitOfWork,
#     ) -> None:
#     with uow:
#         product = uow.products.get(sku)
#         if product is None:
#             product = model.Product(sku, batches=[])
#             uow.products.add(product)
#         product.batches.append(model.Batch(batchref, sku, qty, eta))
#         uow.commit()


# def allocate(
#         orderid: str, sku: str, qty: int,
#         uow: unit_of_work.AbstractUnitOfWork,
#     ) -> str:
#     line = model.OrderLine(orderid, sku, qty)
#     with uow:
#         product = uow.products.get(sku=line.sku)
#         if product is None:
#             raise InvalidSku(f"Invalid sku {sku}")
#         batchref = product.allocate(line)
#         uow.commit()
#         return batchref


def add_batch(
        event: events.BatchCreated,
        uow: unit_of_work.AbstractUnitOfWork,
    ) -> None:
    with uow:
        product = uow.products.get(sku=event.sku)
        if product is None:
            product = model.Product(event.sku, batches=[])
            uow.products.add(product)
        product.batches.append(
            model.Batch(event.batchref, event.sku, event.qty, event.eta)
            )
        uow.commit()


def allocate(
        event: events.AllocationRequired,
        uow: unit_of_work.AbstractUnitOfWork,
    ) -> str:
    line = model.OrderLine(event.orderid, event.sku,event.qty)
    with uow:
        product = uow.products.get(sku=line.sku)
        if product is None:
            raise InvalidSku(f"Invalid sku {event.sku}")
        batchref = product.allocate(line)
        uow.commit()
        return batchref


# TODO: make work
def send_out_stock_notification(
        event: events.OutOfStock,
        uow: unit_of_work.AbstractUnitOfWork,
    ) -> None:
   email.send(
       "stock@made.com",
       f"Out of stock for {event.sku}"
   )
