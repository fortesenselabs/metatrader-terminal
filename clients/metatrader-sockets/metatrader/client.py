import json
import asyncio
import typing as t
from typing import Optional, Callable, List
from metatrader.models import (
    Events,
    AccountInfoResponse,
    ExchangeInfoResponse,
    MultiOrdersResponse,
    OrderResponse,
    SubscribeResponse,
    CreateOrderRequest,
    CancelOrderRequest,
    HistoricalKlineRequest,
    KlineResponse,
    TimeFrame,
    DataMode,
    SubscribeRequest,
    SymbolMarketData,
)
from metatrader.logging import Logger
from metatrader.socketio import SocketIOServerClient


T = t.TypeVar("T")


class get_something(t.Generic[T]):
    def __new__(
        cls,
        v: str,
    ):
        generated_instance = super().__new__(cls)
        return generated_instance.execute(v)

    def execute(self, v: str) -> T:
        return t.cast(T, v)


class TerminalClient:
    """
    A client to interact with the MetaTrader terminal via socket.io.

    Attributes:
        url (str): The URL of the MetaTrader socket.io server.
        verbose (bool): Enables verbose logging if set to True.
        session_data (dict): Stores the data received during the session.
    """

    def __init__(self, url: str = "http://localhost:8000", verbose: bool = False):
        """
        Initializes the TerminalClient.

        Args:
            url (str): The URL of the MetaTrader socket.io server.
            verbose (bool): Enables verbose logging if set to True.
        """
        self.verbose = verbose
        self.url = url
        self.empty_request = "{}"
        self.client_instance: Optional[SocketIOServerClient] = None
        self.session_data = {}
        self.logger = None

    @classmethod
    async def create(cls, url: str = "http://localhost:8000", verbose: bool = False):
        """
        Asynchronously creates an instance of TerminalClient.

        Args:
            url (str): The URL of the MetaTrader socket.io server.
            verbose (bool): Enables verbose logging if set to True.

        Returns:
            TerminalClient: The initialized TerminalClient instance.
        """
        self = cls(url, verbose)
        await self.connect()
        return self

    async def connect(self):
        """
        Connects to the MetaTrader socket.io server.
        """
        self.client_instance = await SocketIOServerClient.connect_client(self.url)
        if self.verbose:
            self.logger = Logger(name=__class__.__name__)
            self.logger.info(
                f"Connected to Server at {self.url}: {self.client_instance.instance.connected}"
            )
        return self.client_instance

    async def subscribe_to_event(self, event: str):
        """
        Subscribes to a specified event and stores the received data in session_data.

        Args:
            event (str): The event to subscribe to.
        """

        async def handler(data):
            self.session_data[event] = json.loads(data)

        await self.client_instance.subscribe_to_server(event, handler)

    async def publish_event(self, event: str, data: str):
        """
        Publishes data to a specified event.

        Args:
            event (str): The event to publish data to.
            data (str): The data to publish.
        """
        await self.client_instance.publish(event, data)

    def clear_session_data(self, event: str):
        """
        Clears the session data for a specific event.

        Args:
            event (str): The event for which to clear the session data.
        """
        if event in self.session_data:
            del self.session_data[event]

    async def send_request(
        self, event: str, request: str, output_type: t.Type[T]
    ) -> Optional[T]:
        await self.subscribe_to_event(event)
        await self.publish_event(event, request)

        if await self.client_instance.wait_for_event(
            lambda: event in self.session_data, timeout=30
        ):
            response = self.session_data.get(event)
            self.clear_session_data(event)
            # await self.client_instance.unsubscribe_from_server(event)
            return output_type(**response) if response else None

        # await self.client_instance.unsubscribe_from_server(event)
        return None

    async def get_account(self) -> Optional[AccountInfoResponse]:
        """
        Fetches the account information.

        Returns:
            AccountInfoResponse: The account information response.
        """
        account_info = await self.send_request(
            Events.Account, self.empty_request, AccountInfoResponse
        )
        if account_info is None:
            return None

        return account_info

    async def get_exchange_info(self) -> Optional[ExchangeInfoResponse]:
        """
        Fetches the exchange information.

        Returns:
            ExchangeInfoResponse: The exchange information response.
        """
        exchange_info = await self.send_request(
            Events.ExchangeInfo, self.empty_request, ExchangeInfoResponse
        )
        if exchange_info is None:
            return None

        return exchange_info

    async def get_open_orders(self) -> Optional[MultiOrdersResponse]:
        open_orders = await self.send_request(
            Events.GetOpenOrders, self.empty_request, MultiOrdersResponse
        )
        if open_orders is None:
            return None

        return open_orders

    async def create_order(
        self, order_request: CreateOrderRequest
    ) -> Optional[OrderResponse]:
        new_order = await self.send_request(
            Events.CreateOrder, order_request.model_dump_json(), OrderResponse
        )
        if new_order is None:
            return None

        return new_order

    async def close_order(
        self, order_request: CancelOrderRequest
    ) -> Optional[OrderResponse]:

        # TODO: consider multiple closing orders
        order = await self.send_request(
            Events.CloseOrder, order_request.model_dump_json(), OrderResponse
        )
        if order is None:
            return None

        return order

    async def get_historical_kline_data(
        self, request: HistoricalKlineRequest
    ) -> Optional[KlineResponse]:
        subscribe_response = await self.send_request(
            Events.KlineHistorical, request.model_dump_json(), SubscribeResponse
        )
        if self.verbose:
            self.logger.info(subscribe_response)

        if subscribe_response is not None and subscribe_response.subscribed:
            await self.subscribe_to_event(Events.KlineHistorical)
            if await self.client_instance.wait_for_event(
                lambda: Events.KlineHistorical in self.session_data
            ):
                klines = self.session_data.get(Events.KlineHistorical)
                self.clear_session_data(Events.KlineHistorical)
                if self.verbose:
                    self.logger.info(klines)

                return KlineResponse(**klines)

        return None

    async def stream(
        self,
        callback: Callable,
        symbols: List[str] = ["Step Index"],
        data_mode: DataMode = DataMode.TICK,
        time_frame: Optional[TimeFrame] = TimeFrame.CURRENT,
    ):
        """
        Subscribe to realtime Tick and Bar Data
        """
        if data_mode == DataMode.TICK and time_frame != TimeFrame.CURRENT:
            time_frame = TimeFrame.CURRENT
        else:
            if data_mode == DataMode.BAR and time_frame == TimeFrame.CURRENT:
                time_frame = TimeFrame.M1

        symbols_data = []
        for symbol in symbols:
            symbols_data.append(
                SymbolMarketData(
                    symbol=symbol,
                    time_frame=time_frame,
                    mode=data_mode if data_mode == DataMode.TICK else DataMode.BAR,
                )
            )

        subscribe_request = SubscribeRequest(symbols_data=symbols_data)
        selected_event = (
            Events.KlineSubscribeTick
            if data_mode == DataMode.TICK
            else Events.KlineSubscribeBar
        )

        await self.client_instance.subscribe_to_server(selected_event, callback)
        await self.client_instance.publish(
            selected_event, subscribe_request.model_dump_json()
        )

        try:
            await asyncio.Event().wait()
        except KeyboardInterrupt:
            if self.logger:
                self.logger.info("Closing Stream...")

        return None

    def run(self, tasks: list[Callable]):
        """
        Runs the specified tasks.

        Args:
            tasks (list[Callable]): The list of tasks to run.
        """
        asyncio.run(self._run(tasks))

    async def _run(self, tasks: list[Callable]):
        """
        Internal method to run the specified tasks.

        Args:
            tasks (list[Callable]): The list of tasks to run.
        """
        await self.connect()
        await asyncio.gather(*[task() for task in tasks])
        # try:
        #     await asyncio.Event().wait()
        # except KeyboardInterrupt:
        #     if self.logger:
        #         self.logger.info("Shutting down...")

