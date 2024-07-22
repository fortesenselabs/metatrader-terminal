import asyncio
import websockets

# Server address and port
address = "127.0.0.1"
port = 7681

# Short message to send back to the client
short_message = "Received your message"


async def echo(websocket, path):
    try:
        async for message in websocket:
            print(f"Received message from client: {message}")
            await websocket.send(short_message)
    except websockets.ConnectionClosed as e:
        print(f"Connection closed: {e}")


async def main():
    async with websockets.serve(echo, address, port):
        print(f"Server started at ws://{address}:{port}")
        await asyncio.Future()  # run forever


if __name__ == "__main__":
    asyncio.run(main())
