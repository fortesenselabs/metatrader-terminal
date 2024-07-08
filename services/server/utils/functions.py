import re
from typing import List
from datetime import datetime, timezone
from models import ServerTimeResponse


def normalize_booleans(arr) -> bool:
    if not len(arr) or False in arr:
        return False
    return True


def get_server_time() -> ServerTimeResponse:
    """
    Retrieves the current server time as a Unix timestamp and timezone.

    Returns:
        ServerTimeResponse: Current server time with timezone and Unix timestamp.
    """
    now = datetime.now(timezone.utc)
    response = {"timezone": "UTC", "unix_timestamp": int(now.timestamp())}
    return ServerTimeResponse(**response)


def detect_format(date_str: str, formats: List[str]) -> str:
    for date_format in formats:
        try:
            datetime.strptime(date_str, date_format)
            return date_format
        except ValueError:
            continue

    raise ValueError(f"Time data '{date_str}' does not match any known formats.")


def date_to_timestamp(date_str: str) -> int:
    # List of potential date formats
    date_formats = [
        "%Y-%m-%d %H:%M:%S.%f",
        "%Y.%m.%d %H:%M",
        "%Y.%m.%d %H:%M:%S",
        "%Y-%m-%d %H:%M:%S.%f%z",
        "%Y-%m-%d %H:%M:%S%z",
        "%Y-%m-%d %H:%M:%S",
        "%Y-%m-%d %H:%M",
        "%Y/%m/%d %H:%M:%S.%f%z",
        "%Y/%m/%d %H:%M:%S%z",
        "%Y/%m/%d %H:%M:%S",
        "%Y/%m/%d %H:%M",
    ]

    # Detect the correct date format
    date_format = detect_format(date_str, date_formats)

    # Convert the date string to a datetime object
    dt_obj = datetime.strptime(date_str, date_format)

    # Convert the datetime object to a timestamp
    timestamp = int(dt_obj.timestamp())

    return timestamp


def split_by_number(timeframe: str):
    # Regular expression to find the number in the string
    match = re.search(r"(\d+)", timeframe)
    if match:
        # Extract the prefix and the number
        number = match.group(1)
        parts = re.split(number, timeframe)
        return parts[0], number
    return None, None


# def calculate_start_time(interval: TimeFrame) -> float:
#     timedelta_value = get_timeframe_timedelta(interval)
#     return (datetime.now(timezone.utc) - timedelta_value).timestamp()


# TIMEFRAME_MAP = {
#     TimeFrame.M1: lambda limit: timedelta(minutes=limit),
#     TimeFrame.M2: lambda limit: timedelta(minutes=limit),
#     TimeFrame.M3: lambda limit: timedelta(minutes=limit),
#     TimeFrame.M4: lambda limit: timedelta(minutes=limit),
#     TimeFrame.M5: lambda limit: timedelta(minutes=limit),
#     TimeFrame.M6: lambda limit: timedelta(minutes=limit),
#     TimeFrame.M10: timedelta(minutes=10),
#     TimeFrame.M12: timedelta(minutes=12),
#     TimeFrame.M15: timedelta(minutes=15),
#     TimeFrame.M20: timedelta(minutes=20),
#     TimeFrame.M30: timedelta(minutes=30),
#     TimeFrame.H1: timedelta(hours=1),
#     TimeFrame.H2: timedelta(hours=2),
#     TimeFrame.H3: timedelta(hours=3),
#     TimeFrame.H4: timedelta(hours=4),
#     TimeFrame.H6: timedelta(hours=6),
#     TimeFrame.H8: timedelta(hours=8),
#     TimeFrame.H12: timedelta(hours=12),
#     TimeFrame.D1: timedelta(days=1),
#     TimeFrame.W1: timedelta(weeks=1),
#     TimeFrame.MN1: timedelta(days=30),  # Approximation
# }

# def get_timeframe_timedelta(time_frame: TimeFrame, offset: int = 1) -> timedelta:
#     TIMEFRAME_MAP = {
#         "M": lambda limit: timedelta(minutes=limit),
#         "H": lambda limit: timedelta(hours=limit),
#         "D": lambda limit: timedelta(days=limit),
#         "W": lambda limit: timedelta(weeks=limit),
#         "MN": lambda limit: timedelta(days=30),  # TODO: Month Data might not work well
#     }
#     interval = time_frame.to_interval()
#     if interval is not None:
#         prefix, _ = split_by_number(time_frame.value)
#         return TIMEFRAME_MAP[prefix](interval * offset)

#     # from_string()
#     # check for minutes
#     # check for hours
#     # get there intervals before passing the to the timedelta function
#     return timedelta()

# @api_router.post("/subscribe", response_model=SubscribeResponse)
# async def subscribe(request: SubscribeRequest):
#     """
#     Subscribe to tick data for the provided symbols.

#     Body:
#         symbols_data: List of symbols to subscribe to.
#     """
#     symbols_data = request.symbols_data
#     subscribed_symbols = processor.subscribe_symbols(symbols_data)

#     all_subscribed = len(subscribed_symbols) == len(symbols_data)
#     response = {
#         "message": f"Subscribed to symbols: {', '.join(subscribed_symbols)}",
#         "subscribed": True,
#         "all": all_subscribed,
#     }
#     return SubscribeResponse(**response)


# if request.id not in list(self.previous_klines.keys()):
#     self.previous_klines[request.id] = set()


# if len(_data) > 0 and timestamp not in self.previous_klines[request.id]:
#     _data["is_final"] = False
#     self.previous_klines[request.id].add(timestamp)


# response = KlineResponse(
#     id=request.id, status=200, result=kline_data, rateLimits=[RATE_LIMIT]
# )

# else:
#     kline_data = WsKlineEvent(
#         event=None,
#         time=get_server_time().unix_timestamp,
#         symbol=symbol,
#         kline=None,
#     )


# # Sample data to mimic database response
# SAMPLE_KLINE_DATA = [
#     [
#         # 1655971200000,  # Kline open time
#         "0.01086000",  # Open price
#         "0.01086600",  # High price
#         "0.01083600",  # Low price
#         "0.01083800",  # Close price
#         "2290.53800000",  # Volume
#         1655974799999,  # Kline close time
#         "24.85074442",  # Quote asset volume
#         2283,  # Number of trades
#         "1171.64000000",  # Taker buy base asset volume
#         "12.71225884",  # Taker buy quote asset volume
#         "0",  # Unused field, ignore
#     ]
# ]

# async def parse_ws_request(request: WsRequest, request_type: RequestType):
#     # if request.method == WsRequest
#     return SAMPLE_KLINE_DATA


# AttributeError: 'NoneType' object has no attribute 'id'
# New order:  {'magic': 1399, 'symbol': 'Step Index', 'lots': 0.3, 'type': 'buy', 'open_price': 8035.6, 'open_time': '2024.06.26 15:13:32', 'SL': 0.0, 'TP': 0.0, 'pnl': 0.0, 'swap': 0.0, 'comment': ''}
# New order:  {'magic': 1399, 'symbol': 'Step Index', 'lots': 0.3, 'type': 'buy', 'open_price': 8035.6, 'open_time': '2024.06.26 15:13:32', 'SL': 0.0, 'TP': 0.0, 'pnl': 0.0, 'swap': 0.0, 'comment': ''}
# self.dwx.open_orders:  {'3965817598': {'magic': 1399, 'symbol': 'Step Index', 'lots': 0.3, 'type': 'buy', 'open_price': 8035.6, 'open_time': '2024.06.26 15:13:32', 'SL': 0.0, 'TP': 0.0, 'pnl': 0.0, 'swap': 0.0, 'comment': ''}, '3965817473': {'magic': 9445, 'symbol': 'Step Index', 'lots': 0.3, 'type': 'buy', 'open_price': 8035.3, 'open_time': '2024.06.26 15:13:25', 'SL': 0.0, 'TP': 0.0, 'pnl': 0.6, 'swap': 0.0, 'comment': ''}, '3965817289': {'magic': 1828, 'symbol': 'Step Index', 'lots': 0.3, 'type': 'buy', 'open_price': 8035.3, 'open_time': '2024.06.26 15:13:17', 'SL': 0.0, 'TP': 0.0, 'pnl': 0.6, 'swap': 0.0, 'comment': ''}}

# SendInfo("Successfully sent order: " + symbol + ", " + OrderTypeToString(orderType) + ", " + DoubleToString(lots, lotSizeDigits) + ", " + DoubleToString(price, digits));

# def get_data(
#     self, symbol: str, mode: DataMode
# ) -> Union[TickDataEvent, BarDataEvent, None]:
#     # if (
#     #     self.current_on_tick_data.symbol != symbol
#     #     or self.current_on_bar_data.symbol != symbol
#     # ):
#     #     return None

#     current_data = None

#     if mode != DataMode.BAR and self.current_on_tick_data is not None:
#         current_data = self.current_on_tick_data
#     else:
#         if self.current_on_bar_data is not None:
#             current_data = self.current_on_bar_data

#         self.current_on_bar_data = None

#     return current_data
