import abc
import src.allocation.domain.model as model


# Aggregates are your entrypoints into the domain model
class AbstractProductRepository(abc.ABC):
        @abc.abstractclassmethod
        def add(self, product):
            raise NotImplementedError

        @abc.abstractclassmethod
        def get(self, sku):
            raise NotImplementedError


class SqlAlchemyRepository(AbstractProductRepository):
    def __init__(self, session):
        self._session = session

    def add(self, product: model.Product):
        self._session.add(product)

    def get(self, sku) -> model.Product:
        return self._session.query(model.Product).filter_by(sku=sku).one_or_none()
