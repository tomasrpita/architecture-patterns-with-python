from typing import List
from allocation.service_layer import unit_of_work

def allocations(oderid: str, uow: unit_of_work.SqlAlchemyUnitOfWork) -> List[dict]:
	with uow:
		# results = uow.session.execute(
		# 	"""
		# 	SELECT ol.sku, b.reference
		# 	FROM allocations as a
		# 	JOIN batches as b on a.batch_id = b.id
		# 	JOIN order_lines as ol on a.orderline_id = ol.id
		# 	WHERE ol.orderid = :orderid
		# 	""",
		# 	{"orderid": oderid},
		# )
		results = uow.session.execute(
			"""
			SELECT sku, batchref from allocations_view WHERE orderid = :orderid
			""",
			{"orderid": oderid},
		)
	return [{"sku": sku, "batchref": batchref} for  sku, batchref in results]
