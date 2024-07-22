#
# Orders
#


from typing import Optional, List, Union
from enum import Enum
from pydantic import BaseModel, model_validator


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
    close_all: bool = True


class ModifyOrderRequest(BaseModel):
    order_id: str
    price: Optional[str] = "0"
    stop_loss_price: Optional[str] = "0"
    take_profit_price: Optional[str] = "0"


class OrderResponse(BaseModel):
    order_id: Optional[str] = None
    symbol: str
    status: Optional[str] = None
    time: Optional[int] = None
    price: Optional[str] = None
    orig_qty: Optional[str] = None
    executed_qty: Optional[str] = None
    stop_loss: Optional[str] = None
    take_profit: Optional[str] = None
    time_in_force: Optional[TimeInForceType] = TimeInForceType.GTC
    type: Optional[OrderType] = OrderType.MARKET
    side: Optional[SideType] = None

    @model_validator(mode="after")
    def adjust_tp_and_sl(self):
        self.stop_loss = (
            None
            if self.stop_loss is not None and self.stop_loss == 0
            else self.stop_loss
        )
        self.take_profit = (
            None
            if self.take_profit is not None and self.take_profit == 0
            else self.take_profit
        )

        return self


# for getting opened and closed orders
class MultiOrdersResponse(BaseModel):
    orders: Optional[List[OrderResponse]] = None
