from datetime import timedelta
from enum import Enum
from typing import List
from .utils import reverse_string


# Enums
class SecType(Enum):
    NONE = 0
    API_KEY = 1
    SIGNED = 2


class SideType(str, Enum):
    BUY = "BUY"
    SELL = "SELL"


class OrderType(str, Enum):
    MARKET = "MARKET"
    LIMIT = "LIMIT"
    STOP = "STOP"
    STOP_LIMIT = "STOP_LIMIT"


class TimeInForceType(str, Enum):
    GTC = "GTC"


class OrderStatusType(str, Enum):
    NEW = "NEW"
    PARTIALLY_FILLED = "PARTIALLY_FILLED"
    FILLED = "FILLED"
    CANCELED = "CANCELED"
    PENDING_CANCEL = "PENDING_CANCEL"
    REJECTED = "REJECTED"
    EXPIRED = "EXPIRED"


class SymbolFilterType(str, Enum):
    LOT_SIZE = "LOT_SIZE"
    PRICE_FILTER = "PRICE_FILTER"
    PERCENT_PRICE = "PERCENT_PRICE"
    MIN_NOTIONAL = "MIN_NOTIONAL"
    ICEBERG_PARTS = "ICEBERG_PARTS"
    MARKET_LOT_SIZE = "MARKET_LOT_SIZE"
    MAX_NUM_ALGO_ORDERS = "MAX_NUM_ALGO_ORDERS"


class TimeFrame(Enum):
    CURRENT = "CURRENT"
    M1 = "M1"
    M2 = "M2"
    M3 = "M3"
    M4 = "M4"
    M5 = "M5"
    M6 = "M6"
    M10 = "M10"
    M12 = "M12"
    M15 = "M15"
    M20 = "M20"
    M30 = "M30"
    H1 = "H1"
    H2 = "H2"
    H3 = "H3"
    H4 = "H4"
    H6 = "H6"
    H8 = "H8"
    H12 = "H12"
    D1 = "D1"
    W1 = "W1"
    MN1 = "MN1"

    @classmethod
    def from_string(cls, string):
        try:
            return cls[string]
        except KeyError:
            return None

    @classmethod
    def export_all(cls) -> List[str]:
        return [order_type.value for order_type in cls]

    def to_timedelta(self) -> timedelta:
        TIMEFRAME_MAP = {
            TimeFrame.M1: timedelta(minutes=1),
            TimeFrame.M2: timedelta(minutes=2),
            TimeFrame.M3: timedelta(minutes=3),
            TimeFrame.M4: timedelta(minutes=4),
            TimeFrame.M5: timedelta(minutes=5),
            TimeFrame.M6: timedelta(minutes=6),
            TimeFrame.M10: timedelta(minutes=10),
            TimeFrame.M12: timedelta(minutes=12),
            TimeFrame.M15: timedelta(minutes=15),
            TimeFrame.M20: timedelta(minutes=20),
            TimeFrame.M30: timedelta(minutes=30),
            TimeFrame.H1: timedelta(hours=1),
            TimeFrame.H2: timedelta(hours=2),
            TimeFrame.H3: timedelta(hours=3),
            TimeFrame.H4: timedelta(hours=4),
            TimeFrame.H6: timedelta(hours=6),
            TimeFrame.H8: timedelta(hours=8),
            TimeFrame.H12: timedelta(hours=12),
            TimeFrame.D1: timedelta(days=1),
            TimeFrame.W1: timedelta(weeks=1),
            TimeFrame.MN1: timedelta(days=30),  # Approximation
        }

        return TIMEFRAME_MAP.get(self, timedelta())

    @classmethod
    def freq_from_pandas(cls, freq: str) -> "TimeFrame":
        """
        Map pandas frequency to metatrader API frequency

        :param freq: pandas frequency https://pandas.pydata.org/docs/user_guide/timeseries.html#timeseries-offset-aliases
        :return: metatrader frequency
        """
        if freq.endswith("min"):  # timeframe enum
            freq = reverse_string(freq.replace("min", "M"))
        elif freq.endswith("D"):  # timeframe enum
            freq = reverse_string(freq)
        elif freq.endswith("W"):
            freq = reverse_string(freq)
        elif freq.endswith("MN"):
            freq = reverse_string(freq)
        elif freq == "BMS":
            freq = freq.replace("BMS", "MN1")

        timeframe = cls.from_string(freq)
        if timeframe is None:
            raise ValueError(f"Not supported Metatrader frequency {freq}")

        return timeframe


#
# TODO: fix the following
#

SYMBOL_TYPE_SPOT = "SPOT"

ORDER_STATUS_NEW = "NEW"
ORDER_STATUS_PARTIALLY_FILLED = "PARTIALLY_FILLED"
ORDER_STATUS_FILLED = "FILLED"
ORDER_STATUS_CANCELED = "CANCELED"
ORDER_STATUS_PENDING_CANCEL = "PENDING_CANCEL"
ORDER_STATUS_REJECTED = "REJECTED"
ORDER_STATUS_EXPIRED = "EXPIRED"

KLINE_INTERVAL_1SECOND = "1s"
KLINE_INTERVAL_1MINUTE = "1m"
KLINE_INTERVAL_3MINUTE = "3m"
KLINE_INTERVAL_5MINUTE = "5m"
KLINE_INTERVAL_15MINUTE = "15m"
KLINE_INTERVAL_30MINUTE = "30m"
KLINE_INTERVAL_1HOUR = "1h"
KLINE_INTERVAL_2HOUR = "2h"
KLINE_INTERVAL_4HOUR = "4h"
KLINE_INTERVAL_6HOUR = "6h"
KLINE_INTERVAL_8HOUR = "8h"
KLINE_INTERVAL_12HOUR = "12h"
KLINE_INTERVAL_1DAY = "1d"
KLINE_INTERVAL_3DAY = "3d"
KLINE_INTERVAL_1WEEK = "1w"
KLINE_INTERVAL_1MONTH = "1M"

SIDE_BUY = "BUY"
SIDE_SELL = "SELL"

ORDER_TYPE_LIMIT = "LIMIT"
ORDER_TYPE_MARKET = "MARKET"
ORDER_TYPE_STOP_LOSS = "STOP_LOSS"
ORDER_TYPE_STOP_LOSS_LIMIT = "STOP_LOSS_LIMIT"
ORDER_TYPE_TAKE_PROFIT = "TAKE_PROFIT"
ORDER_TYPE_TAKE_PROFIT_LIMIT = "TAKE_PROFIT_LIMIT"
ORDER_TYPE_LIMIT_MAKER = "LIMIT_MAKER"

FUTURE_ORDER_TYPE_LIMIT = "LIMIT"
FUTURE_ORDER_TYPE_MARKET = "MARKET"
FUTURE_ORDER_TYPE_STOP = "STOP"
FUTURE_ORDER_TYPE_STOP_MARKET = "STOP_MARKET"
FUTURE_ORDER_TYPE_TAKE_PROFIT = "TAKE_PROFIT"
FUTURE_ORDER_TYPE_TAKE_PROFIT_MARKET = "TAKE_PROFIT_MARKET"
FUTURE_ORDER_TYPE_LIMIT_MAKER = "LIMIT_MAKER"
FUTURE_ORDER_TYPE_TRAILING_STOP_MARKET = "TRAILING_STOP_MARKET"

TIME_IN_FORCE_GTC = "GTC"  # Good till cancelled
TIME_IN_FORCE_IOC = "IOC"  # Immediate or cancel
TIME_IN_FORCE_FOK = "FOK"  # Fill or kill
TIME_IN_FORCE_GTX = "GTX"  # Post only order

ORDER_RESP_TYPE_ACK = "ACK"
ORDER_RESP_TYPE_RESULT = "RESULT"
ORDER_RESP_TYPE_FULL = "FULL"

WEBSOCKET_DEPTH_5 = "5"
WEBSOCKET_DEPTH_10 = "10"
WEBSOCKET_DEPTH_20 = "20"

NO_SIDE_EFFECT_TYPE = "NO_SIDE_EFFECT"
MARGIN_BUY_TYPE = "MARGIN_BUY"
AUTO_REPAY_TYPE = "AUTO_REPAY"


class HistoricalKlinesType(Enum):
    SPOT = 1
    FUTURES = 2
    FUTURES_COIN = 3


class FuturesType(Enum):
    USD_M = 1
    COIN_M = 2


class ContractType(Enum):
    PERPETUAL = "perpetual"
    CURRENT_QUARTER = "current_quarter"
    NEXT_QUARTER = "next_quarter"
