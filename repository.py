import abc
from typing import List
import model


class AbstractRepository(abc.ABC):

    @abc.abstractmethod
    def add(self, batch: model.Batch):
        raise NotImplementedError

    @abc.abstractmethod
    def get(self, reference) -> model.Batch:
        raise NotImplementedError

    # @abc.abstractmethod
    # def list(self) -> List[model.Batch]:
    #     raise NotImplementedError


class SqlRepository(AbstractRepository):

    def __init__(self, session):
        self._session = session

    def add(self, batch: model.Batch):
        self._session.execute(
            "INSERT INTO batches (reference, sku, _purchased_quantity, eta) VALUES"
            "(:reference, :sku, :_purchased_quantity, :eta)",
            batch.__dict__
            )

        if batch.allocated_quantity:
            batch_id = self._session.execute(
                "SELECT id"
                " FROM batches WHERE reference=:reference",
                dict(reference=batch.reference)
            ).fetchone()[0]

            for order_line in batch._allocations:
                orderline_id = self._session.execute(
                    "SELECT id"
                    " FROM order_lines WHERE orderid=:orderid",
                    dict(orderid=order_line.orderid)
                ).fetchone()[0]

                self._session.execute(
                "INSERT INTO allocations (orderline_id, batch_id) VALUES"
                "(:orderline_id, :batch_id)",
                dict(
                    orderline_id=orderline_id,
                    batch_id=batch_id
                )
            )

    def get(self, reference) -> model.Batch:
        row = self._session.execute(
            "SELECT *"
            " FROM batches WHERE reference=:reference",
            dict(reference=reference)
        )
        batch_id, reference, sku, _purchased_quantity, eta = row.fetchone()
        batch = model.Batch(reference, sku, _purchased_quantity, eta )
        rows = list(
            self._session.execute(
                "SELECT orderid, sku, qty"
                " FROM order_lines"
                " JOIN allocations ON allocations.orderline_id = order_lines.id"
                " WHERE allocations.batch_id=:batch_id",
                dict(batch_id=batch_id)),
        )
        for row in rows:
            batch.allocate(model.OrderLine(*row))

        return batch


    # def list(self) -> List[model.Batch]:

