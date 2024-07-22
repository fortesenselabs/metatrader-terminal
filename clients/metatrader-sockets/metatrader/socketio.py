import json
import asyncio
import socketio
from datetime import datetime
from typing import Callable, Union
from .logging import Logger


class SocketIOServerClient:
    """
    A client class for managing Socket.IO server and client connections.

    Attributes:
        instance (Union[socketio.AsyncServer, socketio.AsyncClient]): The Socket.IO server or client instance.
        verbose (bool): Enables verbose logging if set to True.
        log (Logger): Logger instance for logging information and errors.
    """

    instance: Union[socketio.AsyncServer, socketio.AsyncClient]

    def __init__(
        self,
        instance: Union[socketio.AsyncServer, socketio.AsyncClient],
        verbose: bool = False,
    ):
        """
        Initializes the SocketIOServerClient with a given instance.

        Args:
            instance (Union[socketio.AsyncServer, socketio.AsyncClient]): The Socket.IO server or client instance.
            verbose (bool): Enables verbose logging if set to True.
        """
        self.instance = instance
        self.verbose = verbose
        self.log = Logger(name=__class__.__name__) if verbose else None

    @classmethod
    async def create_server(
        cls, namespace="*", verbose: bool = False
    ) -> "SocketIOServerClient":
        """
        Creates a Socket.IO server.

        Args:
            namespace (str, optional): The namespace for the server. Defaults to "*".

        Returns:
            SocketIOServerClient: An instance of the SocketIOServerClient class with a server instance.

        Raises:
            Exception: If the server creation fails.
        """
        try:
            sio = socketio.AsyncServer(async_mode="aiohttp", cors_allowed_origins="*")
            return cls(sio, verbose=verbose)
        except Exception as e:
            if verbose and cls.log:
                cls.log.error(f"Failed to create Socket.IO server: {e}")
            raise

    @classmethod
    async def connect_client(
        cls, url: str, verbose: bool = False
    ) -> "SocketIOServerClient":
        """
        Connects a Socket.IO client to a server.

        Args:
            url (str): The URL of the server to connect to.
            verbose (bool): Enables verbose logging if set to True.

        Returns:
            SocketIOServerClient: An instance of the SocketIOServerClient class with a client instance.

        Raises:
            Exception: If the client connection fails.
        """
        try:
            sio = socketio.AsyncClient()
            await sio.connect(url)
            return cls(sio, verbose=verbose)
        except Exception as e:
            if verbose and cls.log:
                cls.log.error(f"Failed to connect to Socket.IO server: {e}")
            raise

    async def emit(self, event: str, payload: dict, **kwargs):
        """
        Emits an event to the Socket.IO server or client.

        Args:
            event (str): The event name.
            payload (dict): The event data to be emitted.
        """
        try:
            if self.verbose and self.log:
                self.log.info(f"Emitting event: {event}")
            await self.instance.emit(event, payload, **kwargs)
        except Exception as e:
            if self.verbose and self.log:
                self.log.error(f"Socket.IO emit error: {e}")

    async def on_server_event(self, event: str, handler: Callable):
        """
        Registers an event handler for a specific event in the server.

        Args:
            event (str): The event name.
            handler (Callable): The handler function to be called when the event is received.
        """
        try:

            @self.instance.on(event)
            async def event_handler(sid, data):
                if self.verbose and self.log:
                    self.log.info(f"Received server event '{event}' from {sid}")
                data = json.loads(data)
                await handler(sid, data)

        except Exception as e:
            if self.verbose and self.log:
                self.log.error(f"Socket.IO 'on' server event error: {e}")

    async def on_client_event(self, event: str, handler: Callable):
        """
        Registers an event handler for a specific event in the client.

        Args:
            event (str): The event name.
            handler (Callable): The handler function to be called when the event is received.
        """
        try:

            @self.instance.on(event)
            async def event_handler(data):
                if self.verbose and self.log:
                    self.log.info(f"Received client event '{event}'")
                await handler(data)

        except Exception as e:
            if self.verbose and self.log:
                self.log.error(f"Socket.IO 'on' client event error: {e}")

    async def request(
        self, event: str, payload: dict, callback_timeout: int = None
    ) -> dict:
        """
        Sends a request to a specific event and awaits a response.

        Args:
            event (str): The event name.
            payload (dict): The event data to be sent.
            callback_timeout (int, optional): The timeout for the callback. Defaults to None.

        Returns:
            dict: The response from the server or client.

        Raises:
            Exception: If the request fails.
        """
        try:
            if self.verbose and self.log:
                self.log.info(f"Sending request to event: {event}")
            response = await self.instance.emit(
                event, payload, callback_timeout=callback_timeout
            )
            return response
        except Exception as e:
            if self.verbose and self.log:
                self.log.error(f"Socket.IO request error: {e}")

    async def publish(self, event: str, payload: dict):
        """
        Publishes an event to the server or client.

        Args:
            event (str): The event name.
            payload (dict): The event data to be published.
        """
        await self.emit(event, payload)
        if self.verbose and self.log:
            self.log.info(f"Published event: {event}")

    async def subscribe_to_server(self, event: str, handler: Callable):
        """
        Subscribes to a specific event from the server and registers a handler.

        Args:
            event (str): The event name.
            handler (Callable): The handler function to be called when the event is received.
        """
        await self.on_client_event(event, handler)
        if self.verbose and self.log:
            self.log.info(f"Subscribed to Server event: {event}")

    async def subscribe_to_client(self, event: str, handler: Callable):
        """
        Subscribes to a specific event from the client and registers a handler.

        Args:
            event (str): The event name.
            handler (Callable): The handler function to be called when the event is received.
        """
        await self.on_server_event(event, handler)
        if self.verbose and self.log:
            self.log.info(f"Subscribed to Client event: {event}")

    async def unsubscribe_from_server(self, event: str):
        """
        Unsubscribes from a specific event from the server.

        Args:
            event (str): The event name.
        """
        try:
            if self.verbose and self.log:
                self.log.info(f"Unsubscribing from server event: {event}")
            self.instance.off(event)
        except Exception as e:
            if self.verbose and self.log:
                self.log.error(f"Socket.IO 'off' server event error: {e}")

    async def unsubscribe_from_client(self, event: str):
        """
        Unsubscribes from a specific event from the client.

        Args:
            event (str): The event name.
        """
        try:
            if self.verbose and self.log:
                self.log.info(f"Unsubscribing from client event: {event}")
            self.instance.off(event)
        except Exception as e:
            if self.verbose and self.log:
                self.log.error(f"Socket.IO 'off' client event error: {e}")

    async def wait_for_event(
        self,
        event_checker: Callable[[], bool],
        sleep_delay: float = 0.005,
        timeout: int = 60,
    ) -> bool:
        """
        Waits for an event to occur within a timeout period.

        Args:
            event_checker (Callable[[], bool]): The function to check if the event occurred.
            sleep_delay (float): The delay between checks in seconds.
            timeout (int): The maximum time to wait for the event in seconds.

        Returns:
            bool: True if the event occurred within the timeout, False otherwise.
        """
        start_time = datetime.now()
        while (datetime.now() - start_time).seconds < timeout:
            if event_checker():
                return True
            await asyncio.sleep(sleep_delay)
        return False
