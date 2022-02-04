"""
Its job is to handle requests from the outside world and to orchestrate an 
operation. What we mean is that the service layer drives the application by
following a bunch of simple steps:
    * Get some data from the database
    * Update the domain model
    * Persist any changes
"""

from flask import session
import domain.model as model
import adapters.repository as repository


class InvalidSku(Exception):
    pass


def is_valid_sku(sku, batches):
    return sku in {b.sku for b in batches}


def allocate(
        line: model.OrderLine, 
        repo: repository.AbstractRepository, 
        session: session
    ) -> str:
    batches = repo.list()
    if not is_valid_sku(line.sku, batches):
        raise InvalidSku(f"Invalid sku {line.sku}")
    batchref = model.allocate(line, batches)
    # this  step is a little unsatisfactory at the moment, 
    # as our service layer is tightly coupled to our database layer
    session.commit()
    return batchref