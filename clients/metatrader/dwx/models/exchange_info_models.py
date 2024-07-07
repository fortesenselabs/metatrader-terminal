# Exchange Info
from enum import Enum
from typing import List
from pydantic import BaseModel
from .symbol_models import Symbol


class RateLimit(BaseModel):
    rateLimitType: str
    interval: str
    intervalNum: int
    limit: int


class ExchangeInfoResponse(BaseModel):
    timezone: str
    server_time: int
    rate_limits: List[RateLimit] = []
    exchange_filters: List[dict] = []
    symbols: List[Symbol]
    sors: List[dict]


class RequestType(Enum):
    Kline = "Kline"
    Tick = "Tick"

    @classmethod
    def export_all(cls) -> List[str]:
        return [order_type.value for order_type in cls]
