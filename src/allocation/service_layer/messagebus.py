from typing import List, Callable, Dict, Type
from ..domain import events
# from ..adapters import email
# import handlers
# import unit_of_work
from . import handlers
from . import unit_of_work


# def handle(event: events.Event):
# 	for handler in HANDLERS[type(event)]:

def handle(
	event: events.Event,
	uow: unit_of_work.AbstractUnitOfWork
):
	# A Temporary Ugly Hack: The Message Bus Has to Return Results
	results = []
	queue = [event]
	while queue:
		event = queue.pop(0)
		for handler in HANDLERS[type(event)]:
			# handler(event, uow=uow)
			results.append(handler(event, uow=uow))
			queue.extend(uow.collect_new_events())
	return results


# def send_out_stock_notification(event: events.OutOfStock):
# 	email.send_mail(
# 		"stock@made.com",
# 		f"Out of stock for {event.sku}"
# 	)


HANDLERS = {
	events.BatchCreated: [handlers.add_batch],
	events.BatchQuantityChanged: [handlers.change_batch_quantity],
	events.AllocationRequired: [handlers.allocate],
	events.OutOfStock: [handlers.send_out_stock_notification],
} # type: Dict[Type[events.Event], List[Callable[[events.Event], None]]]

# Note that the message bus as implemented doesn’t give us concurrency because only
# one handler will run at a time. Our objective isn’t to support parallel threads
# but to separate tasks conceptually, and to keep each UoW as small as possible.
# This helps us to understand the codebase because the "recipe" for how to run
# each use case is written in a single place.
