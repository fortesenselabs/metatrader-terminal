from fastapi import APIRouter, Query
from typing import Optional, List
from application.lib import MetaTraderDataProcessor
from application.config import Settings, AppLogger
from application.utils import get_server_time
from application.models import (
    PingMessage,
    ServerTimeResponse,
    TickInfoResponse,
    AccountInfoResponse,
    ExchangeInfoResponse,
    OpenOrdersResponse,
    OrderResponse,
    CancelOrderRequest,
    CreateOrderRequest,
    SubscribeRequest,
    SubscribeResponse,
    SymbolMarketData,
    Permission,
)
from application.services import (
    ExchangeInfoService,
    OrderService,
    KlineService,
    AccountService,
)
from application.models.enum_types import TimeFrame, DataMode

# Create an APIRouter instance
rest_router = APIRouter(tags=["API"])


class RestRouter:
    def __init__(self, logger: AppLogger, processor: MetaTraderDataProcessor):
        self.logger = logger
        self.processor = processor

        # Services
        self.exchange_info_service = ExchangeInfoService(logger, processor)
        self.order_service = OrderService(logger, processor)
        self.kline_service = KlineService(logger, processor)
        self.account_service = AccountService(logger, processor)

        # Add routes
        self.add_routes()

    def add_routes(self):
        rest_router.add_api_route("/ping", self.ping_server, response_model=PingMessage)
        rest_router.add_api_route(
            "/time", self.fetch_server_time, response_model=ServerTimeResponse
        )
        rest_router.add_api_route(
            "/account", self.get_account_info, response_model=AccountInfoResponse
        )
        rest_router.add_api_route(
            "/exchangeInfo",
            self.get_exchange_info,
            response_model=ExchangeInfoResponse,
            methods=["GET"],
        )
        rest_router.add_api_route(
            "/subscribe",
            self.subscribe,
            response_model=SubscribeResponse,
            methods=["GET"],
        )
        rest_router.add_api_route(
            "/tick",
            self.get_tick_info,
            response_model=TickInfoResponse,
            methods=["GET"],
        )
        rest_router.add_api_route(
            "/order", self.create_order, response_model=OrderResponse, methods=["POST"]
        )
        rest_router.add_api_route(
            "/order",
            self.cancel_order,
            response_model=OrderResponse,
            methods=["DELETE"],
        )
        rest_router.add_api_route(
            "/openOrders",
            self.cancel_open_orders,
            response_model=OpenOrdersResponse,
            methods=["DELETE"],
        )

    async def ping_server(self):
        response = {"message": "MetaTrader 5 API Server"}
        return PingMessage(**response)

    async def fetch_server_time(self):
        """
        Retrieves the current server time in multiple formats.

        Returns:
            ServerTimeResponse: Current server time with timezone and Unix timestamp.
        """
        response = get_server_time()
        response.server_time = response.unix_timestamp
        return response

    async def get_account_info(self):
        """
        Retrieves information about the connected account.

        Returns:
            Account information in JSON format.
        """
        account_info = await self.account_service.get_account_info()
        return account_info

    async def get_exchange_info(
        self,
        symbol: Optional[str] = Query(None),
        symbols: Optional[List[str]] = Query(None),
        permissions: Optional[List[Permission]] = Query(None, alias="permissions[]"),
    ):
        """
        Retrieve current exchange trading rules and symbol information.

        - No parameters: Get all exchange information.
        - With 'symbol': Filter by a specific symbol.
        - With 'symbols': Filter by multiple symbols.
        - With 'permissions': Filter by specific permissions.

        Examples:
        - No parameter: `curl -X GET "http://127.0.0.1:8000/api/exchangeInfo"`
        - Filter by symbol: `curl -X GET "http://127.0.0.1:8000/api/exchangeInfo?symbol=Step Index"`
        - Filter by symbols: `curl -X GET "http://127.0.0.1:8000/api/exchangeInfo?symbols=EURUSD,USDJPY"`
        - Filter by permissions: `curl -X GET "http://127.0.0.1:8000/api/exchangeInfo?permissions=MARGIN,LEVERAGED"`
        """
        self.logger.info(symbol, symbols, permissions)
        exchange_info = await self.exchange_info_service.get_exchange_info(
            symbol, symbols, permissions
        )
        return exchange_info

    async def subscribe(self, symbol: str):
        """
        Subscribe to tick event data
        """
        request: List[SymbolMarketData] = [
            SymbolMarketData(
                symbol=symbol, time_frame=TimeFrame.CURRENT, mode=DataMode.TICK
            )
        ]
        response = await self.kline_service.subscribe(
            SubscribeRequest(symbols_data=request)
        )
        return response

    async def get_tick_info(self, symbol: str):
        tick_info = await self.kline_service.get_tick_data(symbol)
        return tick_info

    async def create_order(self, order_request: CreateOrderRequest):
        order_info = await self.order_service.create_order(order_request, False)
        return order_info

    async def cancel_order(self, order_request: CancelOrderRequest):
        """
        Cancel an order.
        If the symbol and the order ID is known.
        Intended for non-active orders i.e orders that have not been trigger yet.
        """
        open_orders_info = await self.order_service.close_order(order_request)
        return open_orders_info

    async def cancel_open_orders(self, symbol: str):
        """
        Cancel all active orders on a symbol.
        If just the symbol is known
        Intended for active orders i.e orders that have been trigger otherwise known as positions.
        """
        open_orders_info = await self.order_service.close_open_orders(symbol)
        return open_orders_info


def get_rest_router(logger: AppLogger, processor: MetaTraderDataProcessor) -> APIRouter:
    router_instance = RestRouter(logger, processor)
    return rest_router


# TODO: to be fixed later
# @rest_router.post("/order/test", response_model=OrderResponse)
# async def create_test_order(order_request: CreateOrderRequest):
#     order_info = await order_service.create_order(order_request, True)
#     return order_info
