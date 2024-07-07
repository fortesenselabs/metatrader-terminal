# PubSub

## Example

```python
import asyncio
from pubsub import PubSub

async def handle_event(data):
    print(f"Received message: {data}")

async def subscribe_to_events(pubsub):
    await pubsub.subscribe("event_name", handle_event)

async def publish_event(pubsub):
    payload = {"key": "value"}
    await pubsub.publish("event_name", payload)

async def cleanup(pubsub):
    await pubsub.instance.close()

async def main():
    # Replace 'nats://localhost:4222' with NATS server URL
    pubsub = await PubSub.connect('nats://localhost:4222')

    try:
        await subscribe_to_events(pubsub)
        await publish_event(pubsub)
        # Other operations...
    finally:
        await cleanup(pubsub)

if __name__ == "__main__":
    loop = asyncio.get_event_loop()
    loop.run_until_complete(main())

```
