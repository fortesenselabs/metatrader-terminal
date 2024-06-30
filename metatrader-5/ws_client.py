from enum import Enum
import json
import asyncio
import time
from typing import List
import websockets
import requests  # Added for HTTP request


class SubscriptionDataMode(Enum):
    TICK = "TICK"
    BAR = "BAR"


class TimeFrame(Enum):
    CURRENT = "CURRENT"
    M1 = "M1"
    M2 = "M2"
    M3 = "M3"
    M4 = "M4"
    M5 = "M5"
    M6 = "M6"
    M10 = "M10"
    M12 = "M12"
    M15 = "M15"
    M20 = "M20"
    M30 = "M30"
    H1 = "H1"
    H2 = "H2"
    H3 = "H3"
    H4 = "H4"
    H6 = "H6"
    H8 = "H8"
    H12 = "H12"
    D1 = "D1"
    W1 = "W1"
    MN1 = "MN1"

    @classmethod
    def from_string(cls, string):
        try:
            return cls[string]
        except KeyError:
            return None


class SymbolMarketData:
    symbol: str
    time_frame: TimeFrame
    mode: SubscriptionDataMode


async def subscribe_and_connect(
    base_server_url: str,
    symbols_data: List[SymbolMarketData],
):
    """
    Subscribes to symbols on the server and then connects via WebSocket.
    """
    account_info_url = f"http://{base_server_url}/account_info"
    response = requests.get(account_info_url)
    response.raise_for_status()  # Raise exception for non-2xx status codes

    print(f"Account Info response: {response.text}")

    # Prepare subscription data
    subscription_data = {
        "symbols_data": symbols_data,
    }

    # Send subscription request (replace with actual API endpoint if needed)
    subscription_url = (
        f"http://{base_server_url}/subscribe"  # Adjust URL based on server API
    )
    response = requests.post(subscription_url, json=subscription_data)
    response.raise_for_status()  # Raise exception for non-2xx status codes

    print(f"Subscription response: {response.text}")

    # time.sleep(2)
    await asyncio.sleep(0.1)

    # Connect to WebSocket
    uri = f"ws://{base_server_url}/ws"  # Combine server URL and WebSocket path
    async with websockets.connect(uri) as websocket:
        while True:
            try:
                data = {"current_subscription_data_mode": "TICK"}
                await websocket.send(json.dumps(data))

                if (
                    SubscriptionDataMode(data["current_subscription_data_mode"])
                    == SubscriptionDataMode.BAR
                ):
                    await asyncio.sleep(60)

                # Wait for data from the server
                data = await websocket.recv()
                print(f"Server response: {data}")
            except websockets.ConnectionClosed:
                print("Connection closed by server.")
                break


if __name__ == "__main__":
    base_server_url = "127.0.0.1:8000/api"  # Replace with server's base URL
    # symbols = ["Step Index", "Volatility 75 Index"] # tick data
    # symbols = [["Step Index", "M1"], ["Volatility 75 Index", "M5"]]  # bar data

    # symbol 1
    symbol_1 = SymbolMarketData()
    symbol_1.symbol = "Step Index"
    symbol_1.mode = SubscriptionDataMode.TICK.value
    symbol_1.time_frame = TimeFrame.from_string("CURRENT").value

    # symbol 2
    symbol_2 = SymbolMarketData()
    symbol_2.symbol = "Crash 1000 Index"
    symbol_2.mode = SubscriptionDataMode.BAR.value
    symbol_2.time_frame = TimeFrame.from_string("M5").value

    # symbol 3
    symbol_3 = SymbolMarketData()
    symbol_3.symbol = "Volatility 75 Index"
    symbol_3.mode = SubscriptionDataMode.BAR.value
    symbol_3.time_frame = TimeFrame.from_string("M1").value

    symbols_data = [symbol_1.__dict__, symbol_2.__dict__, symbol_3.__dict__]
    print(symbols_data)
    asyncio.run(subscribe_and_connect(base_server_url, symbols_data))


# https://github.com/leonh/redis-streams-fastapi-chat
# https://stribny.name/blog/2020/07/real-time-data-streaming-using-fastapi-and-websockets/
# https://github.com/mjhea0/awesome-fastapi
# https://medium.com/@philipokiokio/realtime-notifications-for-web-applications-with-fastapi-messaging-queue-and-websockets-8627f7205c2a
