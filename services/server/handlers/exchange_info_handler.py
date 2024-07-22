import asyncio
from datetime import datetime
from typing import Callable, List, Dict, Optional
from models import (
    MTClientParams,
    RateLimit,
    Symbol,
    SymbolData,
    Permission,
    ExchangeInfoResponse,
    OrderType,
)
from internal import SocketIOServerClient, MTSocketClient
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
        mt_socket_client (MTSocketClient): Parameters for DWX client.
        pubsub_instance (SocketIOServerClient): Instance of the Socket.IO server client.
    """

    def __init__(
        self,
        mt_client_params: MTClientParams,
        pubsub_instance: SocketIOServerClient,
    ):
        super().__init__(mt_client_params, pubsub_instance)
        self.logger = Logger(name=__class__.__name__)
        self.symbols_data: Dict[int, SymbolData] = {}

    def on_symbols_data(self, symbols_data):
        self.logger.debug(f"on_symbols_data: {symbols_data}")

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
        all_symbols = []

        active_symbols = await self.get_active_symbols()
        if active_symbols is not None:
            for _, active_symbol in active_symbols.items():
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
                all_symbols.append(symbol)

        if symbols is not None and len(symbols) > 0:
            # filter symbols
            pass

        sors_data = [{"baseAsset": "Step Index", "symbols": ["Step Index"]}]

        return ExchangeInfoResponse(
            timezone=timezone,
            server_time=serverTime,
            rate_limits=rateLimits,
            exchange_filters=exchangeFilters,
            symbols=all_symbols,
            sors=sors_data,
        )

    async def get_active_symbols(
        self, symbol: str = ""
    ) -> Optional[Dict[int, SymbolData]]:
        """
        Retrieves active symbols.

        Args:
            symbol (str): Specific symbol to retrieve information for. Defaults to "".

        Returns:
            List[SymbolData]: A list of active symbols.
        """
        active_symbols = self.socket_client.get_active_symbols(symbol)
        if active_symbols is None:
            return None

        for symbol_id, symbol_data in active_symbols.items():
            self.symbols_data[symbol_id] = SymbolData(**symbol_data)

        return self.symbols_data
