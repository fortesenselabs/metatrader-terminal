from dataclasses import dataclass
from enum import Enum
from typing import List, Optional


class SideType(Enum):
    BUY = "BUY"
    SELL = "SELL"

    @classmethod
    def export_all(cls) -> List[str]:
        return [order_type.value for order_type in cls]


class OrderType(Enum):
    MARKET = "MARKET"
    LIMIT = "LIMIT"
    STOP = "STOP"
    STOP_LIMIT = "STOP_LIMIT"

    @classmethod
    def export_all(cls) -> List[str]:
        return [order_type.value for order_type in cls]


class TimeInForceType(Enum):
    GTC = "GTC"  # Good Till Cancelled
    IOC = "IOC"  # Immediate Or Cancel
    FOK = "FOK"  # Fill Or Kill

    @classmethod
    def export_all(cls) -> List[str]:
        return [order_type.value for order_type in cls]


@dataclass
class CreateOrderRequest:
    symbol: str
    side: SideType
    type: Optional[OrderType] = OrderType.MARKET
    time_in_force: Optional[TimeInForceType] = TimeInForceType.GTC
    quantity: Optional[str] = "0.1"
    price: Optional[str] = "0"
    stop_loss_price: Optional[str] = "0"
    take_profit_price: Optional[str] = "0"


@dataclass
class CreateOrderResponse:
    order_id: int
    symbol: str
    status: str
    transact_time: int
    price: str
    orig_qty: str
    executed_qty: str
    time_in_force: str
    type: OrderType
    side: SideType
