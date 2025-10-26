#Dataclass file for holding configuration of items

from dataclasses import dataclass
from typing import Optional

@dataclass
class Items:
    id: Optional[int]
    sku: str
    name: str
    quantity: int
    min_quantity: int = 0
    unit_cost: float = 0.0
    price: float = 0.0
    barcode: Optional[str] = None
    active: int = 1  # 1 for active, 0 for inactive

@dataclass
class StockTransaction:
    id: Optional[int]
    item_id: int
    delta: int # positive for stock in, negative for stock out
    reason: str = "" # reason for stock change
    reference: Optional[str] = None # optional reference i.e. PO# or ticket

