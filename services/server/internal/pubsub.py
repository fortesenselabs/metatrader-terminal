import json
import nats
from nats.aio.client import Client as NATS
from nats.aio.errors import ErrConnectionClosed, ErrTimeout
from utils import Logger


class PubSub:
    instance: NATS
    log = Logger(name=__name__)

    def __init__(self, instance: NATS):
        self.instance = instance

    @classmethod
    async def connect(cls, url):
        try:
            cls.instance = await nats.connect(url)
            return cls(cls.instance)
        except Exception as e:
            cls.log.error(f"Failed to connect to NATS server: {e}")
            raise

    async def subscribe(self, event, handler):
        try:
            sub = await self.instance.subscribe(event)
            self.log.info(f"Subscribed to event: {event}")
            async for msg in sub.messages:
                try:
                    data = json.loads(msg.data.decode())
                    await handler(data)
                except Exception as e:
                    self.log.error(f"Error processing message: {e}")
        except (ErrConnectionClosed, ErrTimeout) as e:
            self.log.error(f"NATS connection error: {e}")

    async def publish(self, event, payload):
        try:
            self.log.info(f"Publishing event: {event}")
            data = json.dumps(payload).encode("utf-8")
            await self.instance.publish(event, data)
        except (ErrConnectionClosed, ErrTimeout) as e:
            self.log.error(f"NATS connection error: {e}")

    async def request(self, subject, payload, timeout=1):
        try:
            self.log.info(f"Sending request to subject: {subject}")
            data = json.dumps(payload).encode("utf-8")
            response = await self.instance.request(subject, data, timeout=timeout)
            return json.loads(response.data.decode())
        except (ErrConnectionClosed, ErrTimeout) as e:
            self.log.error(f"NATS connection error: {e}")

    async def jetstream(self, config):
        try:
            js = self.instance.jetstream()
            await js.add_stream(**config)
        except (ErrConnectionClosed, ErrTimeout) as e:
            self.log.error(f"NATS connection error: {e}")
