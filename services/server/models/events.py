class Events:
    Kline = "Event:Kline"
    CriticalError = "Event:CriticalError"
    DataFrame = "Event:DataFrame"

    # Orders
    Order = "Event:Order"
    CreateOrder = "Event:Order:Create"
    CloseOrder = "Event:Order:Close"


class Signal:
    BUY = "BUY"
    SELL = "SELL"
    NONE = "NONE"
