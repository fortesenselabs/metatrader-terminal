from typing import Callable, Optional
from handlers import ExchangeInfoHandler, OrderHandler, AccountHandler, KlineHandler
from models import (
    Events,
    DWXClientParams,
    CreateOrderRequest,
    CancelOrderRequest,
    ModifyOrderRequest,
    OrderResponse,
    ExchangeInfoResponse,
    AccountInfoResponse,
    SubscribeRequest,
    SubscribeResponse,
    TimeFrame,
    DataMode,
    HistoricalKlineRequest,
)
from utils import Logger
from internal import SocketIOServerClient


class RequestHandler:
    """
    Class for managing request handlers in a Socket.IO server.

    Attributes:
        server_instance (SocketIOServerClient): Instance of the SocketIOServerClient connected to the server.
        order_handler (OrderHandler): Handler instance for order-related operations.
        exchange_info_handler (ExchangeInfoHandler): Handler instance for exchange information.
        account_handler (AccountHandler): Handler instance for account-related operations.
        kline_handler (KlineHandler): Handler instance for kline data operations.
        connected_clients (set): Set of currently connected clients.
    """

    def __init__(
        self, dwx_client_params: DWXClientParams, server_instance: SocketIOServerClient
    ) -> None:
        """
        Initializes the RequestHandler with a SocketIOServerClient instance.

        Args:
            dwx_client_params (DWXClientParams): Parameters for the DWX client.
            server_instance (SocketIOServerClient): Instance of the SocketIOServerClient connected to the server.
        """
        self.logger = Logger(name=__class__.__name__)
        self.server_instance = server_instance
        self.order_handler = OrderHandler(dwx_client_params, self.server_instance)
        self.exchange_info_handler = ExchangeInfoHandler(
            dwx_client_params, self.server_instance
        )
        self.account_handler = AccountHandler(
            dwx_client_params, self.server_instance, self.exchange_info_handler
        )
        self.kline_handler = KlineHandler(dwx_client_params, self.server_instance)
        self.connected_clients = set()

    @classmethod
    async def setup_event_handlers(
        cls, dwx_client_params: DWXClientParams, server_instance: SocketIOServerClient
    ) -> None:
        """
        Sets up event handlers for the Socket.IO server.

        Args:
            dwx_client_params (DWXClientParams): Parameters for the DWX client.
            server_instance (SocketIOServerClient): Instance of the SocketIOServerClient connected to the server.
        """
        request_handler = cls(dwx_client_params, server_instance)

        # Exchange and Account Info
        await request_handler.register_handler(
            Events.ExchangeInfo, request_handler.get_exchange_info_handler
        )
        await request_handler.register_handler(
            Events.Account, request_handler.get_account_handler
        )

        # Orders
        await request_handler.register_handler(
            Events.CreateOrder, request_handler.create_order_handler
        )
        await request_handler.register_handler(
            Events.CloseOrder, request_handler.close_order_handler
        )
        await request_handler.register_handler(
            Events.GetOpenOrders, request_handler.get_open_orders_handler
        )
        await request_handler.register_handler(
            Events.ModifyOrder, request_handler.modify_order_handler
        )

        # Kline
        await request_handler.register_handler(
            Events.KlineSubscribeTick, request_handler.add_kline_tick_subscriber
        )
        await request_handler.register_handler(
            Events.KlineSubscribeBar, request_handler.add_kline_bar_subscriber
        )
        await request_handler.register_handler(
            Events.KlineHistorical, request_handler.get_historical_kline_data
        )

        # Add more event registrations as needed
        request_handler.logger.info("Event handlers setup completed.")

    async def register_handler(self, event: str, handler: Callable) -> None:
        """
        Registers a request handler for a specific event.

        Args:
            event (str): The event name.
            handler (Callable): The handler function to be called when the event is received.
        """
        try:
            await self.server_instance.subscribe_to_client(event, handler)
            self.logger.info(f"Registered handler for '{event}'")
        except Exception as e:
            self.logger.error(f"Failed to register handler for '{event}': {e}")
            raise

    async def get_open_orders_handler(
        self, sid: str, data: dict
    ) -> Optional[OrderResponse]:
        """
        Handler function for fetching open orders.

        Args:
            sid (str): Socket.IO session ID.
            data (dict): Data containing request details.

        Returns:
            Optional[OrderResponse]: Order information if successful, None otherwise.
        """
        try:
            orders = await self.order_handler.get_open_orders()
            await self.server_instance.publish(
                Events.GetOpenOrders, orders.model_dump_json()
            )
            return orders
        except Exception as e:
            self.logger.error(f"Error fetching open orders: {e}")
            return None

    async def create_order_handler(
        self, sid: str, data: dict
    ) -> Optional[OrderResponse]:
        """
        Handler function for creating an order.

        Args:
            sid (str): Socket.IO session ID.
            data (dict): Data containing order creation request details.

        Returns:
            Optional[OrderResponse]: Order information if successful, None otherwise.
        """
        try:
            order_request = CreateOrderRequest(**data)
            order_info = await self.order_handler.create_order(order_request, False)
            return order_info
        except Exception as e:
            self.logger.error(f"Error creating order: {e}")
            return None

    async def close_order_handler(
        self, sid: str, data: dict
    ) -> Optional[OrderResponse]:
        """
        Handler function for closing an order.

        Args:
            sid (str): Socket.IO session ID.
            data (dict): Data containing order cancellation request details.

        Returns:
            Optional[OrderResponse]: Order information if successful, None otherwise.
        """
        try:
            order_request = CancelOrderRequest(**data)
            order_info = await self.order_handler.close_order(order_request, False)
            return order_info
        except Exception as e:
            self.logger.error(f"Error closing order: {e}")
            return None

    async def modify_order_handler(
        self, sid: str, data: dict
    ) -> Optional[OrderResponse]:
        """
        Handler function for modifying open orders.

        Args:
            sid (str): Socket.IO session ID.
            data (dict): Data containing order modification request details.

        Returns:
            Optional[OrderResponse]: Order information if successful, None otherwise.
        """
        try:
            order_request = ModifyOrderRequest(**data)
            order = await self.order_handler.modify_order(order_request, False)
            return order
        except Exception as e:
            self.logger.error(f"Error modifying open order: {e}")
            return None

    async def get_exchange_info_handler(
        self, sid: str, data: dict
    ) -> Optional[ExchangeInfoResponse]:
        """
        Handler function for fetching exchange information.

        Args:
            sid (str): Socket.IO session ID.
            data (dict): Data containing request details.

        Returns:
            Optional[ExchangeInfoResponse]: Exchange information if successful, None otherwise.
        """
        try:
            exchange_info = await self.exchange_info_handler.get_exchange_info()
            await self.server_instance.publish(
                Events.ExchangeInfo, exchange_info.model_dump_json()
            )
            return exchange_info
        except Exception as e:
            self.logger.error(f"Error fetching exchange info: {e}")
            return None

    async def get_account_handler(
        self, sid: str, data: dict
    ) -> Optional[AccountInfoResponse]:
        """
        Handler function for fetching account information.

        Args:
            sid (str): Socket.IO session ID.
            data (dict): Data containing request details.

        Returns:
            Optional[AccountInfoResponse]: Account information if successful, None otherwise.
        """
        try:
            account_info = await self.account_handler.get_account()
            await self.server_instance.publish(
                Events.Account, account_info.model_dump_json()
            )
            return account_info
        except Exception as e:
            self.logger.error(f"Error fetching account info: {e}")
            return None

    async def add_kline_tick_subscriber(
        self, sid: str, data: dict
    ) -> SubscribeResponse:
        """
        Adds a new subscriber for kline tick data.

        Args:
            sid (str): Socket.IO session ID.
            data (dict): Data containing subscription details.

        Returns:
            SubscribeResponse: Subscription response.
        """
        subscribe_request = SubscribeRequest(**data)
        for symbol in subscribe_request.symbols_data:
            symbol.time_frame = TimeFrame.CURRENT
            symbol.mode = DataMode.TICK

        sub_response = await self.kline_handler.subscribe(subscribe_request)
        if sub_response.subscribed:
            self.logger.info(
                f"{sid} added to kline tick subscribers => {sub_response.message} | {sub_response.subscribed} | {sub_response.all}"
            )
            self.connected_clients.add(sid)

        await self.server_instance.publish(
            Events.KlineSubscribeTick, sub_response.model_dump_json()
        )
        return sub_response

    async def add_kline_bar_subscriber(self, sid: str, data: dict) -> SubscribeResponse:
        """
        Adds a new subscriber for kline bar data.

        Args:
            sid (str): Socket.IO session ID.
            data (dict): Data containing subscription details.

        Returns:
            SubscribeResponse: Subscription response.
        """
        subscribe_request = SubscribeRequest(**data)
        for symbol in subscribe_request.symbols_data:
            if symbol.time_frame == TimeFrame.CURRENT:
                symbol.time_frame = TimeFrame.M1

            symbol.mode = DataMode.BAR

        sub_response = await self.kline_handler.subscribe(subscribe_request)
        if sub_response.subscribed:
            self.logger.info(
                f"{sid} added to kline bar subscribers => {sub_response.message} | {sub_response.subscribed} | {sub_response.all}"
            )
            self.connected_clients.add(sid)

        await self.server_instance.publish(
            Events.KlineSubscribeBar, sub_response.model_dump_json()
        )
        return sub_response

    async def get_historical_kline_data(
        self, sid: str, data: dict
    ) -> SubscribeResponse:
        """
        Adds a new subscriber for historical kline bar data.

        Args:
            sid (str): Socket.IO session ID.
            data (dict): Data containing subscription details.

        Returns:
            SubscribeResponse: Subscription response.
        """
        kline_request = HistoricalKlineRequest(**data)
        sub_response = await self.kline_handler.get_historic_data(kline_request)
        if sub_response.subscribed:
            self.logger.info(
                f"{sid} added to historical kline bar subscribers => {sub_response.message} | {sub_response.subscribed} | {sub_response.all}"
            )
        await self.server_instance.publish(
            Events.KlineHistorical, sub_response.model_dump_json()
        )
        return sub_response
