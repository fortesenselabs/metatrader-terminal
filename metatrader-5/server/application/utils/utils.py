from datetime import datetime, timezone
from typing import List
from application.models import ServerTimeResponse


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
        "%Y-%m-%d %H:%M:%S.%f%z",
        "%Y-%m-%d %H:%M:%S%z",
        "%Y-%m-%d %H:%M:%S",
        "%Y-%m-%d %H:%M",
        "%Y.%m.%d %H:%M",
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
