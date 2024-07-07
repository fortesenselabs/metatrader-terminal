from typing import Optional, List
from application.config.logger import AppLogger
from application.lib.processor import MetaTraderDataProcessor
from application.models.account_info_models import (
    AccountInfoResponse,
    AccountType,
    Permission,
)
from application.utils import get_server_time
from application.models.orders_models import OrderType
from application.models.symbol_models import (
    Symbol,
    AvailableSymbolsInfoResponse,
    SymbolBalance,
)


class AccountService:
    def __init__(
        self,
        processor: MetaTraderDataProcessor,
    ):
        self.logger = AppLogger(name=__class__.__name__)
        self.processor = processor
        self.account_info: Optional[AccountInfoResponse] = None

    async def get_all_symbols(self) -> AvailableSymbolsInfoResponse:
        active_symbols = self.processor.get_active_symbols()

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

        return AvailableSymbolsInfoResponse(symbols=symbols)

    async def get_symbol_detail(self):
        return

    async def get_all_balances(self) -> List[SymbolBalance]:
        balances = [
            {
                "symbol": self.account_info["currency"],
                "free": f"{self.account_info['free_margin']}",
                "locked": f"{self.account_info['equity'] - self.account_info['free_margin']}",  # Calculate Locked balance
            },
        ]
        balances.extend(self.processor.get_active_symbol_balances())

        return balances

    async def get_account_info(self) -> AccountInfoResponse:
        self.account_info = self.processor.get_account_info()
        self.account_info["uid"] = self.account_info["number"]
        self.account_info["can_trade"] = True
        self.account_info["can_withdraw"] = False
        self.account_info["can_deposit"] = False

        # Get current time in Unix time and ensure it is uint64
        self.account_info["update_time"] = get_server_time().unix_timestamp

        self.account_info["account_type"] = AccountType.HEDGING
        self.account_info["permissions"] = Permission.export_all()

        self.account_info["balances"] = await self.get_all_balances()

        return AccountInfoResponse(**self.account_info)

    async def get_trades(self):
        return

    async def get_historical_trades(self):
        return
