import json
from aiohttp import web
from models import DWXClientParams, Events, CreateOrderRequest
from settings import Settings
from utils import Logger
from internal import SocketIOServerClient, RequestHandler
from handlers import OrderHandler


logger = Logger(name=__name__)
settings = Settings()


async def main():
    logger.info("MetaTrader 5 API Server is starting up")
    logger.info(f"Settings: {settings.model_dump()}")

    server_instance = await SocketIOServerClient.create_server()
    logger.info("Socket.IO server is running...")
    dwx_client_params = DWXClientParams(mt_directory_path=settings.METATRADER_FILES_DIR)

    try:
        await RequestHandler.setup_event_handlers(dwx_client_params, server_instance)

        app = web.Application()
        server_instance.instance.attach(app)
        # socketio_server_instance.instance.start_background_task(background_task)

        return app
    except Exception as e:
        raise ValueError("An error occurred while initializing handlers: ", e) from e


if __name__ == "__main__":
    web.run_app(main(), port=8000, access_log_format=" :: %r %s %T %t")
