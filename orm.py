from sqlalchemy import Column, ForeignKey, Integer, String
from sqlalchemy.orm import mapper, relationship
from sqlalchemy import MetaData, Table


import model

metadata = MetaData()

order_lines = Table(
	"order_lines",
	metadata,
	Column("id", Integer, primary_key=True, autoincrement=True),
	Column("sku", String(255)),
	Column("qty", Integer(255), nullable=False),
	Column("orderid", String(255)),

)


def start_mappers():
	lines_mapper = mapper(model.OrderLine, order_lines)
	# mapper(model.Batch, order_lines, properties={
	# 	"allocations": relationship(model.OrderLine, back_populates="batch")
	# })
