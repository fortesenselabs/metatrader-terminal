import json
import logging
import sys

from typing import Callable, Optional, List
from http.client import HTTPResponse
from urllib.parse import urljoin

import requests
from .exceptions import MetaTraderServerAPIException
from .request import RequestBuilder

BASE_API_URL = "http://localhost:8000"


def get_api_endpoint() -> str:
    return BASE_API_URL


class BaseClient:
    def __init__(
        self, base_url: str = get_api_endpoint(), user_agent: str = "MetaTrader/python"
    ):
        self.base_url = base_url
        self.user_agent = user_agent
        self.http_client = requests.Session()
        self.logger = logging.getLogger("MetaTrader-python")
        handler = logging.StreamHandler(sys.stderr)
        handler.setFormatter(
            logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
        )
        self.logger.addHandler(handler)
        self.logger.setLevel(logging.DEBUG)
        self.debug = False
        self.time_offset = 0
        self.do: Optional[Callable[[requests.Request], HTTPResponse]] = None

    def debug_log(self, message: str, *args):
        if self.debug:
            self.logger.debug(message, *args)

    def parse_request(
        self,
        r: "RequestBuilder",
        opts: Optional[List[Callable[["RequestBuilder"], None]]] = None,
    ) -> None:
        if opts:
            for opt in opts:
                opt(r)
        r.validate()
        r.full_url = urljoin(self.base_url, r.endpoint)

    def call_api(
        self,
        r: "RequestBuilder",
        opts: Optional[List[Callable[["RequestBuilder"], None]]] = None,
    ) -> bytes:
        self.parse_request(r, opts)
        req = requests.Request(r.method, r.full_url, headers=r.headers, data=r.body)
        prepped = self.http_client.prepare_request(req)
        self.debug_log("request: %s", prepped)

        if self.do:
            response = self.do(prepped)
        else:
            response = self.http_client.send(prepped)

        data = response.content
        self.debug_log("response: %s", response)
        self.debug_log("response body: %s", data)
        self.debug_log("response status code: %d", response.status_code)

        if response.status_code >= 400:
            api_err = MetaTraderServerAPIException(
                response=None, status_code=response.status_code, text=response.text
            )
            try:
                api_err_data = response.json()
                api_err.message = api_err_data.get("detail", response.text)
                api_err.code = api_err_data.get("code", response.status_code)
            except json.JSONDecodeError:
                self.debug_log("failed to unmarshal json")
            raise api_err

        return data


#
# Specify that the time uses standard utc time especially data from metatrader
#


# Example usage
# if __name__ == "__main__":
#     client = Client()
#     request = Request('GET', '/api/v1/test')
#     request.add_param('key1', 'value1').set_param('key2', 'value2')
#     request.set_body({'data': 'test'})
#     request.set_header('Authorization', 'Bearer token')

#     try:
#         response = client.call_api(request)
#         print(response)
#     except APIError as e:
#         print(e)
