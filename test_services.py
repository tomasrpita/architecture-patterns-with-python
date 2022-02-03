import pytest
import repository
import model

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
    line = model.OrderLine("order-1", "sku-1", 10)
    batch = model.Batch("batch-1", "sku-1", 10, "2011-01-01")
    repo = FakeRepository([batch])

    result = services.allocate(line, repo, FakeSession())
    assert result = "batch-1"


def test_error_for_invalid_sku():
    line = model.OrderLine("order-1", "sku-1", 10)
    batch = model.Batch("batch-1", "sku-2", 10, "2011-01-01")
    repo = FakeRepository([batch])

    with pytest.raises(services.invalidSku, match="Invalid sku NONEXITENTSKU"):
        services.allocate(line, repo, FakeSession())


def test_commit():
    line = model.OrderLine("order-1", "sku-1", 10)
    batch = model.Batch("batch-1", "sku-1", 100, "2011-01-01")
    repo = FakeRepository([batch])
    session = FakeSession()

    services.allocate(line, repo, session)
    assert session.commited is True
    