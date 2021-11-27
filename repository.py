import abc
import model


class AbstractRepository(abc.ABC):

    @abc.abstractmethod
    def add(self, bach: model.Bach):
        raise NotImplementedError

    @abc.abstractmethod
    def get(self, reference) -> model.Batch:
        raise NotImplementedError


class SqlAlchemyRepository(AbstractRepository):

    def __init__(self, session):
        self._session = session

    def add(self, bach: model.Bach):
        self._session.add(bach)

    def get(self, reference) -> model.Batch:
        return self._session.query(model.Batch).filter_by(
            reference=reference).one()

    def list(self) -> list:
        return self._session.query(model.Batch).all()

