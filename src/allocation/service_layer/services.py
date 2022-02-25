"""
Its job is to handle requests from the outside world and to orchestrate an
operation. What we mean is that the service layer drives the application by
following a bunch of simple steps:
    * Get some data from the database
    * Update the domain model
    * Persist any changes
"""

from datetime import date
from typing import ContextManager, Optional

import src.allocation.domain.model as model
# import src.allocation.service_layer.unit_of_work as unit_of_work
from src.allocation.service_layer.unit_of_work import AbstractUnitOfWork, uow_maker



class InvalidSku(Exception):
    pass


def is_valid_sku(sku, batches):
    return sku in {b.sku for b in batches}


def allocate(
        orderid: str, sku: str, qty: int,
        uow #: ContextManager[AbstractUnitOfWork],
    ) -> str:
    line = model.OrderLine(orderid, sku, qty)
    with uow() as uow:
        batches = uow.batches.list()
        if not is_valid_sku(sku, batches):
            raise InvalidSku(f"Invalid sku {sku}")
        batchref = model.allocate(line, batches)
        uow.commit()
    return batchref


def add_batch(
        batchref: str, sku: str, qty: int, eta: Optional[date],
        uow #: ContextManager[AbstractUnitOfWork],
    ) -> None:
    with uow() as uow:
        uow.batches.add(model.Batch(batchref, sku, qty, eta))
        uow.commit()
