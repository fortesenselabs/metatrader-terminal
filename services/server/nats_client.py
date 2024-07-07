import asyncio
from models import Events
from settings import Settings
from utils import Logger
from internal import PubSub  # , Streams, StrategyMap


logger = Logger(name=__name__)
settings = Settings()


async def main():
    url = "{user}:{password}@{url}".format(
        user=settings.NATS_USER, password=settings.NATS_PASS, url=settings.NATS_URL
    )

    pubsub_client = await PubSub.connect(url)
    if not pubsub_client.instance.is_connected:
        logger.error(f"Error connecting to nats server at {url}")
        return

    logger.info(
        f"Connected to nats server at {pubsub_client.instance.connected_url.netloc}"
    )

    # hashmap = StrategyMap()

    pubsub = PubSub(pubsub_client.instance)
    # await pubsub.jetstream(Streams.DataFrame)

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
    await pubsub.subscribe(Events.Order, main_handler)

    # Example: Publish data to an event
    # payload = {"event_type": Events.DataFrame, "data": {...}}
    # await pubsub.publish(Events.DataFrame, payload)

    # Run indefinitely or handle shutdown gracefully
    # try:
    #     await asyncio.Event().wait()  # Wait forever unless interrupted
    # except KeyboardInterrupt:
    #     logger.info("Shutting down...")
    # finally:
    #     await pubsub_client.instance.close()


if __name__ == "__main__":
    loop = asyncio.get_event_loop()
    try:
        loop.run_until_complete(main())
    finally:
        loop.close()
