from tradeflow.metatrader.terminal.enums import SymbolFilterType


class ExchangeInfo:
    def __init__(self, timezone, server_time, rate_limits, exchange_filters, symbols):
        self.timezone = timezone
        self.server_time = server_time
        self.rate_limits = rate_limits
        self.exchange_filters = exchange_filters
        self.symbols = symbols

    @classmethod
    def from_dict(cls, data):
        rate_limits = [RateLimit(**rl) for rl in data.get("rateLimits", [])]
        symbols = [Symbol(**s) for s in data.get("symbols", [])]
        return cls(
            data["timezone"],
            data["serverTime"],
            rate_limits,
            data["exchangeFilters"],
            symbols,
        )


class RateLimit:
    def __init__(self, rateLimitType, interval, intervalNum, limit):
        self.rateLimitType = rateLimitType
        self.interval = interval
        self.intervalNum = intervalNum
        self.limit = limit


class Symbol:
    def __init__(
        self,
        symbol,
        status,
        baseAsset,
        baseAssetPrecision,
        quoteAsset,
        quotePrecision,
        quoteAssetPrecision,
        baseCommissionPrecision,
        quoteCommissionPrecision,
        orderTypes,
        icebergAllowed,
        ocoAllowed,
        quoteOrderQtyMarketAllowed,
        isSpotTradingAllowed,
        isMarginTradingAllowed,
        filters,
        permissions,
        permissionSets,
    ):
        self.symbol = symbol
        self.status = status
        self.baseAsset = baseAsset
        self.baseAssetPrecision = baseAssetPrecision
        self.quoteAsset = quoteAsset
        self.quotePrecision = quotePrecision
        self.quoteAssetPrecision = quoteAssetPrecision
        self.baseCommissionPrecision = baseCommissionPrecision
        self.quoteCommissionPrecision = quoteCommissionPrecision
        self.orderTypes = orderTypes
        self.icebergAllowed = icebergAllowed
        self.ocoAllowed = ocoAllowed
        self.quoteOrderQtyMarketAllowed = quoteOrderQtyMarketAllowed
        self.isSpotTradingAllowed = isSpotTradingAllowed
        self.isMarginTradingAllowed = isMarginTradingAllowed
        self.filters = filters
        self.permissions = permissions
        self.permissionSets = permissionSets

    def get_filter(self, filter_type):
        for filter in self.filters:
            if filter["filterType"] == filter_type.value:
                return filter
        return None

    def lot_size_filter(self):
        filter = self.get_filter(SymbolFilterType.LotSize)
        if filter:
            return LotSizeFilter(filter["maxQty"], filter["minQty"], filter["stepSize"])
        return None

    def price_filter(self):
        filter = self.get_filter(SymbolFilterType.PriceFilter)
        if filter:
            return PriceFilter(
                filter["maxPrice"], filter["minPrice"], filter["tickSize"]
            )
        return None

    def percent_price_filter(self):
        filter = self.get_filter(SymbolFilterType.PercentPrice)
        if filter:
            return PercentPriceFilter(
                filter["avgPriceMins"], filter["multiplierUp"], filter["multiplierDown"]
            )
        return None

    def min_notional_filter(self):
        filter = self.get_filter(SymbolFilterType.MinNotional)
        if filter:
            return MinNotionalFilter(
                filter["minNotional"], filter["avgPriceMins"], filter["applyToMarket"]
            )
        return None

    def iceberg_parts_filter(self):
        filter = self.get_filter(SymbolFilterType.IcebergParts)
        if filter:
            return IcebergPartsFilter(filter["limit"])
        return None

    def market_lot_size_filter(self):
        filter = self.get_filter(SymbolFilterType.MarketLotSize)
        if filter:
            return MarketLotSizeFilter(
                filter["maxQty"], filter["minQty"], filter["stepSize"]
            )
        return None

    def max_num_algo_orders_filter(self):
        filter = self.get_filter(SymbolFilterType.MaxNumAlgoOrders)
        if filter:
            return MaxNumAlgoOrdersFilter(filter["maxNumAlgoOrders"])
        return None


class LotSizeFilter:
    def __init__(self, maxQty, minQty, stepSize):
        self.maxQty = maxQty
        self.minQty = minQty
        self.stepSize = stepSize


class PriceFilter:
    def __init__(self, maxPrice, minPrice, tickSize):
        self.maxPrice = maxPrice
        self.minPrice = minPrice
        self.tickSize = tickSize


class PercentPriceFilter:
    def __init__(self, avgPriceMins, multiplierUp, multiplierDown):
        self.avgPriceMins = avgPriceMins
        self.multiplierUp = multiplierUp
        self.multiplierDown = multiplierDown


class MinNotionalFilter:
    def __init__(self, minNotional, avgPriceMins, applyToMarket):
        self.minNotional = minNotional
        self.avgPriceMins = avgPriceMins
        self.applyToMarket = applyToMarket


class IcebergPartsFilter:
    def __init__(self, limit):
        self.limit = limit


class MarketLotSizeFilter:
    def __init__(self, maxQty, minQty, stepSize):
        self.maxQty = maxQty
        self.minQty = minQty
        self.stepSize = stepSize


class MaxNumAlgoOrdersFilter:
    def __init__(self, maxNumAlgoOrders):
        self.maxNumAlgoOrders = maxNumAlgoOrders
