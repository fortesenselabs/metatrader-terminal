from typing import List, Optional
from enum import Enum
from pydantic import BaseModel, Field
from application.models.exchange_info_models import RateLimit
from application.models.symbol_models import SymbolMarketData
from application.models.enum_types import WsRequestMethod


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


class KlineResponse(BaseModel):
    id: str
    status: int
    result: List[List]
    rateLimits: Optional[List[RateLimit]] = None


class KlineParams(BaseModel):
    symbol: str
    interval: str
    startTime: Optional[int] = None
    endTime: Optional[int] = None
    timeZone: Optional[str] = Field(default="0", description="Default: 0 (UTC)")
    limit: Optional[int] = Field(
        default=500, le=1000, description="Default 500; max 1000"
    )


# WsKline define websocket kline
class WsKline(BaseModel):
    start_time: Optional[int]
    end_time: Optional[int]
    symbol: str
    interval: str
    open: str
    close: str
    high: str
    low: str
    volume: str
    is_final: bool


# WsKlineEvent define websocket kline event
class WsKlineEvent(BaseModel):
    event: Optional[str] = None
    time: Optional[int] = None
    symbol: str
    kline: Optional[WsKline] = None


class WsRequest(BaseModel):
    id: str
    method: Optional[WsRequestMethod] = None
    params: Optional[KlineParams] = None
