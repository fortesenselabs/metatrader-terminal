#
# MetaTraderDataProcessor Types
#
from typing import Optional, List
from enum import Enum
from pydantic import BaseModel
from .orders_models import SideType, OrderType, TimeInForceType


class DWXClientParams(BaseModel):
    """
    This class defines the parameters required to initialize a DWXClient object.

    Attributes:
        mt_directory_path (str): The path to the MetaTrader directory containing the MQL5 libraries.
        sleep_delay (float, optional): The amount of time (in seconds) to wait between retries when
                                       communicating with MetaTrader. Defaults to 0.005(5ms).
        max_retry_command_seconds (int, optional): The maximum number of seconds to keep retrying a
                                                    command before giving up. Defaults to 10.
        verbose (bool, optional): Whether to print verbose logging messages. Defaults to True.
    """

    mt_directory_path: str
    sleep_delay: float = 0.005
    max_retry_command_seconds: int = 10
    verbose: bool = True


class BarDataEvent:
    def __init__(
        self,
        symbol: str,
        time_frame: str,
        time: str,
        open_price: float,
        high: float,
        low: float,
        close_price: float,
        tick_volume: Optional[float] = None,
        is_final: Optional[bool] = True,
    ):
        self.event = "on_bar_data"
        self.symbol = symbol
        self.time_frame = time_frame
        self.time = time
        self.open = open_price
        self.high = high
        self.low = low
        self.close = close_price
        self.tick_volume = tick_volume
        self.is_final = is_final


class TickDataEvent:
    def __init__(
        self,
        symbol: str,
        time: Optional[str] = None,
        bid: Optional[float] = None,
        ask: Optional[float] = None,
        event_type: Optional[str] = "on_tick",
    ):
        self.event = event_type
        self.symbol = symbol
        self.time = time
        self.bid = bid
        self.ask = ask


class MTOrderType(Enum):
    BUY = "buy"
    SELL = "sell"
    BUY_LIMIT = "buylimit"
    SELL_LIMIT = "selllimit"
    BUY_STOP = "buystop"
    SELL_STOP = "sellstop"

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


class MTOrderStatus(Enum):
    NEW = "NEW"
    NONE = "NONE"
    PENDING = "PENDING"
    FILLED = "FILLED"
    CANCELED = "CANCELED"


# OrderStatusTypeNew             OrderStatusType = "NEW"
# OrderStatusTypePartiallyFilled OrderStatusType = "PARTIALLY_FILLED"
# OrderStatusTypeFilled          OrderStatusType = "FILLED"
# OrderStatusTypeCanceled        OrderStatusType = "CANCELED"
# OrderStatusTypePendingCancel   OrderStatusType = "PENDING_CANCEL"
# OrderStatusTypeRejected        OrderStatusType = "REJECTED"
# OrderStatusTypeExpired         OrderStatusType = "EXPIRED"


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


# class SymbolData:
#     def __init__(
#         self,
#         symbol: str,
#         currency_base: str,
#         currency_profit: str,
#         currency_margin: str,
#         contract_size: str,
#         digits: str,
#         point: str,
#         spread: str,
#         stops_level: str,
#         price_change: str,
#         price_volatility: str,
#         volume_min: str,
#         volume_max: str,
#         volume_step: str,
#         volume_limit: str,
#         category: Optional[str],
#         description: str,
#     ):
#         self.symbol = symbol
#         self.currency_base = currency_base
#         self.currency_profit = currency_profit
#         self.currency_margin = currency_margin
#         self.contract_size = contract_size
#         self.digits = digits
#         self.point = point
#         self.spread = spread
#         self.stops_level = stops_level
#         self.price_change = price_change
#         self.price_volatility = price_volatility
#         self.volume_min = volume_min
#         self.volume_max = volume_max
#         self.volume_step = volume_step
#         self.volume_limit = volume_limit
#         self.category = category
#         self.description = description

#     def __repr__(self):
#         return (
#             f"SymbolData(symbol={self.symbol}, currency_base={self.currency_base}, currency_profit={self.currency_profit}, "
#             f"currency_margin={self.currency_margin}, contract_size={self.contract_size}, digits={self.digits}, point={self.point}, "
#             f"spread={self.spread}, stops_level={self.stops_level}, price_change={self.price_change}, price_volatility={self.price_volatility}, "
#             f"volume_min={self.volume_min}, volume_max={self.volume_max}, volume_step={self.volume_step}, volume_limit={self.volume_limit}, "
#             f"category={self.category}, description={self.description})"
#         )


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
