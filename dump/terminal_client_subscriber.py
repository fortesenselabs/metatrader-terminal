import asyncio
import contextlib
import json
import random
from typing import List
from metatrader.models import (
    Events,
    CreateOrderRequest,
    CancelOrderRequest,
    OrderResponse,
    SubscribeRequest,
    SymbolMarketData,
    TimeFrame,
    HistoricalKlineRequest,
)
from metatrader import Logger
from metatrader.socketio import SocketIOServerClient

logger = Logger(name=__name__)

empty_request = "{}"
open_orders: List[OrderResponse] = []
session_data = {}
event = None


async def response_handler(data):
    logger.info(f"{event} => {data}")
    # session_data[Events.KlineHistorical] = data
    # order = OrderResponse(**data)
    # open_orders.append(order)
    # logger.info(f"Opened Orders: {open_orders}")
    # Implement your logic here based on the received data
    # Example: handle different types of events
    # event_type = data.get("event_type")
    # if event_type == Events.Kline:
    #     # Process kline event
    #     pass
    # elif event_type == Events.Order:
    #     # Process order event
    #     pass
    # else:
    #     logger.warning(f"Unknown event type received: {event_type}")

    # request = CancelOrderRequest(order_id=order.order_id)
    # await client_instance.publish(Events.CloseOrder, request.model_dump_json())


async def historical_kline_response_handler(data):
    logger.info(f"{event}=> {data} | length: {len(data)}")
    try:
        jsonData = json.loads(data)
        logger.info(f"len jsonData: {len(jsonData)}")
    except TypeError:
        pass
    except:
        logger.debug(data)


async def subscribe_to_kline_tick(client_instance: SocketIOServerClient):
    event = Events.KlineSubscribeTick
    await client_instance.subscribe_to_server(event, response_handler)

    subscribe_request = SubscribeRequest(
        symbols_data=[SymbolMarketData(symbol="Step Index")]
    )
    await client_instance.publish(event, subscribe_request.model_dump_json())


async def subscribe_to_kline_bar(client_instance: SocketIOServerClient):
    await client_instance.subscribe_to_server(
        Events.KlineSubscribeBar, response_handler
    )
    subscribe_request = SubscribeRequest(
        symbols_data=[SymbolMarketData(symbol="Step Index")]
    )
    await client_instance.publish(
        Events.KlineSubscribeBar, subscribe_request.model_dump_json()
    )


async def subscribe_to_kline_historical(client_instance: SocketIOServerClient):
    """
    Moved
    """
    await client_instance.subscribe_to_server(
        Events.KlineHistorical, historical_kline_response_handler
    )
    subscribe_request = HistoricalKlineRequest(
        symbol="Step Index", time_frame=TimeFrame.M1, limit=500
    )

    await client_instance.publish(
        Events.KlineHistorical, subscribe_request.model_dump_json()
    )

    # For Error Testing:
    # sr = subscribe_request.model_dump()
    # sr["time_frame"] = "M1"
    # sr["limit"] = 2000
    # await client_instance.publish(Events.KlineHistorical, json.dumps(sr))


async def new_order(client_instance: SocketIOServerClient):
    """
    Moved
    """
    event = Events.CreateOrder
    await client_instance.subscribe_to_server(event, response_handler)

    # await client_instance.subscribe_to_server(Events.Order, response_handler)

    new_order_request = CreateOrderRequest(
        symbol="Step Index",
        side="SELL",
        quantity="1",
    )

    for i in range(2):
        logger.info(f"Order {i}")
        new_order_request.side = random.choice(["BUY", "SELL"])
        await client_instance.publish(event, new_order_request.model_dump_json())

    await asyncio.sleep(10)  # wait for some time before closing orders

    # await get_open_orders(client_instance)

    event = Events.CloseOrder
    await client_instance.subscribe_to_server(event, response_handler)
    request = CancelOrderRequest(close_all=True)
    await client_instance.publish(event, request.model_dump_json())


async def get_open_orders(client_instance: SocketIOServerClient):
    """
    Moved
    """
    await client_instance.subscribe_to_server(Events.GetOpenOrders, response_handler)
    await client_instance.publish(Events.GetOpenOrders, empty_request)


async def get_account_and_exchange_info(client_instance: SocketIOServerClient):
    """
    Moved
    """
    await client_instance.subscribe_to_server(Events.ExchangeInfo, response_handler)
    await client_instance.subscribe_to_server(Events.Account, response_handler)

    await client_instance.publish(Events.ExchangeInfo, empty_request)
    await client_instance.publish(Events.Account, empty_request)


async def event_wait(evt, timeout):
    # suppress TimeoutError because we'll return False in case of timeout
    with contextlib.suppress(asyncio.TimeoutError):
        await asyncio.wait_for(evt.wait(), timeout)
    return evt.is_set()


async def main():
    url = "http://localhost:8000"
    client_instance = await SocketIOServerClient.connect_client(url, verbose=False)
    logger.info(f"Connected to Server at {url}: {client_instance.instance.connected}")

    # Subscribe to specific events
    # await get_account_and_exchange_info(client_instance)

    await new_order(client_instance)
    # await get_open_orders(client_instance)

    # await subscribe_to_kline_tick(client_instance)
    # await subscribe_to_kline_bar(client_instance)
    # await subscribe_to_kline_historical(client_instance)

    # Run indefinitely or handle shutdown gracefully
    # try:

    #     async def event_check():
    #         Events.KlineHistorical in session_data

    #     # await asyncio.Event().wait()  # Wait forever unless interrupted
    #     while not await event_wait(event_check, 3):
    #         print(session_data)

    try:
        await asyncio.Event().wait()
    except KeyboardInterrupt:
        logger.info("Shutting down...")


if __name__ == "__main__":
    loop = asyncio.get_event_loop()
    try:
        loop.run_until_complete(main())
    finally:
        loop.close()


# 2024.07.13 18:03:36.419	DWX_Server_MT5 (Step Index,M1)	Not executing command because ID already exists. commandID: 2, command: GET_HISTORIC_DATA, content: Step Index,M1,1720848216,1720890216
