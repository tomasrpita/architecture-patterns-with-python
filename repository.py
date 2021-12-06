import abc
import model


class AbstractRepository(abc.ABC):

    @abc.abstractmethod
    def add(self, batch: model.Batch):
        raise NotImplementedError

    @abc.abstractmethod
    def get(self, reference) -> model.Batch:
        raise NotImplementedError

    @abc.abstractmethod
    def list(self) -> list:
        raise NotImplementedError


class SqlAlchemyRepository(AbstractRepository):

    def __init__(self, session):
        self._session = session

    def add(self, batch: model.Batch):
        self._session.add(batch)

    def get(self, reference) -> model.Batch:
        return self._session.query(model.Batch).filter_by(
            reference=reference).one()

    def list(self) -> list:
        return self._session.query(model.Batch).all()


class FakeRepository(AbstractRepository):

    def __init__(self, batches):
        self._batches = set(batches)

    def add(self, batch: model.Batch):
        self._batches.add(batch)

    def get(self, reference) -> model.Batch:
        return next(b for b in self._batches if b.reference == reference)

    def list(self) -> list:
        return list(self._batches)
