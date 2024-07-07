import asyncio
from nats.aio.client import Client as NATS
from models import DWXClientParams, Events
from utils import Logger
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
        self, dwx_client_params: DWXClientParams, pubsub_client_instance: NATS
    ):
        """
        Initializes the OrderHandler with DWXClient parameters and a Pub/Sub client.

        Args:
            dwx_client_params (DWXClientParams): An object containing parameters required to
                                               initialize a DWXClient instance.
            pubsub_client_instance (nats.aio.client.Client): The NATS client for Pub/Sub messaging.
        """
        super().__init__(dwx_client_params, pubsub_client_instance)
        self.logger = Logger(name=__class__.__name__)

    def on_order_event(self):
        """
        Handle incoming order events.

        This method receives order event data and performs actions based on the event type.
        """
        # Implement logic to handle specific order events based on event_data
        self.logger.info(
            f"on_order_event. open_orders: {len(self.dwx_client.open_orders)} open orders"
        )
        # publish to nats
        payload = {"open_orders_len": len(self.dwx_client.open_orders)}

        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        loop.run_until_complete(self.publish_to_subscriber(Events.Order, payload))
        loop.close()

        # try:
        #     # Get the current event loop or create a new one if it doesn't exist
        #     loop = asyncio.get_event_loop()
        # except RuntimeError:
        #     # If there is no current event loop, create a new one
        #     loop = asyncio.new_event_loop()
        #     asyncio.set_event_loop(loop)

        # # Run the coroutine in the event loop
        # loop.call_soon_threadsafe(
        #     asyncio.create_task, self.publish_to_subscriber(Events.Order, payload)
        # )

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
            NotImplementedError: This method is intended to be overridden.
        """
        raise NotImplementedError("get_open_orders must be implemented by a subclass")

    # async def create_order(
    #     self, order_request: CreateOrderRequest, is_test: bool
    # ) -> OrderResponse:
    #     """
    #     Creates a new order.

    #     Args:
    #         order_request (CreateOrderRequest): The request object containing order details.
    #         is_test (bool): Flag indicating if the order is a test order.

    #     Returns:
    #         OrderResponse: The response object containing details of the created order.
    #     """
    #     # TODO: Implement test order functionality
    #     if is_test:
    #         return

    #     mt_order = self.processor.open_order(
    #         symbol=order_request.symbol,
    #         order_type=MTOrderType.get_mt_order_type(
    #             order_request.side, order_request.type
    #         ),
    #         price=float(order_request.price) or 0,
    #         lots=float(order_request.quantity) or 0,
    #         stop_loss=float(order_request.stop_loss_price) or 0,
    #         take_profit=float(order_request.take_profit_price) or 0,
    #     )

    #     if mt_order is None:
    #         response = {
    #             "symbol": order_request.symbol,
    #             "status": MTOrderStatus.NONE,
    #             "type": order_request.type,
    #             "side": order_request.side,
    #         }
    #     else:
    #         response = {
    #             "order_id": mt_order.ticket_id,
    #             "symbol": mt_order.symbol,
    #             "status": mt_order.status.value,
    #             "price": str(mt_order.price),
    #             "orig_qty": (
    #                 str(order_request.quantity)
    #                 if order_request.quantity is not None
    #                 else "0"
    #             ),
    #             "executed_qty": str(mt_order.lots),
    #             "time_in_force": mt_order.time_in_force,
    #             "type": order_request.type,
    #             "side": order_request.side,
    #         }

    #     return OrderResponse(**response)

    # async def close_order(self, order_request: CancelOrderRequest) -> OrderResponse:
    #     """
    #     Closes an existing order.

    #     Args:
    #         order_request (CancelOrderRequest): The request object containing order details.

    #     Returns:
    #         OrderResponse: The response object containing details of the closed order.
    #     """
    #     mt_order = self.processor.close_order(
    #         ticket_id=order_request.order_id, symbol=order_request.symbol
    #     )

    #     if mt_order is None:
    #         return OrderResponse(
    #             order_id=order_request.order_id, symbol=order_request.symbol
    #         )

    #     _order = mt_order[0]
    #     response = OrderResponse(
    #         order_id=_order.ticket_id,
    #         symbol=_order.symbol,
    #         # Uncomment and set appropriate fields if required
    #         # type=_order.type,
    #         transact_time=_order.open_time,
    #         executed_qty=_order.lots,
    #         orig_qty=_order.lots,
    #         price=_order.open_price,
    #     )
    #     return response

    # async def close_open_orders(self, symbol: str) -> OpenOrdersResponse:
    #     """
    #     Closes all open orders for a given symbol.

    #     Args:
    #         symbol (str): The symbol for which to close all open orders.

    #     Returns:
    #         OpenOrdersResponse: The response object containing details of closed orders.
    #     """
    #     mt_orders = self.processor.close_order(ticket_id="", symbol=symbol)

    #     if mt_orders is None:
    #         return OpenOrdersResponse()

    #     _orders = []
    #     for mt_order in mt_orders:
    #         _order = OrderResponse(
    #             order_id=mt_order.ticket_id,
    #             symbol=mt_order.symbol,
    #             # Uncomment and set appropriate fields if required
    #             # type=mt_order.type,
    #             transact_time=mt_order.open_time,
    #             executed_qty=mt_order.lots,
    #             orig_qty=mt_order.lots,
    #             price=mt_order.open_price,
    #         )
    #         _orders.append(_order)

    #     return OpenOrdersResponse(orders=_orders)
