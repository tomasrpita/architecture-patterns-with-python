from dataclasses import dataclass
from typing import Optional, Set, List
from datetime import date


class OutOfStock(Exception):
    """
    Exception raised when a product is out of stock.
    """
    pass

# @dataclass(frozen=True)
@dataclass(unsafe_hash=True)
class OrderLine:
    orderid: str
    sku: str
    qty: int


class Batch:
    def __init__(self, ref: str, sku: str, qty: int, eta: Optional[date]):
        self.reference = ref
        self.sku = sku
        self.eta = eta
        self._purchased_quantity = qty
        self._allocations = set() # Set[OrderLine] <= Error, why?


    def __eq__(self, other):
        if not isinstance(other, Batch):
            return False
        return self.reference == other.reference

    # An object is hashable if it has a hash value which never changes during its lifetime
    def __hash__(self):
        return hash(self.reference)


    # to use for sorting - sorted(List[Batch])
    def __gt__(self, other):
        if self.eta is None:
            return False
        if other.eta is None:
            return True
        return self.eta > other.eta

    @property
    def allocated_quantity(self) -> int:
        return sum(line.qty for line in self._allocations)

    @property
    def available_quantity(self) -> int:
        return self._purchased_quantity - self.allocated_quantity


    def allocate(self, line: OrderLine):
        if self.can_allocate(line):
            self._allocations.add(line)

    def deallocate(self, line: OrderLine):
        if line in self._allocations:
            self._allocations.remove(line)


    def can_allocate(self, line: OrderLine) -> bool:
        return self.available_quantity >= line.qty\
            and self.sku == line.sku


class Product:
    def __init__(self, sku: str, batches: List[Batch],
        version_number: int = 0
    ) -> None:
        self.sku = sku
        self.batches = set(batches)
        self.version_number = version_number

    def allocate(self, line: OrderLine) -> str:
        try:
            batch = next(b for b in sorted(list(self.batches)) if b.can_allocate(line))
            batch.allocate(line)
            self.version_number += 1
            return batch.reference
        except StopIteration:
            raise OutOfStock(f"Out of stock for sku {line.sku}")

