from aiohttp import web
from models import MTClientParams
from settings import Settings
from utils import Logger
from internal import SocketIOServerClient, MTSocketClient
from handlers import RequestHandler


logger = Logger(name=__name__)
settings = Settings()


async def main():
    logger.info(f"Settings: {settings.model_dump()}")

    server_instance = await SocketIOServerClient.create_server(verbose=True)
    logger.info("Created Socket.IO Server Instance...")

    mt_client_params = MTClientParams(mt_directory_path=settings.METATRADER_FILES_DIR)

    try:
        logger.info("Setting up Event Handlers...")
        await RequestHandler.setup_event_handlers(mt_client_params, server_instance)

        logger.info("Attaching Application to Server Instance...")
        app = web.Application()
        server_instance.instance.attach(app)
        # socketio_server_instance.instance.start_background_task(background_task)

        return app
    except Exception as e:
        message = f"An error occurred while initializing API Server: {e}"
        logger.exception(message)
        raise ValueError(message) from e


if __name__ == "__main__":
    logger.info("API Server is starting up")
    web.run_app(main(), port=settings.PORT, access_log_format=" :: %r %s %T %t")


#
# TODO:
# To slow down the server OR to ensure a synchronous operation
# Why don you implement or add a Queue or Cache to the server
#
