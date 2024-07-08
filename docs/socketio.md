# SocketIOServerClient

`SocketIOServerClient` is a Python client class for managing Socket.IO server and client connections asynchronously. It provides an interface to create Socket.IO servers, connect Socket.IO clients to servers, emit events, handle event subscriptions, and manage event callbacks.

## Features

- **Server and Client Connection Management:** Easily create a Socket.IO server or connect a client to an existing server.
- **Event Handling:** Register handlers for both server-side and client-side events.
- **Request-Response Mechanism:** Send requests to specific events and await responses asynchronously.
- **Publish-Subscribe Model:** Publish events to the server or client and subscribe to receive events.
- **Error Logging:** Integrated logging using a provided Logger instance for information and error messages.

## Installation

Ensure you have Python 3.7+ installed. Install the required dependencies:

```bash
pip install -r requirements.txt
```

## Usage

### Creating a Socket.IO Server

```python
import asyncio
from socketio_server_client import SocketIOServerClient

async def main():
    # Create a Socket.IO server
    server = await SocketIOServerClient.create_server(namespace="/chat")

    # Define event handlers
    async def chat_message_handler(sid, data):
        print(f"Received message from {sid}: {data}")

    # Subscribe to 'chat_message' event
    await server.subscribe_to_server('chat_message', chat_message_handler)

if __name__ == "__main__":
    asyncio.run(main())
```

### Connecting a Socket.IO Server

```python
import asyncio
from socketio_server_client import SocketIOServerClient

async def main():
    # Connect to a Socket.IO server
    client = await SocketIOServerClient.connect_client("http://localhost:8080")

    # Define event handlers
    async def server_event_handler(data):
        print(f"Received server event: {data}")

    # Subscribe to 'server_event' event
    await client.subscribe_to_client('server_event', server_event_handler)

if __name__ == "__main__":
    asyncio.run(main())
```

## API Reference

### Class: `SocketIOServerClient`

#### Attributes

- **instance**: Union[socketio.AsyncServer, socketio.AsyncClient]

  - The Socket.IO server or client instance.

- **log**: Logger
  - Logger instance for logging information and errors.

#### Methods

- **create_server(cls, namespace="\*") -> SocketIOServerClient**
  - Creates a Socket.IO server instance.
- **connect_client(cls, url: str) -> SocketIOServerClient**

  - Connects a Socket.IO client to a server instance.

- **emit(event: str, payload: dict, **kwargs)\*\*

  - Emits an event to the Socket.IO server or client.

- **on_server_event(event: str, handler: Callable)**

  - Registers an event handler for a specific event in the server.

- **on_client_event(event: str, handler: Callable)**

  - Registers an event handler for a specific event in the client.

- **request(event: str, payload: dict, callback_timeout: int = None) -> dict**

  - Sends a request to a specific event and awaits a response.

- **publish(event: str, payload: dict)**

  - Publishes an event to the server or client.

- **subscribe_to_server(event: str, handler: Callable)**

  - Subscribes to a specific event from the server and registers a handler.

- **subscribe_to_client(event: str, handler: Callable)**
  - Subscribes to a specific event from the client and registers a handler.
