import asyncio
from typing import List, Dict, Optional
from models import (
    DWXClientParams,
    Events,
    OrderResponse,
    CreateOrderRequest,
    CancelOrderRequest,
    ModifyOrderRequest,
    MTOrderType,
    SideType,
    NewOrderEvent,
    MultiOrdersResponse,
)
from internal import SocketIOServerClient
from utils import Logger, date_to_timestamp
from .base_handler import BaseHandler


class OrderHandler(BaseHandler):
    """
    Handler class for managing orders with MetaTrader.

    This class provides methods for handling order events, retrieving all orders, and retrieving
    open orders. Specific implementations for these functionalities should be provided by overriding
    the corresponding placeholder methods.

    Attributes:
        logger (Logger): Instance for logging information and errors.
        dwx_client_params (DWXClientParams): Parameters used to initialize the DWXClient.
    """

    def __init__(
        self,
        dwx_client_params: DWXClientParams,
        pubsub_instance: SocketIOServerClient,
    ):
        """
        Initializes the OrderHandler with DWXClient parameters and a Pub/Sub client.

        Args:
            dwx_client_params (DWXClientParams): An object containing parameters required to
                                                 initialize a DWXClient instance.
            pubsub_instance (SocketIOServerClient): The client for Pub/Sub messaging.
        """
        super().__init__(dwx_client_params, pubsub_instance)
        self.logger = Logger(name=__class__.__name__)

    async def _handle_create_order_event(self, latest_order):
        """
        Handles the event when a new order is created.

        Args:
            latest_order (dict): The latest order information.
        """
        try:
            if latest_order["event_type"] == "Order:Created":
                new_order = await self.create_order(
                    is_order_executed=True, mt_executed_order=latest_order
                )
                await self.publish_to_subscriber(
                    Events.CreateOrder, new_order.model_dump_json()
                )
        except KeyError:
            pass

    async def _handle_close_order_event(self, latest_order):
        """
        Handles the event when an order is closed.

        Args:
            latest_order (dict): The latest order information.
        """
        try:
            if latest_order["event_type"] == "Order:Removed":
                new_order = await self.close_order(
                    is_order_executed=True, mt_executed_order=latest_order
                )
                await self.publish_to_subscriber(
                    Events.CloseOrder, new_order.model_dump_json()
                )
        except KeyError:
            pass

    def on_order_event(self):
        """
        Handles outgoing/incoming order events.

        This method receives order event data and performs actions based on the event type.
        """
        self.logger.info(
            f"on_order_event. open_orders: {len(self.dwx_client.open_orders)} open orders"
        )

        self.logger.info(
            f"on_order_event. closed_orders: {len(self.dwx_client.closed_orders)} closed orders"
        )

        payload = {
            "open_orders_len": len(self.dwx_client.open_orders),
            "closed_orders_len": len(self.dwx_client.closed_orders),
            "open_orders": self.dwx_client.open_orders,
            "closed_orders": self.dwx_client.closed_orders,
        }

        async def main():
            if len(self.dwx_client.open_orders) > 0:
                latest_order = list(self.dwx_client.open_orders.values())[-1]
                self.logger.info(f"latest_opened_order: {latest_order}")
                await self._handle_create_order_event(latest_order)

            if len(self.dwx_client.closed_orders) > 0:
                latest_order = self.dwx_client.closed_orders[-1]
                self.logger.info(f"latest_closed_order: {latest_order}")
                await self._handle_close_order_event(latest_order)

            await self.publish_to_subscriber(Events.Order, payload)

        asyncio.run(main())

    async def publish_to_subscriber(self, event_type, payload):
        """
        Publishes an event to the subscriber.

        Args:
            event_type (str): The type of event to publish.
            payload (dict): The data to publish with the event.
        """
        await self.pubsub.publish(event_type, payload)

    async def get_orders(self):
        """
        Retrieves all orders from MetaTrader.

        This method should be overridden to implement the actual logic for fetching all orders.
        It could involve creating a DWXClient instance and using its methods to retrieve orders.

        Raises:
            NotImplementedError: This method is intended to be overridden.
        """
        raise NotImplementedError("get_orders must be implemented by a subclass")

    async def get_open_orders(self) -> MultiOrdersResponse:
        """
        Retrieves all open orders from MetaTrader.

        This method should be overridden to implement the logic for fetching open orders.

        Returns:
            MultiOrdersResponse: The response containing open orders.
        """
        open_orders = []
        for order_id, order in self.dwx_client.open_orders.items():
            response = {
                "order_id": str(order_id),
                "symbol": order["symbol"],
                "time": date_to_timestamp(order["open_time"]),
                "price": str(order["open_price"]),
                "executed_qty": str(order["lots"]),
                "side": SideType.from_string(str(order["type"]).upper()),
                "stop_loss": str(order["SL"]),
                "take_profit": str(order["TP"]),
            }
            open_orders.append(OrderResponse(**response))

        return MultiOrdersResponse(orders=open_orders)

    async def create_order(
        self,
        order_request: Optional[CreateOrderRequest] = None,
        is_order_executed: bool = False,
        mt_executed_order: Optional[Dict] = None,
    ) -> OrderResponse:
        """
        Creates a new order.

        Args:
            order_request (CreateOrderRequest): The request object containing order details.
            is_order_executed (bool): Flag indicating if the order is already executed.
            mt_executed_order (dict): The executed order details.

        Returns:
            OrderResponse: The response object containing details of the created order.
        """
        if is_order_executed:
            response = {
                "order_id": str(mt_executed_order["order_id"]),
                "symbol": mt_executed_order["symbol"],
                "time": date_to_timestamp(mt_executed_order["open_time"]),
                "price": str(mt_executed_order["open_price"]),
                "executed_qty": str(mt_executed_order["lots"]),
                "side": SideType.from_string(str(mt_executed_order["type"]).upper()),
                "stop_loss": str(mt_executed_order["SL"]),
                "take_profit": str(mt_executed_order["TP"]),
            }

            return OrderResponse(**response)

        if order_request is not None:
            self.dwx_client.open_order(
                symbol=order_request.symbol,
                order_type=MTOrderType.get_mt_order_type(
                    order_request.side, order_request.type
                ).value,
                price=float(order_request.price) or 0,
                lots=float(order_request.quantity) or 0,
                stop_loss=float(order_request.stop_loss_price) or 0,
                take_profit=float(order_request.take_profit_price) or 0,
            )

    async def close_order(
        self,
        order_request: Optional[CancelOrderRequest] = None,
        is_order_executed: bool = False,
        mt_executed_order: Optional[Dict] = None,
    ) -> OrderResponse:
        """
        Closes an existing order.

        Args:
            order_request (CancelOrderRequest): The request object containing order details.
            is_order_executed (bool): Flag indicating if the order is already executed.
            mt_executed_order (dict): The executed order details.

        Returns:
            OrderResponse: The response object containing details of the closed order.
        """
        if is_order_executed:
            response = {
                "order_id": str(mt_executed_order["order_id"]),
                "symbol": mt_executed_order["symbol"],
                "time": date_to_timestamp(mt_executed_order["open_time"]),
                "price": str(mt_executed_order["open_price"]),
                "executed_qty": str(mt_executed_order["lots"]),
                "side": SideType.from_string(str(mt_executed_order["type"]).upper()),
                "stop_loss": str(mt_executed_order["SL"]),
                "take_profit": str(mt_executed_order["TP"]),
            }

            return OrderResponse(**response)

        await asyncio.sleep(5)  # wait for sometime before closing orders,
        # the async nature of the server seems to make this run faster than it should.
        opened_orders = await self.get_open_orders()
        if opened_orders.orders is not None and len(opened_orders.orders) > 0:
            if order_request.close_all:
                self.dwx_client.close_all_orders()
            elif order_request.symbol is not None:
                self.dwx_client.close_orders_by_symbol(symbol=order_request.symbol)
            elif order_request.magic_id is not None:
                self.dwx_client.close_orders_by_magic(magic=order_request.magic_id)
            elif order_request.order_id is not None:
                self.dwx_client.close_order(
                    ticket=order_request.order_id, lots=order_request.quantity
                )
            else:
                self.dwx_client.close_all_orders()

    async def modify_order(
        self,
        order_request: Optional[ModifyOrderRequest] = None,
        is_order_executed: bool = False,
        mt_executed_order: Optional[Dict] = None,
    ) -> OrderResponse:
        """
        Modifies an existing order.

        Args:
            order_request (ModifyOrderRequest): The request object containing order details.
            is_order_executed (bool): Flag indicating if the order is already executed.
            mt_executed_order (dict): The executed order details.

        Returns:
            OrderResponse: The response object containing details of the modified order.
        """
        if is_order_executed:
            response = {
                "order_id": str(mt_executed_order["order_id"]),
                "symbol": mt_executed_order["symbol"],
                "time": date_to_timestamp(mt_executed_order["open_time"]),
                "price": str(mt_executed_order["open_price"]),
                "executed_qty": str(mt_executed_order["lots"]),
                "side": SideType.from_string(str(mt_executed_order["type"]).upper()),
                "stop_loss": str(mt_executed_order["SL"]),
                "take_profit": str(mt_executed_order["TP"]),
            }

            return OrderResponse(**response)

        await asyncio.sleep(1)
        opened_orders = await self.get_open_orders()
        if len(opened_orders.orders) > 0:
            self.dwx_client.modify_order(
                ticket=order_request.order_id,
                price=order_request.price,
                stop_loss=order_request.stop_loss_price,
                take_profit=order_request.take_profit_price,
            )

    async def search_orders_by_magic(self, magic_id: int) -> List[NewOrderEvent]:
        """
        Searches for orders with a specific magic id.

        Args:
            magic_id (int): The magic id to search for.

        Returns:
            List[NewOrderEvent]: A list of NewOrderEvent instances that match the magic id.
        """
        open_orders = self.dwx_client.open_orders

        if open_orders:
            matching_orders = [
                NewOrderEvent(
                    ticket_id=order_data["ticket_id"],
                    magic=order_data["magic"],
                    symbol=order_data["symbol"],
                    lots=order_data["lots"],
                    type=order_data["type"],
                    open_price=order_data["open_price"],
                    open_time=order_data["open_time"],
                    sl=order_data["sl"],
                    tp=order_data["tp"],
                    pnl=order_data["pnl"],
                    swap=order_data["swap"],
                    comment=order_data["comment"],
                )
                for order_data in open_orders
                if order_data["magic"] == magic_id
            ]

            return matching_orders

        return []
