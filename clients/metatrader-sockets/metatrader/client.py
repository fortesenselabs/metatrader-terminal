import json
import asyncio
from datetime import datetime
from typing import Any, Optional, Callable
from metatrader.models import Events, AccountInfoResponse, ExchangeInfoResponse
from metatrader.logging import Logger
from metatrader.socketio import SocketIOServerClient


class TerminalClient:
    """
    A client to interact with the MetaTrader terminal via socket.io.

    Attributes:
        url (str): The URL of the MetaTrader socket.io server.
        verbose (bool): Enables verbose logging if set to True.
        session_data (dict): Stores the data received during the session.
    """

    def __init__(self, url: str = "http://localhost:8000", verbose: bool = False):
        """
        Initializes the TerminalClient.

        Args:
            url (str): The URL of the MetaTrader socket.io server.
            verbose (bool): Enables verbose logging if set to True.
        """
        self.verbose = verbose
        self.url = url
        self.empty_request = "{}"
        self.client_instance: Optional[SocketIOServerClient] = None
        self.session_data = {}
        self.logger = None

    @classmethod
    async def create(cls, url: str = "http://localhost:8000", verbose: bool = False):
        """
        Asynchronously creates an instance of TerminalClient.

        Args:
            url (str): The URL of the MetaTrader socket.io server.
            verbose (bool): Enables verbose logging if set to True.

        Returns:
            TerminalClient: The initialized TerminalClient instance.
        """
        self = cls(url, verbose)
        await self.connect()
        return self

    async def connect(self):
        """
        Connects to the MetaTrader socket.io server.
        """
        self.client_instance = await SocketIOServerClient.connect_client(self.url)
        if self.verbose:
            self.logger = Logger(name=__class__.__name__)
            self.logger.info(
                f"Connected to Server at {self.url}: {self.client_instance.instance.connected}"
            )
        return self.client_instance

    async def subscribe_to_event(self, event: str):
        """
        Subscribes to a specified event and stores the received data in session_data.

        Args:
            event (str): The event to subscribe to.
        """

        async def handler(data):
            self.session_data[event] = json.loads(data)

        await self.client_instance.subscribe_to_server(event, handler)

    async def publish_event(self, event: str, data: str):
        """
        Publishes data to a specified event.

        Args:
            event (str): The event to publish data to.
            data (str): The data to publish.
        """
        await self.client_instance.publish(event, data)

    async def wait_for_event(
        self,
        event_checker: Callable[[], bool],
        sleep_delay: float = 0.005,
        timeout: int = 10,
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

    def clear_session_data(self, event: str):
        """
        Clears the session data for a specific event.

        Args:
            event (str): The event for which to clear the session data.
        """
        if event in self.session_data:
            del self.session_data[event]

    async def get_account(self) -> Optional[AccountInfoResponse]:
        """
        Fetches the account information.

        Returns:
            AccountInfoResponse: The account information response.
        """
        await self.subscribe_to_event(Events.Account)
        await self.publish_event(Events.Account, self.empty_request)

        if await self.wait_for_event(lambda: Events.Account in self.session_data):
            account_info = self.session_data.get(Events.Account)
            self.clear_session_data(Events.Account)
            return AccountInfoResponse(**account_info)

        return None

    async def get_exchange_info(self) -> Optional[ExchangeInfoResponse]:
        """
        Fetches the exchange information.

        Returns:
            ExchangeInfoResponse: The exchange information response.
        """
        await self.subscribe_to_event(Events.ExchangeInfo)
        await self.publish_event(Events.ExchangeInfo, self.empty_request)

        if await self.wait_for_event(lambda: Events.ExchangeInfo in self.session_data):
            exchange_info = self.session_data.get(Events.ExchangeInfo)
            self.clear_session_data(Events.ExchangeInfo)
            return ExchangeInfoResponse(**exchange_info)

        return None

    def run(self, tasks: list[Callable]):
        """
        Runs the specified tasks.

        Args:
            tasks (list[Callable]): The list of tasks to run.
        """
        asyncio.run(self._run(tasks))

    async def _run(self, tasks: list[Callable]):
        """
        Internal method to run the specified tasks.

        Args:
            tasks (list[Callable]): The list of tasks to run.
        """
        await self.connect()
        await asyncio.gather(*[task() for task in tasks])
        # try:
        #     await asyncio.Event().wait()
        # except KeyboardInterrupt:
        #     if self.logger:
        #         self.logger.info("Shutting down...")
