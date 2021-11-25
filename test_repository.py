


def test_repository_can_save_a_batch(session):
    batch = model.Batch("batch1", "RUSTY-SOAPDISH", 100, eta=None)

    repo = repository.SqlAlchemyRepository(session)
    repo.add(batch)

    # We keep the .commit() outside of the repository and make it the 
    # responsibility of the caller. There are pros and cons for this; some of
    #  our reasons will become clearer when we get to [chapter_06_uow].
    session.commit()

    rows = session.execute( 
        'SELECT reference, sku, _purchased_quantity, eta FROM "batches"'
    )
    assert list(rows) == [("batch1", "RUSTY-SOAPDISH", 100, None)]



def insert_order_line(session):
    session.execute(  #(1)
        "INSERT INTO order_lines (orderid, sku, qty)"
        ' VALUES ("order1", "GENERIC-SOFA", 12)'
    )
    [[orderline_id]] = session.execute(
        "SELECT id FROM order_lines WHERE orderid=:orderid AND sku=:sku",
        dict(orderid="order1", sku="GENERIC-SOFA"),
    )
    return orderline_id


def insert_batch(session, batch_id):  #(2)
    session.execute(
        "INSERT INTO batches (reference, sku, quantity, eta)"
        ' VALUES (:reference, :sku, :quantity, :eta)',