from flask import session
import pytest
import adapters.repository as repository
import domain.model as model
import service_layer.services as services 


class FakeSession:
    commited = False

    def commit(self):
        self.commited = True


class FakeRepository(repository.AbstractRepository):

    def __init__(self, batches):
        self._batches = set(batches)

    def add(self, batch: model.Batch):
        self._batches.add(batch)

    def get(self, reference) -> model.Batch:
        return next(b for b in self._batches if b.reference == reference)

    def list(self) -> list:
        return list(self._batches)


def test_returns_allocation():
    repo = FakeRepository([])
    session = FakeSession()
    services.add_batch("batch-1", "sku-1", 10, "2011-01-01", repo, session)
    
    result = services.allocate("order-1", "sku-1", 10, repo, session)
    
    assert result == "batch-1"


def test_error_for_invalid_sku():
    repo = FakeRepository([])
    session = FakeSession()
    
    services.add_batch("batch-1", "sku-2", 100, "2011-01-01", repo, session)

    with pytest.raises(services.InvalidSku, match="Invalid sku sku-1"):
        services.allocate("order-1", "sku-1", 10, repo, FakeSession())


def test_add_batch():
    repo, session = FakeRepository([]), FakeSession()
    services.add_batch("batch-1", "sku-1", 100, "2011-01-01", repo, session)

    assert repo.get("batch-1") is not None
    assert session.commited is True


def test_commit():

    repo = FakeRepository([])
    session = FakeSession()
    session2 = FakeSession()
    
    services.add_batch("batch-1", "sku-1", 100, "2011-01-01", repo, session)
    services.allocate("order-1", "sku-1", 10, repo, session2)
    
    assert session.commited is True
    assert session2.commited is True
