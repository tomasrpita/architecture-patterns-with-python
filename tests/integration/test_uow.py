import src.allocation.domain.model as model
import src.allocation.service_layer.unit_of_work as unit_of_work
import pytest


def insert_batch(session, ref, sku, qty, eta):
    session.execute(
        "INSERT INTO products (sku) VALUES (:sku)",

        dict(sku=sku),
    )
    session.execute(
        "INSERT INTO batches (reference, sku, _purchased_quantity, eta)"
        " VALUES (:ref, :sku, :qty, :eta)",
        dict(ref=ref, sku=sku, qty=qty, eta=eta),
    )
    session.execute(
        "INSERT INTO products_batches (product_id, batch_id)"
        " SELECT id, id FROM products WHERE sku = :sku",
        dict(sku=sku),
    )


def get_allocated_batch_ref(session, orderid, sku):
    [[orderlineid]] = session.execute(
        "SELECT id FROM order_lines WHERE orderid=:orderid AND sku=:sku",
        dict(orderid=orderid, sku=sku),
    )
    [[batchref]] = session.execute(
        "SELECT b.reference FROM allocations JOIN batches AS b ON batch_id = b.id"
        " WHERE orderline_id=:orderlineid",
        dict(orderlineid=orderlineid),
    )
    return batchref


def test_uow_can_retrieve_a_batch_and_allocate_to_it(session_factory):
    session = session_factory()
    insert_batch(session, "batch1", "LITTLE-PRETTY-CHAIR", 100, None)
    session.commit()

    uow = unit_of_work.SqlAlchemyUnitOfWork(session_factory)
    with uow:
        product = uow.products.get(sku="LITTLE-PRETTY-CHAIR")
        line = model.OrderLine("o1", "LITTLE-PRETTY-CHAIR", 10)
        product.allocate(line)
        uow.commit()

    batchref = get_allocated_batch_ref(session, "o1", "LITTLE-PRETTY-CHAIR")
    assert batchref == "batch1"


def test_rolls_back_uncommitted_work_by_default(session_factory):
    uow = unit_of_work.SqlAlchemyUnitOfWork(session_factory)
    with uow:
        insert_batch(uow.session, "batch1", "MEDIUM-PLINTH", 100, None)

    new_session = session_factory()
    rows = list(new_session.execute('SELECT * FROM "batches"'))
    assert rows == []


def test_rolls_back_on_error(session_factory):
    class MyException(Exception):
        pass

    uow = unit_of_work.SqlAlchemyUnitOfWork(session_factory)
    with pytest.raises(MyException):
        with uow:
            insert_batch(uow.session, "batch1", "LARGE-FORK", 100, None)
            raise MyException()

    new_session = session_factory()
    rows = list(new_session.execute('SELECT * FROM "batches"'))
    assert rows == []


# # def try_to_allocate(orderid, sku, exceptions):

# @pytest.mark.skip("do this for an advanced challenge")
# def test_concurrent_updates_to_version_are_not_allowed(postgres_session_factory):
#     pass
