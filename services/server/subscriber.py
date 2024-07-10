import asyncio
import json
from typing import List
from models import (
    Events,
    CreateOrderRequest,
    CancelOrderRequest,
    OrderResponse,
    SubscribeRequest,
    SymbolMarketData,
    TimeFrame,
    HistoricalKlineRequest,
)
from settings import Settings
from utils import Logger
from internal import SocketIOServerClient  # , Streams, StrategyMap


logger = Logger(name=__name__)
settings = Settings()

empty_request = "{}"
open_orders: List[OrderResponse] = []


async def response_handler(data):
    logger.info(f"response_handler => {data}")
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
    logger.info(f"response_handler => {data} | length: {len(data)}")


async def subscribe_to_kline_tick(client_instance: SocketIOServerClient):
    await client_instance.subscribe_to_server(
        Events.KlineSubscribeTick, response_handler
    )

    subscribe_request = SubscribeRequest(
        symbols_data=[SymbolMarketData(symbol="Step Index")]
    )
    await client_instance.publish(
        Events.KlineSubscribeTick, subscribe_request.model_dump_json()
    )


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
    await client_instance.subscribe_to_server(
        Events.KlineHistorical, historical_kline_response_handler
    )
    subscribe_request = HistoricalKlineRequest(
        symbol="Step Index", time_frame=TimeFrame.M1, limit=10
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
    await client_instance.subscribe_to_server(Events.CreateOrder, response_handler)
    await client_instance.subscribe_to_server(Events.CloseOrder, response_handler)
    # await client_instance.subscribe_to_server(Events.Order, response_handler)

    new_order_request = CreateOrderRequest(
        symbol="Step Index",
        side="SELL",
        quantity="1",
    )

    for i in range(3):
        logger.info(f"Order {i}")
        await client_instance.publish(
            Events.CreateOrder, new_order_request.model_dump_json()
        )

    await asyncio.sleep(7)  # wait for some time before closing orders
    request = CancelOrderRequest(close_all=True)
    await client_instance.publish(Events.CloseOrder, request.model_dump_json())


async def get_open_orders(client_instance: SocketIOServerClient):
    await client_instance.subscribe_to_server(Events.GetOpenOrders, response_handler)
    await client_instance.publish(Events.GetOpenOrders, empty_request)


async def get_account_and_exchange_info(client_instance: SocketIOServerClient):
    await client_instance.subscribe_to_server(Events.ExchangeInfo, response_handler)
    await client_instance.subscribe_to_server(Events.Account, response_handler)

    await client_instance.publish(Events.ExchangeInfo, empty_request)
    await client_instance.publish(Events.Account, empty_request)


async def main():
    url = "http://localhost:8000"
    client_instance = await SocketIOServerClient.connect_client(url)
    logger.info(f"Connected to Server at {url}: {client_instance.instance.connected}")

    # Subscribe to specific events

    await get_account_and_exchange_info(client_instance)

    # await new_order(client_instance)
    await get_open_orders(client_instance)

    # await subscribe_to_kline_tick(client_instance)
    # await subscribe_to_kline_bar(client_instance)
    # await subscribe_to_kline_historical(client_instance)

    # Run indefinitely or handle shutdown gracefully
    try:
        await asyncio.Event().wait()  # Wait forever unless interrupted
    except KeyboardInterrupt:
        logger.info("Shutting down...")


if __name__ == "__main__":
    loop = asyncio.get_event_loop()
    try:
        loop.run_until_complete(main())
    finally:
        loop.close()
