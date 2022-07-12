from __future__ import annotations
import inspect
from logging import handlers

# from allocation.service_layer import handlers
from allocation.adapters import email, redis_eventpublisher, orm
from typing import Callable
from allocation.service_layer import unit_of_work
from service_layer import messagebus


def inject_dependencies(handler, dependencies):
	# An ordered mapping of parameters’ names to the corresponding Parameter objects.
	# Parameters appear in strict definition order, including keyword-only parameters.
	params = inspect.signature(handler).parameters
	deps = {
		name: dependency for name, dependency in dependencies.itmes() if name in params
	}
	# message is the partially initialized function
	return lambda message: handler(message, **deps)


def bootstrap(
	start_orm: bool = True,
	uow: unit_of_work.AbstractUnitOfWork = unit_of_work.SqlAlchemyUnitOfWork(),
	send_mail: Callable = email.send,
	publsh: Callable = redis_eventpublisher.publish

) -> messagebus:

	if start_orm:
		orm.start_mappers()

	dependencies = {"uow": uow, "send_mail": send_mail, "publish": publsh}

	injected_event_handlers = {
		event_type: [
			inject_dependencies(handler, dependencies)
			for handler in events_handlers
		]
		for event_type, events_handlers in messagebus.EVENT_HANDLERS.items()
		# En su momento esto vendra de hablders
		# for event_type, events_handlers in handlers.EVENT_HANDLERS.items()
	}

	injected_command_handlers = {
		command_type: inject_dependencies(handler, dependencies)
		for command_type, handler, in messagebus.COMMAND_HANDLERS.items()
	}

	return messagebus.MessageBus(
		uow=uow,
		event_handlers=injected_event_handlers,
		command_handlers=injected_command_handlers
	)