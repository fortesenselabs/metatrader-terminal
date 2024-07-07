from abc import ABC
import time
from typing import Dict
from nats.aio.client import Client as NATS
from internal import DWXClient, PubSub
from models import DWXClientParams
from utils import Logger


class BaseHandler(ABC):
    """
    The BaseHandler class provides a foundation for handling various events
    from a trading system. It initializes a DWXClient, starts it, and defines
    methods for handling different types of data and events. Subclasses should
    implement specific event handling methods according to their needs.

    Attributes:
        dwx_client (DWXClient): The client to connect to the trading system.
        logger (Logger): Logger for logging information and errors.
        pubsub (PubSub): Pub/Sub client for message subscriptions.
    """

    def __init__(
        self, dwx_client_params: DWXClientParams, pubsub_client_instance: NATS
    ):
        """
        Initializes the BaseHandler with DWXClient parameters and a Pub/Sub client.

        Args:
            dwx_client_params (DWXClientParams): Parameters required to initialize DWXClient.
            pubsub_client_instance (nats.aio.client.Client): The NATS client for Pub/Sub messaging.
        """
        self.logger = Logger(name=__class__.__name__)

        try:
            self.dwx_client = DWXClient(
                self,
                dwx_client_params.mt_directory_path,
                dwx_client_params.sleep_delay,
                dwx_client_params.max_retry_command_seconds,
                dwx_client_params.verbose,
            )
        except Exception as e:  # Catch more specific errors
            raise ValueError(
                "An error occurred while connecting to MetaTrader: ", e
            ) from e

        time.sleep(1)
        self.dwx_client.start()

        self.pubsub = PubSub(pubsub_client_instance)

    def on_tick(self, symbol, bid, ask):
        """
        Handle incoming tick data.

        Args:
            symbol (str): The symbol of the instrument.
            bid (float): The bid price.
            ask (float): The ask price.
        """
        return

    def on_bar_data(
        self, symbol, time_frame, time, open_price, high, low, close_price, tick_volume
    ):
        """
        Handle incoming bar data.

        Args:
            symbol (str): The symbol of the instrument.
            time_frame (str): The time frame of the data.
            time (str): The time of the bar data.
            open_price (float): The opening price.
            high (float): The highest price.
            low (float): The lowest price.
            close_price (float): The closing price.
            tick_volume (int): The tick volume.
        """
        return

    def on_historic_data(self, symbol, time_frame, data: Dict[str, dict]):
        """
        Handle incoming historic data.

        Args:
            symbol (str): The symbol of the instrument.
            time_frame (str): The time frame of the data.
            data (Dict[str, dict]): The historic data as a dictionary.
        """
        return

    def on_historic_trades(self):
        """
        Handle incoming historic trades data.
        """
        return

    def on_symbols_data(self, symbol_id, symbol_data):
        """
        Handle incoming symbols data.

        Args:
            symbol_id (str): The ID of the symbol.
            symbol_data (dict): The data related to the symbol.
        """
        return

    def on_order_event(self):
        """
        Handle incoming order events.
        """
        return

    def on_message(self, message):
        """
        Handle incoming messages.

        Args:
            message (dict): The message data.
        """
        if message["type"] == "ERROR":
            self.logger.info(
                f"{message['type']} | {message['error_type']} | {message['description']}"
            )
        elif message["type"] == "INFO":
            self.logger.info(f"{message['type']} | {message['message']}")
