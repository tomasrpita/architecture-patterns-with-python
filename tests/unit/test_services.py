import pytest
import src.allocation.adapters.repository as repository
import src.allocation.domain.model as model
import src.allocation.service_layer.services as services
import src.allocation.service_layer.unit_of_work as unit_of_work



# class FakeRepository(repository.AbstractRepository):

#     def __init__(self, batches):
#         self._batches = set(batches)

#     def add(self, batch: model.Batch):
#         self._batches.add(batch)

#     def get(self, reference) -> model.Batch:
#         return next(b for b in self._batches if b.reference == reference)

#     def list(self) -> list:
#         return list(self._batches)


class FakeRepository(repository.AbstractProductRepository):

    def __init__(self, products):

        self._products = set(products)


    def add(self, product: model.Product):
        self._products.add(product)
        

    def get(self, sku) -> model.Product:
        return next((p for p in self._products if p.sku == sku), None)

    # def list(self) -> list:
    #     return list(self.products)



class FakeUnitOfWork(unit_of_work.AbstractUnitOfWork):
    def __init__(self):
        self.products = FakeRepository([])
        self.committed = False

    def commit(self):
        self.committed = True

    def rollback(self):
        pass


def test_add_batch_for_new_product():
    uow = FakeUnitOfWork()

    services.add_batch("b1", "CRUNCHY-ARMCHAIR", 100, None, uow)
    
    assert uow.products.get("CRUNCHY-ARMCHAIR") is not None
    assert uow.committed


# def test_add_batch_for_existing_product():

# def test_allocate_returns_allocation():

# def test_allocate_errors_for_invalid_sku():

# def test_allocate_commits():



# def test_allocate_returns_allocation():
#     uow = FakeUnitOfWork()
#     services.add_batch("batch1", "COMPLICATED-LAMP", 100, None, uow)
#     result = services.allocate("o1", "COMPLICATED-LAMP", 10, uow)
#     assert result == "batch1"

# def test_allocate_error_for_invalid_sku():
#     uow = FakeUnitOfWork()
#     services.add_batch("batch-1", "sku-2", 100, "2011-01-01", uow)

#     with pytest.raises(services.InvalidSku, match="Invalid sku sku-1"):
#         services.allocate("order-1", "sku-1", 10, uow)

# def test_allocate_commits():
#     uow = FakeUnitOfWork()
#     services.add_batch("batch-1", "sku-1", 100, "2011-01-01", uow)
#     services.allocate("order-1", "sku-1", 10, uow)
#     assert uow.committed is True
