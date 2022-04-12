from typing import Callable, Dict, List, Type, Union


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



HANDLERS = {
    events.BatchCreated: [handlers.add_batch],
    events.BatchQuantityChanged: [handlers.change_batch_quantity],
    events.AllocationRequired: [handlers.allocate],
    events.OutOfStock: [handlers.send_out_stock_notification],
}  #  type: Dict[Type[events.Event], List[Callable]]

# Note that the message bus as implemented doesn’t give us concurrency because only
# one handler will run at a time. Our objective isn’t to support parallel threads
# but to separate tasks conceptually, and to keep each UoW as small as possible.
# This helps us to understand the codebase because the "recipe" for how to run
# each use case is written in a single place.
