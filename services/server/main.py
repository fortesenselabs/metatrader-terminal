import asyncio
from nats.aio.client import Client as NATS
from models import DWXClientParams, Events
from settings import Settings
from utils import Logger
from internal import PubSub  # , Streams, StrategyMap
from handlers import OrderHandler


logger = Logger(name=__name__)
settings = Settings()


async def init_handlers(dwx_client_params: DWXClientParams, pubsub_instance: NATS):
    try:
        order_handler = OrderHandler(dwx_client_params, pubsub_instance)
        return
    except Exception as e:
        raise ValueError("An error occurred while initializing handlers: ", e) from e


async def main():
    logger.info("MetaTrader 5 API Server is starting up")
    logger.info(f"Settings: {settings.model_dump()}")

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
    dwx_client_params = DWXClientParams(mt_directory_path=settings.METATRADER_FILES_DIR)
    await init_handlers(dwx_client_params, pubsub_client.instance)

    # hashmap = StrategyMap()

    pubsub = PubSub(pubsub_client.instance)
    # await pubsub.jetstream(Streams.DataFrame)

    async def main_handler(data):
        logger.info(f"data received: {data}")
        # symbol = data["kline"]["symbol"]
        # strategy = hashmap.get_instance(symbol)
        # strategy.populate(data)
        # payload = {}  # strategy.get_payload()
        # await pubsub.publish(Events.DataFrame, payload)
        return

    # await pubsub.subscribe(Events.Kline, main_handler)
    await pubsub.subscribe(Events.Order, main_handler)

    # Run indefinitely or handle shutdown gracefully
    try:
        await asyncio.Event().wait()  # Wait forever unless interrupted
    except KeyboardInterrupt:
        logger.info("Shutting down...")
    finally:
        await pubsub_client.instance.close()


if __name__ == "__main__":
    loop = asyncio.get_event_loop()
    try:
        loop.run_until_complete(main())
    finally:
        loop.close()
