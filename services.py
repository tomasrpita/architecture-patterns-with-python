from flask import session
import model
import repository


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