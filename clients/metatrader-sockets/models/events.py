class Events:
    # Errors
    CriticalError = "Event:CriticalError"

    # Kline
    KlineSubscribeTick = "Event:Kline:Subscribe:Tick"
    KlineSubscribeBar = "Event:Kline:Subscribe:Bar"
    KlineUnsubscribeTick = "Event:Kline:Unsubscribe:Tick"
    KlineUnsubscribeBar = "Event:Kline:Unsubscribe:Bar"
    KlineListSubscriptions = "Event:Kline:ListSubscriptions"
    KlineHistorical = "Event:Kline:Historical"

    # Orders
    Order = "Event:Order:All"
    CreateOrder = "Event:Order:Create"
    CloseOrder = "Event:Order:Close"
    ModifyOrder = "Event:Order:Modify"
    GetOpenOrders = "Event:Order:Get:Open"
    GetCloseOrders = "Event:Order:Get:Close"

    # Account
    Account = "Event:Account:All"

    # Exchange Info
    ExchangeInfo = "Event:ExchangeInfo:All"
