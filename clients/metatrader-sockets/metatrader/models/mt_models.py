#
# MetaTraderDataProcessor Types
#
from typing import Optional, List, Tuple, Union
from enum import Enum
from pydantic import BaseModel, Field
from .orders_models import SideType, OrderType, TimeInForceType


class BarDataEvent(BaseModel):
    event: str = "on_bar_data"
    symbol: str
    time_frame: str
    time: str
    open: float = Field(..., alias="open_price")
    high: float
    low: float
    close: float = Field(..., alias="close_price")
    tick_volume: Optional[float] = None
    is_final: Optional[bool] = True

    class Config:
        populate_by_name = True


class TickDataEvent(BaseModel):
    event: str = "on_tick"
    symbol: str
    time: Optional[str] = None
    bid: Optional[float] = None
    ask: Optional[float] = None

    class Config:
        populate_by_name = True


class MTOrderType(Enum):
    BUY = "buy"
    SELL = "sell"
    BUY_LIMIT = "buylimit"
    SELL_LIMIT = "selllimit"
    BUY_STOP = "buystop"
    SELL_STOP = "sellstop"

    @classmethod
    def from_string(cls, string) -> Union["MTOrderType", None]:
        try:
            return cls[string]
        except KeyError:
            return None

    @classmethod
    def get_mt_order_type(
        cls, side_type: SideType, order_type: OrderType
    ) -> Optional["MTOrderType"]:
        mapping = {
            (SideType.BUY, OrderType.MARKET): cls.BUY,
            (SideType.SELL, OrderType.MARKET): cls.SELL,
            (SideType.BUY, OrderType.LIMIT): cls.BUY_LIMIT,
            (SideType.SELL, OrderType.LIMIT): cls.SELL_LIMIT,
            (SideType.BUY, OrderType.STOP): cls.BUY_STOP,
            (SideType.SELL, OrderType.STOP): cls.SELL_STOP,
        }
        return mapping.get((side_type, order_type))

    @classmethod
    def get_side_and_order_type(
        cls, mt_order_type: "MTOrderType"
    ) -> Optional[Tuple[SideType, OrderType]]:
        reverse_mapping = {
            cls.BUY: (SideType.BUY, OrderType.MARKET),
            cls.SELL: (SideType.SELL, OrderType.MARKET),
            cls.BUY_LIMIT: (SideType.BUY, OrderType.LIMIT),
            cls.SELL_LIMIT: (SideType.SELL, OrderType.LIMIT),
            cls.BUY_STOP: (SideType.BUY, OrderType.STOP),
            cls.SELL_STOP: (SideType.SELL, OrderType.STOP),
        }
        return reverse_mapping.get(mt_order_type)


class MTOrderStatus(Enum):
    NEW = "NEW"
    NONE = "NONE"
    PENDING = "PENDING"
    FILLED = "FILLED"
    CANCELED = "CANCELED"


class MTOrderEvent:
    def __init__(
        self,
        ticket_id: int,
        symbol: str,
        lots: float,
        price: float,
        order_type: MTOrderType,
        magic: int,
        status: MTOrderStatus = MTOrderStatus.NONE,
        time_in_force: TimeInForceType = TimeInForceType.GTC,
    ):
        self.ticket_id = ticket_id
        self.symbol = symbol
        self.lots = lots
        self.price = price
        self.type = order_type
        self.status = status
        self.magic = magic
        self.time_in_force = time_in_force


class NewOrderEvent:
    def __init__(
        self,
        ticket_id: int,
        magic: int,
        symbol: str,
        lots: float,
        type: MTOrderType,
        open_price: float,
        open_time: str,
        sl: float,
        tp: float,
        pnl: float,
        swap: float,
        comment: Optional[str] = "",
    ):
        self.ticket_id = ticket_id
        self.magic = magic
        self.symbol = symbol
        self.lots = lots
        self.type = type
        self.open_price = open_price
        self.open_time = open_time
        self.sl = sl
        self.tp = tp
        self.pnl = pnl
        self.swap = swap
        self.comment = comment

    def __repr__(self):
        return (
            f"NewOrderEvent(magic={self.magic}, symbol={self.symbol}, lots={self.lots}, "
            f"type={self.type}, open_price={self.open_price}, open_time={self.open_time}, "
            f"sl={self.sl}, tp={self.tp}, pnl={self.pnl}, swap={self.swap}, comment={self.comment})"
        )


class SymbolData(BaseModel):
    symbol: str
    currency_base: str
    currency_profit: str
    currency_margin: str
    contract_size: str
    digits: str
    point: str
    spread: str
    stops_level: str
    price_change: str
    price_volatility: str
    volume_min: str
    volume_max: str
    volume_step: str
    volume_limit: str
    category: Optional[str]
    description: str

    def __repr__(self):
        return (
            f"SymbolData(symbol={self.symbol}, currency_base={self.currency_base}, currency_profit={self.currency_profit}, "
            f"currency_margin={self.currency_margin}, contract_size={self.contract_size}, digits={self.digits}, point={self.point}, "
            f"spread={self.spread}, stops_level={self.stops_level}, price_change={self.price_change}, price_volatility={self.price_volatility}, "
            f"volume_min={self.volume_min}, volume_max={self.volume_max}, volume_step={self.volume_step}, volume_limit={self.volume_limit}, "
            f"category={self.category}, description={self.description})"
        )
