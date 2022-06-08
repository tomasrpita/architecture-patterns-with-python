from sqlalchemy import Column
from sqlalchemy import Date
from sqlalchemy import ForeignKey
from sqlalchemy import Integer
from sqlalchemy import MetaData
from sqlalchemy import String
from sqlalchemy import Table
from sqlalchemy import event
from sqlalchemy.orm import mapper
from sqlalchemy.orm import relationship

from allocation.domain import model

metadata = MetaData()

order_lines = Table(
    "order_lines",
    metadata,
    Column("id", Integer, primary_key=True, autoincrement=True),
    Column("sku", String(255)),
    Column("qty", Integer, nullable=False),
    Column("orderid", String(255)),
)

batches = Table(
    "batches",
    metadata,
    Column("id", Integer, primary_key=True, autoincrement=True),
    Column("reference", String(255)),
    Column("sku", String(255), ForeignKey("products.sku")),
    Column("_purchased_quantity", Integer, nullable=False),
    Column("eta", Date, nullable=True),
)

allocations = Table(
    "allocations",
    metadata,
    Column("id", Integer, primary_key=True, autoincrement=True),
    Column("orderline_id", ForeignKey("order_lines.id")),
    Column("batch_id", ForeignKey("batches.id")),
)

products = Table(
    "products",
    metadata,
    Column("sku", String(255), primary_key=True),
    Column("version_number", Integer, nullable=False, server_default="0"),
)

allocations_view = Table(
    "allocations_view",
    metadata,
    Column("orderid", String(255)),
    Column("sku", String(255)),
    Column("batchref", String(255))
)


def start_mappers():
    # When we call the mapper function, SQLAlchemy does its magic to bind
    # our domain model classes to the various tables we’ve defined.
    lines_mapper = mapper(model.OrderLine, order_lines)
    batches_mapper = mapper(
        model.Batch,
        batches,
        properties={
            "_allocations": relationship(
                lines_mapper,
                secondary=allocations,
                collection_class=set,
            )
        },
    )
    mapper(
        model.Product, products, properties={"batches": relationship(batches_mapper)}
    )


# a little hack in the orm so that events work
# https://docs.sqlalchemy.org/en/14/orm/events.html#instance-events
@event.listens_for(model.Product, "load")
def receive_load(product, _):  # _ is the "context" argument
    product.events = []
