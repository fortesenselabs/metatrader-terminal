from application.config import AppLogger
from application.lib.processor import MetaTraderDataProcessor
from application.models.orders_models import (
    CreateOrderRequest,
    OpenOrdersResponse,
    OrderResponse,
    CancelOrderRequest,
)
from application.models.mt_models import MTOrderType, MTOrderStatus


class OrderService:
    """
    Service class for managing orders with MetaTrader.

    Attributes:
        logger (AppLogger): The logger instance.
        processor (MetaTraderDataProcessor): The MetaTrader data processor instance.
    """

    def __init__(self, processor: MetaTraderDataProcessor):
        """
        Initialize the OrderService with a logger and a MetaTrader data processor.

        Args:
            processor (MetaTraderDataProcessor): The MetaTrader data processor instance.
        """
        self.logger = AppLogger(name=__class__.__name__)
        self.processor = processor

    async def get_orders(self):
        """
        Placeholder for getting all orders.
        """
        pass

    async def get_open_orders(self):
        """
        Placeholder for getting all open orders.
        """
        pass

    async def create_order(
        self, order_request: CreateOrderRequest, is_test: bool
    ) -> OrderResponse:
        """
        Create a new order.

        Args:
            order_request (CreateOrderRequest): The request object containing order details.
            is_test (bool): Flag indicating if the order is a test order.

        Returns:
            OrderResponse: The response object containing order details.
        """
        # TODO: Implement test order functionality
        if is_test:
            return

        mt_order = self.processor.open_order(
            symbol=order_request.symbol,
            order_type=MTOrderType.get_mt_order_type(
                order_request.side, order_request.type
            ),
            price=float(order_request.price) or 0,
            lots=float(order_request.quantity) or 0,
            stop_loss=float(order_request.stop_loss_price) or 0,
            take_profit=float(order_request.take_profit_price) or 0,
        )

        if mt_order is None:
            response = {
                "symbol": order_request.symbol,
                "status": MTOrderStatus.NONE,
                "type": order_request.type,
                "side": order_request.side,
            }
        else:
            response = {
                "order_id": mt_order.ticket_id,
                "symbol": mt_order.symbol,
                "status": mt_order.status.value,
                "price": str(mt_order.price),
                "orig_qty": (
                    str(order_request.quantity)
                    if order_request.quantity is not None
                    else "0"
                ),
                "executed_qty": str(mt_order.lots),
                "time_in_force": mt_order.time_in_force,
                "type": order_request.type,
                "side": order_request.side,
            }

        return OrderResponse(**response)

    async def close_order(self, order_request: CancelOrderRequest) -> OrderResponse:
        """
        Close an existing order.

        Args:
            order_request (CancelOrderRequest): The request object containing order details.

        Returns:
            OrderResponse: The response object containing closed order details.
        """
        mt_order = self.processor.close_order(
            ticket_id=order_request.order_id, symbol=order_request.symbol
        )

        if mt_order is None:
            return OrderResponse(
                order_id=order_request.order_id, symbol=order_request.symbol
            )

        _order = mt_order[0]
        response = OrderResponse(
            order_id=_order.ticket_id,
            symbol=_order.symbol,
            # Uncomment and set appropriate fields if required
            # type=_order.type,
            transact_time=_order.open_time,
            executed_qty=_order.lots,
            orig_qty=_order.lots,
            price=_order.open_price,
        )
        return response

    async def close_open_orders(self, symbol: str) -> OpenOrdersResponse:
        """
        Close all open orders for a given symbol.

        Args:
            symbol (str): The symbol for which to close all open orders.

        Returns:
            OpenOrdersResponse: The response object containing details of closed orders.
        """
        mt_orders = self.processor.close_order(ticket_id="", symbol=symbol)

        if mt_orders is None:
            return OpenOrdersResponse()

        _orders = []
        for mt_order in mt_orders:
            _order = OrderResponse(
                order_id=mt_order.ticket_id,
                symbol=mt_order.symbol,
                # Uncomment and set appropriate fields if required
                # type=mt_order.type,
                transact_time=mt_order.open_time,
                executed_qty=mt_order.lots,
                orig_qty=mt_order.lots,
                price=mt_order.open_price,
            )
            _orders.append(_order)

        return OpenOrdersResponse(orders=_orders)
