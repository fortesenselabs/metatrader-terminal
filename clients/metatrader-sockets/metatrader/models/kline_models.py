from datetime import datetime, timezone
from typing import List, Optional
from pydantic import BaseModel, Field, model_validator

from .enum_types import TimeFrame
from .exchange_info_models import RateLimit
from .symbol_models import SymbolMarketData


class TickInfoResponse(BaseModel):
    event: str
    time: Optional[int]
    symbol: str
    bid: Optional[float]
    ask: Optional[float]


class BarInfoResponse(BaseModel):
    event: str
    time_frame: str
    symbol: str
    time: str
    open: str
    high: str
    low: str
    close: str


# Define a schema for the subscription request body
class SubscribeRequest(BaseModel):
    symbols_data: List[SymbolMarketData]


class SubscribeResponse(BaseModel):
    message: str
    subscribed: bool
    all: bool


# Kline
class Kline(BaseModel):
    start_time: Optional[int]
    end_time: Optional[int]
    time: Optional[int]
    symbol: str
    interval: str
    open: float
    close: float
    high: float
    low: float
    volume: float
    is_final: bool


class HistoricalKlineRequest(BaseModel):
    symbol: str
    time_frame: TimeFrame
    start_time: Optional[float] = None
    end_time: Optional[float] = None
    time_zone: Optional[str] = Field(default="0", description="Default: 0 (UTC)")
    limit: Optional[int] = Field(
        default=300, le=1000, description="Default 300; max 1000"
    )

    @model_validator(mode="after")
    def adjust_time(self):
        self.time_frame = (
            self.time_frame if self.time_frame != TimeFrame.CURRENT else TimeFrame.M1
        )
        return self


# WsKline define websocket kline


class KlineResponse(BaseModel):
    result: List[Kline]
    id: Optional[str] = None
    status: Optional[int] = None
    rateLimits: Optional[List[RateLimit]] = None


# KlineEvent websocket kline event
class KlineEvent(BaseModel):
    event: Optional[str] = None
    time: Optional[int] = None
    symbol: str
    kline: Optional[Kline] = None
