import asyncio
from models import Events
from settings import Settings
from utils import Logger
from internal import PubSub, SocketIOServerClient  # , Streams, StrategyMap


logger = Logger(name=__name__)
settings = Settings()


async def main():
    url = "http://localhost:8000"

    socketio_client_instance = await SocketIOServerClient.connect_client(url)

    logger.info(
        f"Connected to Server at {url}: {socketio_client_instance.instance.connected}"
    )

    async def main_handler(data):
        logger.info(f"Data received: {data}")
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

    # Subscribe to specific events
    # await pubsub.subscribe(Events.Kline, main_handler)
    # await pubsub.subscribe(Events.Order, main_handler)
    await socketio_client_instance.subscribe(Events.Order, main_handler)

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
