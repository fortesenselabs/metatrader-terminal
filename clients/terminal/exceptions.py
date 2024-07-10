# coding=utf-8
import json


# errors.py
class APIError(Exception):
    def __init__(self, code: int, message: str):
        self.code = code
        self.message = message

    def __str__(self) -> str:
        return f"<APIError> code={self.code}, msg={self.message}"


def is_api_error(e: Exception) -> bool:
    return isinstance(e, APIError)


class MetaTraderServerAPIException(Exception):

    def __init__(self, response, status_code, text):
        self.code = 0
        try:
            json_res = json.loads(text)
        except ValueError:
            self.message = (
                "Invalid JSON error message from MetaTrader Server: {}".format(
                    response.text
                )
            )
        else:
            self.code = json_res.get("code")
            self.message = json_res.get("msg")

        self.status_code = status_code
        self.response = response
        self.request = getattr(response, "request", None)

    def __str__(self):  # pragma: no cover
        return "APIError(code=%s): %s" % (self.code, self.message)


class MetaTraderServerRequestException(Exception):
    def __init__(self, message):
        self.message = message

    def __str__(self):
        return "MetaTraderServerRequestException: %s" % self.message


class MetaTraderServerOrderException(Exception):

    def __init__(self, code, message):
        self.code = code
        self.message = message

    def __str__(self):
        return "MetaTraderServerOrderException(code=%s): %s" % (self.code, self.message)


class MetaTraderServerOrderMinAmountException(MetaTraderServerOrderException):

    def __init__(self, value):
        message = "Amount must be a multiple of %s" % value
        super().__init__(-1013, message)


class MetaTraderServerOrderMinPriceException(MetaTraderServerOrderException):

    def __init__(self, value):
        message = "Price must be at least %s" % value
        super().__init__(-1013, message)


class MetaTraderServerOrderMinTotalException(MetaTraderServerOrderException):

    def __init__(self, value):
        message = "Total must be at least %s" % value
        super().__init__(-1013, message)


class MetaTraderServerOrderUnknownSymbolException(MetaTraderServerOrderException):

    def __init__(self, value):
        message = "Unknown symbol %s" % value
        super().__init__(-1013, message)


class MetaTraderServerOrderInactiveSymbolException(MetaTraderServerOrderException):

    def __init__(self, value):
        message = "Attempting to trade an inactive symbol %s" % value
        super().__init__(-1013, message)


class MetaTraderServerWebsocketUnableToConnect(Exception):
    pass


class NotImplementedException(Exception):
    def __init__(self, value):
        message = f"Not implemented: {value}"
        super().__init__(message)


class UnknownDateFormat(Exception): ...
