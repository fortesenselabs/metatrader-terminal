from models.events import Events


from datetime import datetime, timezone
from typing import Optional, List, Dict, Union, Tuple
from application.config.logger import AppLogger
from application.lib import MetaTraderDataProcessor
from application.models import (
    SymbolMarketData,
    SubscribeRequest,
    SubscribeResponse,
    Kline,
    KlineEvent,
    KlineRequest,
    WsRequest,
    TickInfoResponse,
    WsRequestMethod,
    BarDataEvent,
    TickDataEvent,
    TimeFrame,
    DataMode,
)
from application.utils import date_to_timestamp


class KlineService:
    def __init__(self, processor: MetaTraderDataProcessor):
        self.logger = AppLogger(name=__class__.__name__)
        self.processor = processor
        self.connected_clients = set()
        self.previous_klines: Dict[str, set] = {}

    async def subscribe(self, request: SubscribeRequest) -> SubscribeResponse:
        """
        Subscribe to tick data for the provided symbols.

        Body:
            symbols_data: List of symbols to subscribe to.
        """
        symbols_data = request.symbols_data
        subscribed_symbols = self.processor.subscribe_symbols(symbols_data)

        all_subscribed = len(subscribed_symbols) == len(symbols_data)
        response = {
            "message": f"Subscribed to symbols: {', '.join(subscribed_symbols)}",
            "subscribed": True,
            "all": all_subscribed,
        }
        return SubscribeResponse(**response)

    async def add_subscriber(
        self, request: WsRequest, symbol: str, interval: TimeFrame
    ):
        if (
            request.method == WsRequestMethod.SUBSCRIBE
            and request.id not in self.connected_clients
        ):
            sub_request = SubscribeRequest(
                symbols_data=[
                    SymbolMarketData(
                        symbol=symbol, time_frame=interval, mode=DataMode.BAR
                    )
                ]
            )

            sub_response = await self.subscribe(sub_request)
            if sub_response.subscribed:
                self.logger.info(
                    f"{request.id} subscribed to  {symbol} {interval} data => {sub_response.message} | {sub_response.subscribed} | {sub_response.all}"
                )
                self.connected_clients.add(request.id)
        return

    def parse_time(
        self,
        interval: TimeFrame,
        start_time: Optional[datetime],
        end_time: Optional[datetime],
        limit: int = 5,
    ) -> Tuple[float, float]:
        if start_time is None and end_time is None:
            end_time = datetime.now(timezone.utc)  #
            timedelta_value = interval.to_timedelta() * limit
            start_time = (end_time - timedelta_value).timestamp()
            end_time = end_time.timestamp()

        if start_time is None:

            timedelta_value = interval.to_timedelta() * limit
            start_time = (end_time - timedelta_value).timestamp()

        return start_time, end_time

    async def get_latest_klines(self, request: KlineRequest) -> List[Kline]:
        request_query = f"get_latest_klines.request: {request.model_dump()}"
        # print(request_query)
        # print(request.end_time - request.start_time)
        self.logger.info(request_query)
        active_symbols = self.processor.get_active_symbols(request.symbol)
        if len(active_symbols) == 0:
            return []  # TODO: return validation Error

        start_time, end_time = self.parse_time(
            request.interval,
            (
                datetime.fromtimestamp(request.start_time)
                if request.start_time is not None
                else None
            ),
            (
                datetime.fromtimestamp(request.end_time)
                if request.start_time is not None
                else None
            ),
            request.limit,
        )
        kline_data = await self.processor.get_historic_data(
            symbol=request.symbol,
            time_frame=TimeFrame(request.interval).value,
            start=start_time,
            end=end_time,
        )
        if kline_data is None:
            return []

        return kline_data

    async def get_kline_data(self, symbol: str, interval: TimeFrame) -> KlineEvent:
        request_query = f"symbol: {symbol} | interval: {interval}"
        self.logger.info(request_query)

        # await parse_ws_request(request, RequestType.Kline)
        # _data: Union[BarDataEvent, None] = self.processor.get_data(symbol, DataMode.BAR)
        _data: Union[BarDataEvent, None] = self.processor.current_on_bar_data
        if _data is None:
            return KlineEvent(symbol=symbol)

        kline_data = KlineEvent(
            event=_data.event,
            time=date_to_timestamp(_data.time),
            symbol=symbol,
            kline=Kline(
                start_time=None,
                end_time=None,
                symbol=_data.symbol,
                interval=_data.time_frame,
                open=str(_data.open),
                close=str(_data.close),
                high=str(_data.high),
                low=str(_data.low),
                volume=str(_data.tick_volume),
                is_final=_data.is_final,
            ),
        )

        return kline_data

    async def get_tick_data(self, symbol):
        request_query = f"symbol: {symbol}"
        self.logger.info(request_query)

        # await parse_ws_request(request, RequestType.Kline)
        # _data: Union[TickDataEvent, None] = self.processor.get_data(
        #     symbol, DataMode.TICK
        # )
        _data: Union[TickDataEvent, None] = self.processor.current_on_tick_data
        if _data is None:
            return TickDataEvent(symbol=symbol)

        tick_data = TickInfoResponse(
            event=_data.event,
            time=date_to_timestamp(_data.time),
            symbol=_data.symbol,
            bid=_data.bid,
            ask=_data.ask,
        )
        return tick_data

    async def get_historical_data(self):
        return
