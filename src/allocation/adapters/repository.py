import abc
import src.allocation.domain.model as model


class AbstractProductRepository(abc.ABC):

        @abc.abstractclassmethod
        def add(self, product):
            raise NotImplementedError

        @abc.abstractclassmethod
        def get(self, sku):
            raise NotImplementedError

        # @abc.abstractmethod
        # def list(self) -> list:
        #   raise NotImplementedError


class SqlAlchemyRepository(AbstractProductRepository):

    def __init__(self, session):
        self._session = session

    def add(self, product: model.Product):
        # is there a table for products?
        self._session.add(product)

    def get(self, sku) -> model.Product:
        # return self.session.query(model.Batch).filter_by(reference=reference).one()
        return self._session.query(model.Product).filter_by(sku=sku).one_or_none()
        # batches = self._session.query(model.Batch).filter_by(
        #     sku=sku).all()
        # if batches:
        #     return model.Product(sku, batches)
        # return None


    # def list(self) -> list:
    #     return self._session.query(model.Batch).all()
