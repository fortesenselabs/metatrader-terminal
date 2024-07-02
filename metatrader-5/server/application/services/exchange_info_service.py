from typing import Optional, List
from application.config.logger import AppLogger
from application.lib.processor import MetaTraderDataProcessor
from application.models.exchange_info_models import (
    RateLimit,
    ExchangeInfoResponse,
)
from application.models.symbol_models import Symbol
from application.models.enum_types import (
    Permission,
)
from application.models.orders_models import OrderType
from application.utils.utils import get_server_time

RATE_LIMIT = RateLimit(
    rateLimitType="REQUEST_WEIGHT",
    interval="MINUTE",
    intervalNum=1,
    limit=6000,
    count=2,
)


class ExchangeInfoService:
    def __init__(
        self,
        processor: MetaTraderDataProcessor,
    ):
        self.logger = AppLogger(name=__class__.__name__)
        self.processor = processor

    async def get_exchange_info(
        self,
        symbol: Optional[str] = None,
        symbols: Optional[List[str]] = None,
        permissions: Optional[List[Permission]] = None,
    ):
        # Mock data for demonstration
        get_time = get_server_time()
        timezone = get_time.timezone
        serverTime = get_time.unix_timestamp
        rateLimits = []  # Add rate limits if available
        exchangeFilters = []  # Add exchange filters if available

        symbols_data = [
            Symbol(
                symbol="Step Index",
                status="TRADING",
                baseAsset="Step Index",
                baseAssetPrecision=8,
                quoteAsset="USD",
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
        ]
        sors_data = [{"baseAsset": "Step Index", "symbols": ["Step Index"]}]

        return ExchangeInfoResponse(
            timezone=timezone,
            server_time=serverTime,
            rate_limits=rateLimits,
            exchange_filters=exchangeFilters,
            symbols=symbols_data,
            sors=sors_data,
        )
