from typing import List, Callable, Dict, Type
from ..domain import events
from ..adapters import email


def handle(event: events.Event):
	for handler in HANDLERS[type(event)]:
		handler(event)


def send_out_stock_notification(event: events.OutOfStock):
	email.send_mail(
		"stock@made.com",
		f"Out of stock for {event.sku}"
	)


HANDLERS = {
	events.OutOfStock: [send_out_stock_notification]
} # type: Dict[Type[events.Event], List[Callable[[events.Event], None]]]

# Note that the message bus as implemented doesn’t give us concurrency because only
# one handler will run at a time. Our objective isn’t to support parallel threads
# but to separate tasks conceptually, and to keep each UoW as small as possible.
# This helps us to understand the codebase because the "recipe" for how to run
# each use case is written in a single place.
