from tradeflow.metatrader import base_client
from tradeflow.metatrader.request import RequestBuilder


class KlinesService:
    def __init__(self, client: base_client.Client):
        self.client = client
        self._symbol = ""
        self._interval = ""
        self._limit = None
        self._start_time = None
        self._end_time = None

    def symbol(self, symbol: str):
        self._symbol = symbol
        return self

    def interval(self, interval: str):
        self._interval = interval
        return self

    def limit(self, limit: int):
        self._limit = limit
        return self

    def start_time(self, start_time: int):
        """
        start_time: timestamp
        """
        self._start_time = start_time
        return self

    def end_time(self, end_time: int):
        """
        end_time: timestamp
        """
        self._end_time = end_time
        return self

    def do(self, opts=None):
        request = RequestBuilder("POST", "/api/klines")
        data = {}
        data["symbol"] = self._symbol
        data["interval"] = self._interval

        if self._limit is not None:
            data["limit"] = self._limit
        if self.start_time is not None:
            data["start_time"] = self._start_time
        if self.end_time is not None:
            data["end_time"] = self._end_time

        request.set_body(data)

        data = self.client.call_api(request, opts)
        return [Kline.from_list(item) for item in data]


class Kline:
    def __init__(
        self,
        open_time,
        open,
        high,
        low,
        close,
        volume,
        close_time,
        quote_asset_volume,
        trade_num,
        taker_buy_base_asset_volume,
        taker_buy_quote_asset_volume,
    ):
        self.open_time = open_time
        self.open = open
        self.high = high
        self.low = low
        self.close = close
        self.volume = volume
        self.close_time = close_time
        self.quote_asset_volume = quote_asset_volume
        self.trade_num = trade_num
        self.taker_buy_base_asset_volume = taker_buy_base_asset_volume
        self.taker_buy_quote_asset_volume = taker_buy_quote_asset_volume

    @classmethod
    def from_list(cls, data):
        if len(data) < 11:
            raise ValueError("Invalid kline response")
        return cls(
            open_time=data[0],
            open=data[1],
            high=data[2],
            low=data[3],
            close=data[4],
            volume=data[5],
            close_time=data[6],
            quote_asset_volume=data[7],
            trade_num=data[8],
            taker_buy_base_asset_volume=data[9],
            taker_buy_quote_asset_volume=data[10],
        )


# Usage example:
# client = Client(base_url="https://api.example.com")
# klines_service = KlinesService(client)
# klines = klines_service.symbol("BTCUSDT").interval("1h").limit(100).do()
# for kline in klines:
#     print(kline.open, kline.close)
