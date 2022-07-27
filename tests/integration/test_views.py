from datetime import date
from allocation.service_layer import messagebus, unit_of_work
from allocation.domain import commands
from allocation import views

today = date.today()

def test_allocations_view(sqlite_bus):
    sqlite_bus.handle(commands.CreateBatch("sku1batch", "sku1", 50, None))  #(1)
    sqlite_bus.handle(commands.CreateBatch("sku2batch", "sku2", 50, today))
    sqlite_bus.handle(commands.Allocate("order1", "sku1", 20))
    sqlite_bus.handle(commands.Allocate("order1", "sku2", 20))
    # add a spurious batch and order to make sure we're getting the right ones
    sqlite_bus.handle(commands.CreateBatch("sku1batch-later", "sku1", 50, today))
    sqlite_bus.handle(commands.Allocate("otherorder", "sku1", 30))
    sqlite_bus.handle(commands.Allocate("otherorder", "sku2", 10))

    assert views.allocations("order1", sqlite_bus.uow) == [
        {"sku": "sku1", "batchref": "sku1batch"},
        {"sku": "sku2", "batchref": "sku2batch"},
    ]



# def test_allocations_view(session_factory):
#     uow = unit_of_work.SqlAlchemyUnitOfWork(session_factory)
#     messagebus.handle(commands.CreateBatch("sku1batch", "sku1", 50, None), uow)  #(1)
#     messagebus.handle(commands.CreateBatch("sku2batch", "sku2", 50, today), uow)
#     messagebus.handle(commands.Allocate("order1", "sku1", 20), uow)
#     messagebus.handle(commands.Allocate("order1", "sku2", 20), uow)
#     # add a spurious batch and order to make sure we're getting the right ones
#     messagebus.handle(commands.CreateBatch("sku1batch-later", "sku1", 50, today), uow)
#     messagebus.handle(commands.Allocate("otherorder", "sku1", 30), uow)
#     messagebus.handle(commands.Allocate("otherorder", "sku2", 10), uow)

#     assert views.allocations("order1", uow) == [
#         {"sku": "sku1", "batchref": "sku1batch"},
#         {"sku": "sku2", "batchref": "sku2batch"},
#     ]

def test_deallocation(sqlite_bus):
    sqlite_bus.handle(commands.CreateBatch("b1", "sku1", 50, None))
    sqlite_bus.handle(commands.CreateBatch("b2", "sku1", 50, today))
    sqlite_bus.handle(commands.Allocate("o1", "sku1", 40))
    sqlite_bus.handle(commands.ChangeBatchQuantity("b1", 10))

    assert views.allocations("o1", sqlite_bus.uow) == [
        {"sku": "sku1", "batchref": "b2"},
    ]
