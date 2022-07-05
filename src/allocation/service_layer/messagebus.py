import imp
import logging
from __future__ import annotations
from typing import Callable
from typing import Dict
from typing import List
from typing import Type
from typing import Union

from tenacity import RetryError
from tenacity import Retrying
from tenacity import stop_after_attempt
from tenacity import wait_exponential

from ..domain import commands
from ..domain import events
from . import handlers
from . import unit_of_work

logger = logging.getLogger(__name__)

Message = Union[commands.Command, events.Event]






class MessageBus():
    def __init__(self,
        uow: unit_of_work.AbstractUnitOfWork,
        event_handlers: Dict[Type[events.Events], List[Callable]],
        command_handlers: Dict[Type[commands.Command], Callable]
    ):
        self.uow = uow
        self.event_handlers = event_handlers
        self.command_handlers = command_handlers

    def handle(self, message: Message):
        self.queue = [message]

        while self.queue:
            message = self.queue.pop(0)
            if isinstance(message, events.Event):
                self.handle_event(message)
            elif isinstance(message, commands.Command):
                self.handle_command(message)
            else:
                raise Exception(f"{message} was not an Event or Command")

    def handle_event(self, event: events.Event):
        for handler in self.event_handlers[type(event)]:
            try:

                logger.debug(f"Handlig event {event} whith the handler {handler}")
                handler(event)
                self.queue.extend(self.uow.collect_new_events())
            except RetryError as retry_failure:
                logger.error(
                    logger.exception("Exception handling event %s", event)
                )
                continue

    def handle_command(self, command: commands.Command):
        logger.debug(f"Handlig command {command}")
        try:
            handler = self.command_handlers[type(command)]
            handler(command)
            self.queue.extend(self.uow.collect_new_events())
        except Exception:
            logger.exception(f"Exception handling command {command}")
            raise






# def handle(message: Message, uow: unit_of_work.AbstractUnitOfWork):
#     queue = [message]
#     while queue:
#         message = queue.pop(0)
#         if isinstance(message, events.Event):
#             handle_event(message, queue, uow)
#         elif isinstance(message, commands.Command):
#             handle_command(message, queue, uow)
#         else:
#             raise Exception(f"{message} was not an Event or Command")


# def handle_event(
#     event: events.Event, queue: List[Message], uow: unit_of_work.AbstractUnitOfWork
# ):
#     for handler in EVENT_HANDLERS[type(event)]:
#         try:
#             for attempt in Retrying(
#                 stop=stop_after_attempt(3), wait=wait_exponential()
#             ):
#                 with attempt:
#                     logger.debug(f"Handlig event {event} whith the handler {handler}")
#                     handler(event, uow=uow)
#                     queue.extend(uow.collect_new_events())
#         except RetryError as retry_failure:
#             logger.error(
#                 "Failed to handle event %s times, giving up!",
#                 retry_failure.last_attempt.attempt_number,
#             )
#             continue


# def handle_command(
#     command: commands.Command,
#     queue: List[Message],
#     uow: unit_of_work.AbstractUnitOfWork,
# ):
#     logger.debug(f"Handlig command {command}")
#     try:
#         handler = COMMAND_HANDLERS[type(command)]
#         handler(command, uow=uow)
#         queue.extend(uow.collect_new_events())
#     except Exception:
#         logger.exception(f"Exception handling command {command}")
#         raise


EVENT_HANDLERS = {
    events.Allocated: [
        handlers.publish_allocated_event,
        handlers.add_allocation_to_read_model,
    ],
    events.Deallocated: [
        handlers.remove_allocation_from_read_model,
        handlers.reallocate,
    ],
    events.OutOfStock: [handlers.send_out_of_stock_notification],
}  # type: Dict[Type[events.Event], List[Callable]]

COMMAND_HANDLERS = {
    commands.Allocate: handlers.allocate,
    commands.CreateBatch: handlers.add_batch,
    commands.ChangeBatchQuantity: handlers.change_batch_quantity,
}  # type: Dict[Type[commands.Command], Callable]

# Note that the message bus as implemented doesn’t give us concurrency because only
# one handler will run at a time. Our objective isn’t to support parallel threads
# but to separate tasks conceptually, and to keep each UoW as small as possible.
# This helps us to understand the codebase because the "recipe" for how to run
# each use case is written in a single place.
