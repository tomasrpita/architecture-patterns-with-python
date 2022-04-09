import abc
from typing import Set
import src.allocation.domain.model as model
import src.allocation.adapters.orm as orm


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

        def get_by_batchref(self, batchref: str) -> model.Product:
            product = self._get_by_batchref(batchref)
            if product:
                self.seen.add(product)
            return product

        @abc.abstractmethod
        def _get_by_batchref(self, batchref: str) -> model.Product:
            raise NotImplementedError

        @abc.abstractmethod
        def _add(self, product: model.Product):
            raise NotImplementedError

        @abc.abstractmethod
        def _get(self, sku: str) -> model.Product:
            raise NotImplementedError


class SqlAlchemyRepository(AbstractRepository):
    def __init__(self, session):
        super().__init__()
        self.session = session

    def _add(self, product: model.Product):
        self.session.add(product)

    def _get(self, sku) -> model.Product:
        return self.session.query(model.Product).filter_by(sku=sku).one_or_none()

    def _get_by_batchref(self, batchref: str) -> model.Product:
        # batch = self.session.query(model.Batch).filter_by(
        #     reference=batchref
        #     ).one_or_none()
        # if not batch:
        #     return None
        # return self._get(batch.sku)
        return (
            self.session.query(model.Product)
            .join(model.Batch)
            .filter(orm.batches.c.reference == batchref)
            .first()
        )

