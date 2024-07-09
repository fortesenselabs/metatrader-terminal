import asyncio
from typing import List, Dict, Optional
from models import (
    DWXClientParams,
    Events,
    OrderResponse,
    CreateOrderRequest,
    CancelOrderRequest,
    MTOrderType,
    SideType,
    NewOrderEvent,
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
        Handle outgoing/incoming order events.

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

    async def get_open_orders(self):
        """
        Retrieves all open orders from MetaTrader.

        Similar to get_orders, this method should be overridden to implement the logic for
        fetching open orders.

        Raises:
            NotImplementedError: This method is intended to be overridden by a subclass.
        """
        raise NotImplementedError("get_open_orders must be implemented by a subclass")

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
                # "time_in_force": mt_executed_order["time_in_force"],
                # "type": "MARKET",
                "side": SideType.from_string(str(mt_executed_order["type"]).upper()),
                # "stop_loss": mt_executed_order["SL"],
                # "take_profit": mt_executed_order["TP"],
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
                # "time_in_force": mt_executed_order["time_in_force"],
                # "type": "MARKET",
                "side": SideType.from_string(str(mt_executed_order["type"]).upper()),
                # "stop_loss": mt_executed_order["SL"],
                # "take_profit": mt_executed_order["TP"],
            }

            return OrderResponse(**response)

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

    async def get_open_orders(self) -> List[OrderResponse]:
        open_orders = self.dwx_client.open_orders
        for order_id, order in open_orders.items():
            pass

        return open_orders

    async def modify_order(self):
        # modify_order
        # self.dwx_client.modify_order()
        return

    async def search_orders_by_magic(self, magic_id: int) -> List[NewOrderEvent]:
        """
        Search for orders with a specific magic id.

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
