from allocation.service_layer import unit_of_work

def allocations(oderid: str, uow: unit_of_work.SqlAlchemyUnitOfWork) -> str:
	with uow:
		results = uow.session.execute(
			"""
			SELECT ol.sku, b.reference
			FROM allocations as a
			JOIN batches as b on a.batch_id = b.id
			JOIN orderlines as ol on a.orderline_id = ol.id
			WHERE a.order_id = :orderid
			""",
			{"orderid": oderid},
		)
	return [{"sku": sku, "batchref": batchref} for  sku, batchref in results]
