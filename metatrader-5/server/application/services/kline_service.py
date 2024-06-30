from typing import Optional, List, Dict, Union
from application.config.logger import AppLogger
from application.lib.processor import MetaTraderDataProcessor
from application.models.symbol_models import (
    SymbolMarketData,
)
from application.models.kline_models import (
    SubscribeRequest,
    SubscribeResponse,
    WsKline,
    WsKlineEvent,
    WsRequest,
    TickInfoResponse,
    WsRequestMethod,
)
from application.models.mt_models import (
    BarDataEvent,
    TickDataEvent,
)
from application.models.enum_types import (
    TimeFrame,
    DataMode,
)
from application.utils.utils import date_to_timestamp


class KlineService:
    def __init__(self, logger: AppLogger, processor: MetaTraderDataProcessor):
        self.logger = logger
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

    async def get_kline_data(self, symbol: str, interval: TimeFrame) -> WsKlineEvent:
        request_query = f"symbol: {symbol} | interval: {interval}"
        self.logger.info(request_query)

        # await parse_ws_request(request, RequestType.Kline)
        # _data: Union[BarDataEvent, None] = self.processor.get_data(symbol, DataMode.BAR)
        _data: Union[BarDataEvent, None] = self.processor.current_on_bar_data
        if _data is None:
            return WsKlineEvent(symbol=symbol)

        kline_data = WsKlineEvent(
            event=_data.event,
            time=date_to_timestamp(_data.time),
            symbol=symbol,
            kline=WsKline(
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
