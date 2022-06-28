from __future__ import annotations
from allocation.adapters import email, redis_eventpublisher
from typing import Callable
from allocation.service_layer import unit_of_work
from service_layer import messagebus

def bootstrap(
	start_orm: bool = True,
	uow: unit_of_work.AbstractUnitOfWork = unit_of_work.SqlAlchemyUnitOfWork,
	send_mail: Callable = email.send,
	publsh: Callable = redis_eventpublisher.publish

) -> messagebus:
	pass
