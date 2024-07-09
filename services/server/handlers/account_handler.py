from typing import List, Dict, Optional
from models import (
    DWXClientParams,
    AccountInfoResponse,
    AccountType,
    Permission,
    SymbolBalance,
)
from internal import SocketIOServerClient
from utils import Logger, get_server_time
from .base_handler import BaseHandler
from .exchange_info_handler import ExchangeInfoHandler


class AccountHandler(BaseHandler):
    """
    Handler class for managing account-related operations.

    Args:
        dwx_client_params (DWXClientParams): Parameters for DWX client.
        pubsub_instance (SocketIOServerClient): Instance of the Socket.IO server client.
        exchange_info (ExchangeInfoHandler): Handler for exchange information.
    """

    def __init__(
        self,
        dwx_client_params: DWXClientParams,
        pubsub_instance: SocketIOServerClient,
        exchange_info: ExchangeInfoHandler,
    ):
        super().__init__(dwx_client_params, pubsub_instance)
        self.logger = Logger(name=__class__.__name__)
        self.account_info: Optional[Dict] = None
        self.exchange_info: Optional[ExchangeInfoHandler] = exchange_info

    def on_historic_trades(self):
        self.logger.info(f"historic_trades: {len(self.dwx_client.historic_trades)}")
        self.historic_trades = self.dwx_client.historic_trades

    async def get_balances(self) -> List[SymbolBalance]:
        """
        Retrieves the balance information for the account.

        Returns:
            List[SymbolBalance]: A list of balances for different symbols.
        """
        balances = [
            {
                "symbol": self.account_info["currency"],
                "free": f"{self.account_info['free_margin']}",
                "locked": f"{self.account_info['equity'] - self.account_info['free_margin']}",  # Calculate Locked balance
            },
        ]

        active_symbols = await self.exchange_info.get_active_symbols()
        for symbol_data in active_symbols:
            balance = {
                "symbol": symbol_data.symbol,
                "free": "0",
                "locked": "0",
            }
            balances.append(balance)

        return balances

    async def get_account(self) -> AccountInfoResponse:
        """
        Retrieves account information and constructs an AccountInfoResponse object.

        Returns:
            AccountInfoResponse: An object containing account information.
        """
        self.account_info = self.dwx_client.account_info

        self.account_info["uid"] = self.account_info["number"]
        self.account_info["can_trade"] = True
        self.account_info["can_withdraw"] = False
        self.account_info["can_deposit"] = False

        # Get current time in Unix time and ensure it is uint64
        self.account_info["update_time"] = get_server_time().unix_timestamp

        self.account_info["account_type"] = AccountType.HEDGING
        self.account_info["permissions"] = Permission.export_all()

        self.account_info["balances"] = await self.get_balances()

        return AccountInfoResponse(**self.account_info)

    async def get_trades(self):
        """
        Placeholder method for retrieving trades.
        """
        return

    async def get_historical_trades(self):
        """
        Placeholder method for retrieving historical trades.
        """
        return
