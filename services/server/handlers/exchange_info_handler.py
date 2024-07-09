import asyncio
from typing import List, Dict, Optional
from models import (
    DWXClientParams,
    RateLimit,
    Symbol,
    SymbolData,
    Permission,
    ExchangeInfoResponse,
    OrderType,
)
from internal import SocketIOServerClient
from utils import Logger, get_server_time
from .base_handler import BaseHandler

RATE_LIMIT = RateLimit(
    rateLimitType="REQUEST_WEIGHT",
    interval="MINUTE",
    intervalNum=1,
    limit=6000,
    count=2,
)


class ExchangeInfoHandler(BaseHandler):
    """
    Handler class for managing exchange information.

    Args:
        dwx_client_params (DWXClientParams): Parameters for DWX client.
        pubsub_instance (SocketIOServerClient): Instance of the Socket.IO server client.
    """

    def __init__(
        self,
        dwx_client_params: DWXClientParams,
        pubsub_instance: SocketIOServerClient,
    ):
        super().__init__(dwx_client_params, pubsub_instance)
        self.logger = Logger(name=__class__.__name__)
        self.symbols_data: Dict[int, SymbolData] = {}

    def on_symbols_data(self, symbol_id, symbol_data):
        self.symbols_data[symbol_id] = SymbolData(**symbol_data)
        self.logger.info(
            f"on_symbols_data: symbol_id={symbol_id}, symbol_data={symbol_data}"
        )

    async def get_exchange_info(
        self,
        symbol: Optional[str] = None,
        symbols: Optional[List[str]] = None,
        permissions: Optional[List[Permission]] = None,
    ) -> ExchangeInfoResponse:
        """
        Retrieves exchange information.

        Args:
            symbol (Optional[str]): Specific symbol to retrieve information for.
            symbols (Optional[List[str]]): List of symbols to retrieve information for.
            permissions (Optional[List[Permission]]): List of permissions to filter symbols.

        Returns:
            ExchangeInfoResponse: An object containing exchange information.
        """
        # Mock data for demonstration
        get_time = get_server_time()
        timezone = get_time.timezone
        serverTime = get_time.unix_timestamp
        rateLimits = []  # Add rate limits if available
        exchangeFilters = []  # Add exchange filters if available

        active_symbols = await self.get_active_symbols()

        symbols = []
        for active_symbol in active_symbols:
            symbol = Symbol(
                symbol=active_symbol.symbol,
                status="TRADING",
                baseAsset=active_symbol.symbol,
                baseAssetPrecision=8,
                quoteAsset=active_symbol.currency_base,
                quoteAssetPrecision=8,
                baseCommissionPrecision=8,
                quoteCommissionPrecision=8,
                orderTypes=OrderType.export_all(),
                icebergAllowed=True,
                ocoAllowed=True,
                otoAllowed=True,
                quoteOrderQtyMarketAllowed=True,
                allowTrailingStop=False,
                cancelReplaceAllowed=False,
                isSpotTradingAllowed=True,
                isMarginTradingAllowed=True,
                filters=[],
                permissions=Permission.export_all(),
                permissionSets=[Permission.export_all()],
                defaultSelfTradePreventionMode="NONE",
                allowedSelfTradePreventionModes=["NONE"],
            )
            symbols.append(symbol)

        sors_data = [{"baseAsset": "Step Index", "symbols": ["Step Index"]}]

        return ExchangeInfoResponse(
            timezone=timezone,
            server_time=serverTime,
            rate_limits=rateLimits,
            exchange_filters=exchangeFilters,
            symbols=symbols,
            sors=sors_data,
        )

    async def get_active_symbols(self, symbol: str = "") -> List[SymbolData]:
        """
        Retrieves active symbols.

        Args:
            symbol (str): Specific symbol to retrieve information for. Defaults to "".

        Returns:
            List[SymbolData]: A list of active symbols.
        """
        self.dwx_client.get_active_symbols(symbol)
        await asyncio.sleep(0.5)

        if len(self.dwx_client.symbols_data) > 0 and len(self.symbols_data) == 0:
            for symbol_id, symbol_data in self.dwx_client.symbols_data.items():
                self.symbols_data[symbol_id] = SymbolData(**symbol_data)

        if len(symbol) > 0:
            return [
                data for data in self.symbols_data.values() if data.symbol == symbol
            ]

        return list(self.symbols_data.values())
