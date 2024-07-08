import json
import socketio
from typing import Callable, Union
from utils import Logger


class SocketIOServerClient:
    instance: Union[socketio.AsyncServer, socketio.AsyncClient]
    log = Logger(name=__name__)

    def __init__(self, instance: Union[socketio.AsyncServer, socketio.AsyncClient]):
        self.instance = instance

    @classmethod
    async def create_server(cls, namespace="*"):
        try:
            sio = socketio.AsyncServer(async_mode="aiohttp", cors_allowed_origins="*")
            return cls(sio)
        except Exception as e:
            cls.log.error(f"Failed to create Socket.IO server: {e}")
            raise

    @classmethod
    async def connect_client(cls, url):
        try:
            sio = socketio.AsyncClient()
            await sio.connect(url)
            return cls(sio)
        except Exception as e:
            cls.log.error(f"Failed to connect to Socket.IO server: {e}")
            raise

    async def emit(self, event, payload):
        try:
            self.log.info(f"Emitting event: {event}")
            await self.instance.emit(event, payload)
        except Exception as e:
            self.log.error(f"Socket.IO emit error: {e}")

    async def on(self, event, handler: Callable):
        try:

            @self.instance.on(event)
            async def event_handler(data):
                self.log.info(f"Received event '{event}': {data}")
                await handler(data)

        except Exception as e:
            self.log.error(f"Socket.IO 'on' event error: {e}")

    async def request(self, event, payload, callback_timeout=None):
        try:
            self.log.info(f"Sending request to event: {event}")
            response = await self.instance.emit(
                event, payload, callback_timeout=callback_timeout
            )
            return response
        except Exception as e:
            self.log.error(f"Socket.IO request error: {e}")

    async def publish(self, event, payload):
        await self.emit(event, payload)
        self.log.info(f"Published event: {event}")
        return

    async def subscribe(self, event, handler: Callable):
        await self.on(event, handler)
        self.log.info(f"Subscribed to event: {event}")
        return
