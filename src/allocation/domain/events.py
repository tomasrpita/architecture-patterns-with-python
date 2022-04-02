from dataclasses import dataclass
from typing import Optional
from datetime import date

class Event:
	pass

@dataclass
class OutOfStock(Event):
	sku: str

@dataclass
class BatchCreated(Event):
	batchref: str
	sku: str
	qty: int
	eta: Optional[date] = None

@dataclass
class AllocationRequired(Event):
	orderid: str
	sku: str
	qty: int
