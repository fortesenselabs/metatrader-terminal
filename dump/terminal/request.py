import json
from typing import Dict, Callable, Any
from enum import Enum


class SecType(Enum):
    NONE = 0
    API_KEY = 1
    SIGNED = 2  # if the 'timestamp' parameter is required


Params = Dict[str, Any]


class RequestBuilder:
    def __init__(self, method: str, endpoint: str):
        self.method = method
        self.endpoint = endpoint
        self.query = {}
        self.form = {}
        self.recv_window = None
        self.sec_type = SecType.NONE
        self.headers = {}
        self.body = None
        self.full_url = ""

    def add_param(self, key: str, value: Any) -> "RequestBuilder":
        self.query[key] = value
        return self

    def set_param(self, key: str, value: Any) -> "RequestBuilder":
        self.query[key] = value
        return self

    def set_params(self, params: Params) -> "RequestBuilder":
        for k, v in params.items():
            self.set_param(k, v)
        return self

    def set_form_param(self, key: str, value: Any) -> "RequestBuilder":
        self.form[key] = value
        return self

    def set_form_params(self, params: Params) -> "RequestBuilder":
        for k, v in params.items():
            self.set_form_param(k, v)
        return self

    def validate(self) -> None:
        if self.query is None:
            self.query = {}
        if self.form is None:
            self.form = {}

    def set_body(self, data: Any) -> "RequestBuilder":
        self.body = json.dumps(data)
        return self

    def build(self):
        return {
            "method": self.method,
            "endpoint": self.endpoint,
            "headers": self.headers,
            "params": self.query,
            "data": self.body,
        }

    def set_header(self, key: str, value: str) -> None:
        self.headers[key] = value

    def apply_option(self, option: Callable[["RequestBuilder"], None]) -> None:
        option(self)


def with_recv_window(recv_window: int) -> Callable[[RequestBuilder], None]:
    def option(request: RequestBuilder) -> None:
        request.recv_window = recv_window

    return option


def with_header(
    key: str, value: str, replace: bool = True
) -> Callable[[RequestBuilder], None]:
    def option(request: RequestBuilder) -> None:
        if replace:
            request.header[key] = value
        else:
            if key in request.header:
                request.header[key] += f", {value}"
            else:
                request.header[key] = value

    return option


def with_headers(headers: Dict[str, str]) -> Callable[[RequestBuilder], None]:
    def option(request: RequestBuilder) -> None:
        request.header = headers.copy()

    return option


# Example usage
# request = Request("GET", "https://example.com/api")
# request.add_param("key1", "value1").set_param("key2", "value2")
# request.set_body({"data": "test"})
# request.set_header("Authorization", "Bearer token")
# request.apply_option(with_recv_window(5000))
# request.apply_option(with_header("Custom-Header", "HeaderValue", replace=False))
