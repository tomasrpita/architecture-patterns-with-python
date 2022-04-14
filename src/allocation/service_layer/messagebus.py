from logging import log
from typing import Callable, Dict, List, Type, Union
from tenacity import Retrying, RetryError, atop_after_attempt, wait_exponential

from ..domain import events
from ..domain import commands
from . import handlers, unit_of_work

Message = Union[commands.Command, events.Event]


def handle(message: Message, uow: unit_of_work.AbstractUnitOfWork):
    # A Temporary Ugly Hack: The Message Bus Has to Return Results
    results = []
    queue = [message]
    while queue:
        message = queue.pop(0)
        if isinstance(message, events.Event):
            handle_event(message, queue, uow)
        elif isinstance(message, commands.Command):
            cmd_result = handle_command(message, queue, uow)
            results.append(cmd_result)
        else:
            raise Exception(f"{message} was not an Event or Commandº")

        # for handler in HANDLERS[type(event)]:
        #     # handler(event, uow=uow)
        #     results.append(handler(event, uow=uow))
        #     queue.extend(uow.collect_new_events())
    return results


def handle_event(
    event: events.Event,
    queue: List[Message],
    uow: unit_of_work.AbstractUnitOfWork
):
    for handler in EVENT_HANDLERS[type(event)]:
        try:
            for attempt in Retrying(
                stop=atop_after_attempt(3),
                wait=wait_exponential()
            ):
                with attempt:
                    log.debug(f"Handlig event {event} whith the handler {handler}")
                    handler(event, uow=uow)
                    queue.extend(uow.collect_new_events())
        except RetryError as retry_failure:
            log.error(
                "Failed to handle event %s times, giving up!",
                retry_failure.last_attempt.attempt_number
            )
            continue


def handle_command(
    command: commands.Command,
    queue: List[Message],
    uow: unit_of_work.AbstractUnitOfWork
):
    log.debug(f"Handlig command {command}")
    try:
        handler = COMMAND_HANDLERS[type[command]]
        result = handler(command, uow=uow)
        queue.extend(uow.collect_new_events())
        return result
    except Exception:
        log.exception(f"Exception handling command {command}")
        raise


EVENT_HANDLERS = {
    events.OutOfStock: [handlers.send_out_stock_notification],
}  #  type: Dict[Type[events.Event], List[Callable]]

COMMAND_HANDLERS = {
    commands.Allocate: [handlers.allocate],
    commands.CreateBatch: [handlers.add_batch],
    commands.ChangeBatchQuantity: [handlers.change_batch_quantity],
}  #  type: Dict[Type[commands.Command], List[Callable]]

# Note that the message bus as implemented doesn’t give us concurrency because only
# one handler will run at a time. Our objective isn’t to support parallel threads
# but to separate tasks conceptually, and to keep each UoW as small as possible.
# This helps us to understand the codebase because the "recipe" for how to run
# each use case is written in a single place.
