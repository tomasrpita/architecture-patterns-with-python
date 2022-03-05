from sqlalchemy import Column, ForeignKey, Integer, String, Date
from sqlalchemy.orm import mapper, relationship
from sqlalchemy import MetaData, Table


import src.allocation.domain.model as model

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
    Column("sku", String(255)),
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
	Column("id", Integer, primary_key=True, autoincrement=True),
	Column("sku", String(255)),
	Column("version_number", Integer, nullable=False),
)


products_batches = Table(
	"products_batches",
	metadata,
	Column("id", Integer, primary_key=True, autoincrement=True),
	Column("product_id", ForeignKey("products.id")),
	Column("batch_id", ForeignKey("batches.id")),
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
				lines_mapper, secondary=allocations, collection_class=set,
			)
		},
	)
	products_mapper = mapper(model.Product, products, properties={
		"batches": relationship(
			batches_mapper, secondary=products_batches, collection_class=set,
		)
	})
