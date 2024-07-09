from typing import List, Optional
from pydantic import BaseModel
from .enum_types import Permission, TimeFrame, DataMode


class Symbol(BaseModel):
    symbol: str
    status: str
    baseAsset: str
    baseAssetPrecision: int
    quoteAsset: str
    quoteAssetPrecision: int
    baseCommissionPrecision: int
    quoteCommissionPrecision: int
    orderTypes: List[str]
    icebergAllowed: bool
    ocoAllowed: bool
    otoAllowed: bool
    quoteOrderQtyMarketAllowed: bool
    allowTrailingStop: bool
    cancelReplaceAllowed: bool
    isSpotTradingAllowed: bool
    isMarginTradingAllowed: bool
    filters: List[dict]
    permissions: List[Permission]
    permissionSets: List[List[Permission]]
    defaultSelfTradePreventionMode: str
    allowedSelfTradePreventionModes: List[str]


class SymbolBalance(BaseModel):
    symbol: str
    free: str
    locked: str


class SymbolMarketData(BaseModel):
    symbol: str
    time_frame: Optional[TimeFrame] = TimeFrame.CURRENT
    mode: Optional[DataMode] = DataMode.TICK


class AvailableSymbolsInfoResponse(BaseModel):
    symbols: List[Symbol]
