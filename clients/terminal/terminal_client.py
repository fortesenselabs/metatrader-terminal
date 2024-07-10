import json
from typing import List, Optional, Union
from .models import (
    Account,
    APIKeyPermission,
    ExchangeInfo,
    CreateOrderRequest,
    CreateOrderResponse,
)
from .utils import current_timestamp
from .request import RequestBuilder
from .base_client import BaseClient, get_api_endpoint


class TerminalClient(BaseClient):
    def __init__(
        self, base_url: str = get_api_endpoint(), user_agent: str = "MetaTrader/python"
    ):
        super().__init__(base_url, user_agent)
        self.time_offset = None

    def ping(self, opts=None):
        request = RequestBuilder("GET", "/api/ping")
        data = self.call_api(request, opts)
        return json.loads(data)

    def get_server_time(self, opts=None):
        request = RequestBuilder("GET", "/api/time")
        data = self.call_api(request, opts)
        return data["server_time"]

    def set_server_time(self, opts=None):
        server_time = self.get_server_time()
        time_offset = current_timestamp() - server_time
        self.time_offset = time_offset
        return time_offset

    def get_server_system_status(self, opts=None):
        request = RequestBuilder("GET", "/api/system/status")
        data = self.call_api(request, opts)
        return json.loads(data)

    #
    # ACCOUNT
    #

    def get_account(self, opts=None) -> Account:
        """
        GetAccount: for getting account info
        """
        request = RequestBuilder("GET", "/api/account")
        response = self.call_api(request, opts)
        return Account(**response.json())

    def get_api_key_permission(self, opts=None) -> APIKeyPermission:
        """
        GetAPIKeyPermission for getting API key permissions
        """
        request = RequestBuilder("GET", "/sapi/v1/account/apiRestrictions")
        response = self.call_api(request, opts)
        return APIKeyPermission(**response.json())

    #
    # Exchange Info
    #

    def get_exchange_info(self, symbols: Optional[Union[List, str]] = None, opts=None):
        params = {}

        if isinstance(symbols, str):
            params["symbol"] = symbols

        if isinstance(symbols, list):
            params["symbols"] = symbols

        request = RequestBuilder("GET", "/api/exchangeInfo")
        request.set_params(params)

        data = self.call_api(request, opts)
        return ExchangeInfo.from_dict(data)

    #
    # REST Events
    #

    def subscribe(self, symbol: str):
        """
        Subscribe to tick event data for a given symbol.
        """
        request = RequestBuilder("GET", "/api/subscribe")
        request.set_params({"symbol": symbol})

        data = self.call_api(request)
        return json.loads(data)

    def get_tick_info(self, symbol: str):
        """
        Get tick info for a given symbol.
        """
        self.subscribe(symbol)

        request = RequestBuilder("GET", "/api/tick")
        request.set_params({"symbol": symbol})

        data = self.call_api(request)
        return json.loads(data)

    def create_order(
        self, order_request: CreateOrderRequest, opts=None
    ) -> CreateOrderResponse:
        """
        Create Order
        """
        request = RequestBuilder("POST", "/api/order")
        request.set_body(order_request.__dict__)

        data = self.call_api(request, opts)
        return CreateOrderResponse(**json.loads(data))
