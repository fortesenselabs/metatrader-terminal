import asyncio
from typing import List, Dict, Optional, Tuple, Union
from datetime import datetime, timezone, timedelta
from models import (
    DWXClientParams,
    Events,
    SubscribeRequest,
    SubscribeResponse,
    SymbolMarketData,
    TimeFrame,
    DataMode,
    TickDataEvent,
    BarDataEvent,
    Kline,
    KlineResponse,
    HistoricalKlineRequest,
)
from internal import SocketIOServerClient
from utils import Logger, date_to_timestamp
from .base_handler import BaseHandler


class KlineHandler(BaseHandler):
    """
    Handler class for managing Kline data events.

    Attributes:
        logger (Logger): Instance of the logger for logging events.
        previous_klines (Dict[str, set]): Dictionary to store previous Kline data.
        current_on_tick_data (Optional[TickDataEvent]): Current TickDataEvent instance.
        current_on_bar_data (Optional[BarDataEvent]): Current BarDataEvent instance.
        historical_klines (List[Kline]): List to store historical Kline data.
    """

    def __init__(
        self,
        dwx_client_params: DWXClientParams,
        pubsub_instance: SocketIOServerClient,
    ):
        """
        Initializes the KlineHandler with DWXClient parameters and a Pub/Sub instance.

        Args:
            dwx_client_params (DWXClientParams): Parameters for the DWX client.
            pubsub_instance (SocketIOServerClient): Instance of the SocketIOServerClient.
        """
        super().__init__(dwx_client_params, pubsub_instance)
        self.logger = Logger(name=__class__.__name__)
        self.previous_klines: Dict[str, set] = {}
        self.current_on_tick_data: Optional[TickDataEvent] = None
        self.current_on_bar_data: Optional[BarDataEvent] = None
        self.historical_klines: List[Kline] = []

    def on_tick(self, symbol: str, bid: float, ask: float) -> None:
        """
        Handles incoming tick data.

        Args:
            symbol (str): The symbol for which tick data is received.
            bid (float): The bid price.
            ask (float): The ask price.
        """
        now = datetime.now(timezone.utc)
        self.logger.info(f"on_tick: {now}, {symbol}, {bid}, {ask}")

        self.current_on_tick_data = TickDataEvent(
            symbol=symbol,
            time=now.strftime("%Y-%m-%d %H:%M:%S.%f"),
            bid=bid,
            ask=ask,
        )

        asyncio.run(
            self.publish_to_subscriber(
                Events.KlineSubscribeTick, self.current_on_tick_data.model_dump_json()
            )
        )

    def on_bar_data(
        self,
        symbol: str,
        time_frame: str,
        time: str,
        open_price: float,
        high: float,
        low: float,
        close_price: float,
        tick_volume: int,
    ) -> None:
        """
        Handles incoming bar data.

        Args:
            symbol (str): The symbol for which bar data is received.
            time_frame (str): The timeframe of the bar.
            time (str): The time of the bar.
            open_price (float): The opening price.
            high (float): The highest price.
            low (float): The lowest price.
            close_price (float): The closing price.
            tick_volume (int): The tick volume.
        """
        self.logger.info(
            f"on_bar_data: {symbol}, {time_frame}, {time}, {open_price}, {high}, {low}, {close_price}"
        )

        self.current_on_bar_data = BarDataEvent(
            symbol=symbol,
            time_frame=time_frame,
            time=time,
            open_price=open_price,
            high=high,
            low=low,
            close_price=close_price,
            tick_volume=tick_volume,
            is_final=True,
        )

        asyncio.run(
            self.publish_to_subscriber(
                Events.KlineSubscribeBar, self.current_on_bar_data.model_dump_json()
            )
        )

    def on_historic_data(
        self, symbol: str, time_frame: str, data: Dict[str, dict]
    ) -> None:
        """
        Handles incoming historic data.

        Args:
            symbol (str): The symbol for which historic data is received.
            time_frame (str): The timeframe of the historic data.
            data (Dict[str, dict]): The historic data.
        """
        self.logger.info(f"historic_data: {symbol}, {time_frame}, {len(data)} bars")

        historical_klines = [
            Kline(
                start_time=None,
                end_time=None,
                time=date_to_timestamp(_date),
                symbol=symbol,
                interval=time_frame,
                open=kline.get("open"),
                close=kline.get("close"),
                high=kline.get("high"),
                low=kline.get("low"),
                volume=kline.get("tick_volume"),
                is_final=True,
            )
            for _date, kline in data.items()
        ]

        asyncio.run(
            self.publish_to_subscriber(
                Events.KlineHistorical,
                KlineResponse(result=historical_klines).model_dump_json(),
            )
        )

    async def publish_to_subscriber(self, event_type: str, payload: dict) -> None:
        """
        Publishes data to a subscriber.

        Args:
            event_type (str): Type of the event to publish.
            payload (dict): Data payload to publish.
        """
        await self.pubsub.publish(event_type, payload)

    async def _subscribe_to_symbols(
        self,
        symbols_data: Optional[List[SymbolMarketData]] = [
            SymbolMarketData(
                symbol="Step Index", time_frame=TimeFrame.M5, mode=DataMode.BAR
            )
        ],
    ) -> List[str]:
        """
        Subscribe to symbols for receiving bar or tick data.

        Args:
            symbols_data (Optional[List[SymbolMarketData]]): List of symbols to subscribe to.

        Returns:
            List[str]: List of subscribed symbols.
        """
        if symbols_data is None:
            return []

        subscribed_symbols = []
        for symbol_data in symbols_data:
            if (
                symbol_data.mode != DataMode.TICK
                and symbol_data.time_frame != TimeFrame.CURRENT
            ):
                self.dwx_client.subscribe_symbols_bar_data(
                    [[symbol_data.symbol, symbol_data.time_frame.value]]
                )
            else:
                self.dwx_client.subscribe_symbols([symbol_data.symbol])
            subscribed_symbols.append(symbol_data.symbol)

        return subscribed_symbols

    async def subscribe(self, request: SubscribeRequest) -> SubscribeResponse:
        """
        Subscribe to tick data for the provided symbols.

        Args:
            request (SubscribeRequest): Request containing symbols data to subscribe to.

        Returns:
            SubscribeResponse: Response indicating the subscription status.
        """
        symbols_data = request.symbols_data
        subscribed_symbols = await self._subscribe_to_symbols(symbols_data)

        all_subscribed = len(subscribed_symbols) == len(symbols_data)
        response = {
            "message": f"Subscribed to symbols: {', '.join(subscribed_symbols)}",
            "subscribed": True,
            "all": all_subscribed,
        }
        return SubscribeResponse(**response)

    async def get_historic_data(
        self, kline_request: HistoricalKlineRequest
    ) -> SubscribeResponse:
        """
        Retrieve historical Kline data.

        Args:
            symbol (str): The symbol to retrieve historic data for.
            time_frame (str): The timeframe for the data.
            start (float): The start timestamp.
            end (float): The end timestamp.

        Returns:
            Union[List[Kline], None]: List of Kline data or None if not available.
        """

        start_time, end_time = self.parse_time(
            kline_request.time_frame,
            (
                datetime.fromtimestamp(kline_request.start_time)
                if kline_request.start_time is not None
                else None
            ),
            (
                datetime.fromtimestamp(kline_request.end_time)
                if kline_request.start_time is not None
                else None
            ),
            kline_request.limit,
        )

        self.dwx_client.get_historic_data(
            symbol=kline_request.symbol,
            time_frame=kline_request.time_frame.value,
            start=start_time,
            end=end_time,
        )

        response = {
            "message": f"Subscribed to historical kline data for: {kline_request.symbol}",
            "subscribed": True,
            "all": True,
        }

        return SubscribeResponse(**response)

    def parse_time(
        self,
        interval: TimeFrame,
        start_time: Optional[datetime],
        end_time: Optional[datetime],
        limit: int = 5,
    ) -> Tuple[float, float]:
        """
        Parse start and end times based on the interval and limit.

        Args:
            interval (TimeFrame): The timeframe interval.
            start_time (Optional[datetime]): The start time.
            end_time (Optional[datetime]): The end time.
            limit (int): The limit for the number of intervals.

        Returns:
            Tuple[float, float]: The parsed start and end times as timestamps.
        """
        if start_time is None and end_time is None:
            end_time = datetime.now(timezone.utc)
            timedelta_value = interval.to_timedelta() * limit
            start_time = (end_time - timedelta_value).timestamp()
            end_time = end_time.timestamp()

        if start_time is None:
            timedelta_value = interval.to_timedelta() * limit
            start_time = (end_time - timedelta_value).timestamp()

        return start_time, end_time

    # async def get_latest_klines(self, request: KlineRequest) -> List[Kline]:
    #     """
    #     Retrieve the latest Kline data based on the request.

    #     Args:
    #         request (KlineRequest): The Kline request details.

    #     Returns:
    #         List[Kline]: List of Kline data.
    #     """
    #     request_query = f"get_latest_klines.request: {request.model_dump()}"
    #     self.logger.info(request_query)
    #     active_symbols = self.processor.get_active_symbols(request.symbol)
    #     if len(active_symbols) == 0:
    #         return []  # TODO: return validation Error

    #     start_time, end_time = self.parse_time(
    #         request.interval,
    #         (
    #             datetime.fromtimestamp(request.start_time)
    #             if request.start_time is not None
    #             else None
    #         ),
    #         (
    #             datetime.fromtimestamp(request.end_time)
    #             if request.start_time is not None
    #             else None
    #         ),
    #         request.limit,
    #     )
    #     kline_data = await self.processor.get_historic_data(
    #         symbol=request.symbol,
    #         time_frame=TimeFrame(request.interval).value,
    #         start=start_time,
    #         end=end_time,
    #     )
    #     if kline_data is None:
    #         return []

    #     return kline_data

    # async def get_kline_data(self, symbol: str, interval: TimeFrame) -> KlineEvent:
    #     """
    #     Retrieve the latest Kline data event.

    #     Args:
    #         symbol (str): The symbol to retrieve Kline data for.
    #         interval (TimeFrame): The timeframe interval.

    #     Returns:
    #         KlineEvent: The Kline event data.
    #     """
    #     request_query = f"symbol: {symbol} | interval: {interval}"
    #     self.logger.info(request_query)

    #     _data: Union[BarDataEvent, None] = self.current_on_bar_data
    #     if _data is None:
    #         return KlineEvent(symbol=symbol)

    #     kline_data = KlineEvent(
    #         event=_data.event,
    #         time=date_to_timestamp(_data.time),
    #         symbol=symbol,
    #         kline=Kline(
    #             start_time=None,
    #             end_time=None,
    #             symbol=_data.symbol,
    #             interval=_data.time_frame,
    #             open=str(_data.open),
    #             close=str(_data.close),
    #             high=str(_data.high),
    #             low=str(_data.low),
    #             volume=str(_data.tick_volume),
    #             is_final=_data.is_final,
    #         ),
    #     )

    #     return kline_data

    # async def get_tick_data(self, symbol: str) -> TickInfoResponse:
    #     """
    #     Retrieve the latest tick data.

    #     Args:
    #         symbol (str): The symbol to retrieve tick data for.

    #     Returns:
    #         TickInfoResponse: The tick data response.
    #     """
    #     request_query = f"symbol: {symbol}"
    #     self.logger.info(request_query)

    #     _data: Union[TickDataEvent, None] = self.current_on_tick_data
    #     if _data is None:
    #         return TickDataEvent(symbol=symbol)

    #     tick_data = TickInfoResponse(
    #         event=_data.event,
    #         time=date_to_timestamp(_data.time),
    #         symbol=_data.symbol,
    #         bid=_data.bid,
    #         ask=_data.ask,
    #     )
    #     return tick_data

    # async def get_historical_data(self):
    #     """
    #     Placeholder for retrieving historical data.

    #     To be implemented.
    #     """
    #     return
