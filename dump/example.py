import asyncio
from metatrader import (
    TerminalClient,
    CreateOrderRequest,
    CancelOrderRequest,
    HistoricalKlineRequest,
    SideType,
    TimeFrame,
)


async def main():
    client = await TerminalClient.create(verbose=False)

    async def fetch_account_info():
        account_info = await client.get_account()
        if account_info:
            print(f"Account Info: {account_info}")
        else:
            print("Failed to fetch account info.")

    async def fetch_exchange_info():
        exchange_info = await client.get_exchange_info()
        if exchange_info:
            print(f"Exchange Info: {exchange_info}")
        else:
            print("Failed to fetch exchange info.")

    # await fetch_account_info()
    # OR
    # tasks = [fetch_account_info, fetch_exchange_info]
    # await client._run(tasks)

    # Create new order
    # order_request = CreateOrderRequest(
    #     symbol="Step Index",
    #     side=SideType.BUY,
    #     quantity="0.4",
    # )
    # new_order = await client.create_order(order_request)
    # if new_order:
    #     print(f"New Order: {new_order}")
    # else:
    #     print("Failed to create new order.")

    # # Get open orders
    # open_orders = await client.get_open_orders()
    # if open_orders:
    #     print(f"Open Orders: {open_orders}")
    # else:
    #     print("Failed to fetch open orders.")

    # # await asyncio.sleep(7)

    # # Close all opened orders
    # order_request = CancelOrderRequest(close_all=True)
    # new_order = await client.close_order(order_request)
    # if new_order:
    #     print(f"Closed Order: {new_order}")
    # else:
    #     print("Failed to close order.")

    # # get historical kline data
    # request = HistoricalKlineRequest(
    #     symbol="Step Index",
    #     time_frame=TimeFrame.M1,
    #     limit=500,
    # )
    # kline_data = await client.get_historical_kline_data(request)
    # if kline_data:
    #     print(f"Kline Data: {kline_data}")
    # else:
    #     print("Failed to fetch data.")

    # subscribe to realtime tick/bar data
    async def callback(event):
        print(f"event: {event}")

    await client.stream(
        callback, symbols=["Step Index"], data_mode="BAR", time_frame="M5"
    )


if __name__ == "__main__":
    loop = asyncio.get_event_loop()
    try:
        loop.run_until_complete(main())
    finally:
        loop.close()
