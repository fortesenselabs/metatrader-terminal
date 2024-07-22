import asyncio
from metatrader import (
    TerminalClient,
    CreateOrderRequest,
    CancelOrderRequest,
    SideType,
)


async def main():
    client = await TerminalClient.create(verbose=False)

    # Create new order
    order_request = CreateOrderRequest(
        symbol="Step Index",
        side=SideType.BUY,  # random.choice(["BUY", "SELL"])
        quantity="0.4",
    )
    new_order = await client.create_order(order_request)
    if new_order:
        print(f"New Order: {new_order}")
    else:
        print("Failed to create new order.")

    # Get open orders
    open_orders = await client.get_open_orders()
    if open_orders:
        print(f"Open Orders: {open_orders}")
    else:
        print("Failed to fetch open orders.")

    await asyncio.sleep(3)

    # Close all opened orders
    order_request = CancelOrderRequest(close_all=True)
    new_order = await client.close_order(order_request)
    if new_order:
        print(f"Closed Order: {new_order}")
    else:
        print("Failed to close order.")


if __name__ == "__main__":
    loop = asyncio.get_event_loop()
    try:
        loop.run_until_complete(main())
    finally:
        loop.close()
