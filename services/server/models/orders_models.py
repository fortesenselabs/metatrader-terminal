#
# Orders
#


from typing import Optional, List, Union
from enum import Enum
from pydantic import BaseModel


class SideType(Enum):
    BUY = "BUY"
    SELL = "SELL"

    @classmethod
    def from_string(cls, string) -> Union["SideType", None]:
        try:
            return cls[string]
        except KeyError:
            return None

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

    # @classmethod
    # def get_order_type(cls, order_type: MTOrderType) -> Optional["OrderType"]:
    #     mapping = {
    #         (SideType.BUY, OrderType.MARKET): cls.BUY,
    #         (SideType.SELL, OrderType.MARKET): cls.SELL,
    #         (SideType.BUY, OrderType.LIMIT): cls.BUY_LIMIT,
    #         (SideType.SELL, OrderType.LIMIT): cls.SELL_LIMIT,
    #         (SideType.BUY, OrderType.STOP): cls.BUY_STOP,
    #         (SideType.SELL, OrderType.STOP): cls.SELL_STOP,
    #     }
    #     return mapping.get(order_type)


# TODO: Add more
class TimeInForceType(Enum):
    GTC = "GTC"  # Good Till Cancelled
    IOC = "IOC"  # Immediate Or Cancel
    FOK = "FOK"  # Fill Or Kill

    @classmethod
    def export_all(cls) -> List[str]:
        return [order_type.value for order_type in cls]


class CreateOrderRequest(BaseModel):
    symbol: str
    side: SideType
    type: Optional[OrderType] = OrderType.MARKET
    time_in_force: Optional[TimeInForceType] = TimeInForceType.GTC
    quantity: Optional[str] = "0.1"
    price: Optional[str] = "0"
    stop_loss_price: Optional[str] = "0"
    take_profit_price: Optional[str] = "0"


class CancelOrderRequest(BaseModel):
    order_id: Optional[str] = None
    symbol: Optional[str] = None
    magic_id: Optional[int] = None
    quantity: Optional[str] = "0.1"
    close_all: bool = False


class OrderResponse(BaseModel):
    order_id: Optional[str] = None
    symbol: str
    status: Optional[str] = None
    transact_time: Optional[int] = None
    price: Optional[str] = None
    orig_qty: Optional[str] = None
    executed_qty: Optional[str] = None
    time_in_force: Optional[TimeInForceType] = TimeInForceType.GTC
    type: Optional[OrderType] = OrderType.MARKET
    side: Optional[SideType] = None


class OpenOrdersResponse(BaseModel):
    orders: Optional[List[OrderResponse]] = None
