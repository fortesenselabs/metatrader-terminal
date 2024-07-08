from aiohttp import web
from models import DWXClientParams
from settings import Settings
from utils import Logger
from internal import SocketIOServerClient
from handlers import OrderHandler


logger = Logger(name=__name__)
settings = Settings()


async def init_socketio_server():
    server = await SocketIOServerClient.create_server()

    async def server_handler(data):
        logger.info(f"Server received data: {data}")
        await server.emit("response_event", {"message": "Hello from server!"})

    await server.on("request_event", server_handler)
    logger.info("Socket.IO server is running...")

    return server


async def init_handlers(
    dwx_client_params: DWXClientParams,
    pubsub_instance: SocketIOServerClient,
):
    try:
        order_handler = OrderHandler(
            dwx_client_params,
            pubsub_instance,
        )
        return
    except Exception as e:
        raise ValueError("An error occurred while initializing handlers: ", e) from e


async def main():
    logger.info("MetaTrader 5 API Server is starting up")
    logger.info(f"Settings: {settings.model_dump()}")

    socketio_server_instance = await init_socketio_server()
    # logger.info(
    #     f"socketio_server_instance.instance.socketio_path: {socketio_server_instance.instance.socketio_path}"
    # )
    dwx_client_params = DWXClientParams(mt_directory_path=settings.METATRADER_FILES_DIR)
    await init_handlers(
        dwx_client_params,
        socketio_server_instance,
    )

    app = web.Application()
    socketio_server_instance.instance.attach(app)
    # socketio_server_instance.instance.start_background_task(background_task)

    # await socketio_server_instance.on(Events.Order, server_handler)
    # await socketio_server_instance.instance.wait()

    # # hashmap = StrategyMap()

    # pubsub = PubSub(pubsub_client.instance)
    # # await pubsub.jetstream(Streams.DataFrame)

    # async def main_handler(data):
    #     logger.info(f"data received: {data}")
    #     # symbol = data["kline"]["symbol"]
    #     # strategy = hashmap.get_instance(symbol)
    #     # strategy.populate(data)
    #     # payload = {}  # strategy.get_payload()
    #     # await pubsub.publish(Events.DataFrame, payload)
    #     return

    # await pubsub.subscribe(Events.Kline, main_handler)
    # await pubsub.subscribe(Events.Order, main_handler)
    return app


if __name__ == "__main__":
    web.run_app(main(), port=8000, access_log_format=" :: %r %s %T %t")
