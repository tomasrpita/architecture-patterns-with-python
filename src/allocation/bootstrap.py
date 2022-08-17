from __future__ import annotations
import inspect

# from allocation.service_layer import handlers
from typing import Callable
from allocation.adapters import redis_eventpublisher, orm
from allocation.service_layer import handlers, unit_of_work, messagebus
from adapters.notifications import AbstractNotifications, EmailNotifications


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
    notifications: AbstractNotifications = EmailNotifications(),
    publsh: Callable = redis_eventpublisher.publish,
) -> messagebus.MessageBus:

    if start_orm:
        orm.start_mappers()

    dependencies = {"uow": uow, "notifications": notifications, "publish": publsh}

    injected_event_handlers = {
        event_type: [
            inject_dependencies(handler, dependencies) for handler in event_handlers
        ]
        for event_type, event_handlers in handlers.EVENT_HANDLERS.items()
    }

    injected_command_handlers = {
        command_type: inject_dependencies(handler, dependencies)
        for command_type, handler in handlers.COMMAND_HANDLERS.items()
    }

    return messagebus.MessageBus(
        uow=uow,
        event_handlers=injected_event_handlers,
        command_handlers=injected_command_handlers,
    )
