import abc
import src.allocation.domain.model as model


# Aggregates are your entrypoints into the domain model
class AbstractRepository(abc.ABC):
        def __init__(self):
            self.seen = set() # type: Set[model.Product]


        def add(self, product: model.Product):
            self._add(product)
            self.seen.add(product)

        def get(self, sku: str) -> model.Product:
            product = self._get(sku)
            if product:
                self.seen.add(product)
            return product

        @abc.abstractmethod
        def _add(self, product: model.Product):
            raise NotImplementedError

        @abc.abstractmethod
        def _get(self, sku: str) -> model.Product:
            raise NotImplementedError


class SqlAlchemyRepository(AbstractRepository):
    def __init__(self, session):
        super().__init__()
        self._session = session

    def _add(self, product: model.Product):
        self._session.add(product)

    def _get(self, sku) -> model.Product:
        return self._session.query(model.Product).filter_by(sku=sku).one_or_none()
