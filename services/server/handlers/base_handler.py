from abc import ABC, abstractmethod
from typing import Dict
from internal import MTSocketClient, SocketIOServerClient
from models import MTClientParams
from utils import Logger


class BaseHandler(ABC):
    """
    The BaseHandler class provides a foundation for handling various events
    from a trading system. It initializes a MTSocketClient, starts it, and defines
    methods for handling different types of data and events. Subclasses should
    implement specific event handling methods according to their needs.

    Attributes:
        mt_socket_client (MTSocketClient): The client to connect to the trading system.
        logger (Logger): Logger for logging information and errors.
        pubsub (SocketIOServerClient): Pub/Sub client for message subscriptions.
    """

    def __init__(
        self,
        mt_client_params: MTClientParams,
        pubsub_instance: SocketIOServerClient,
        verbose: bool = False,
    ):
        """
        Initializes the BaseHandler with MTSocketClient and a Pub/Sub client.

        Args:
            mt_socket_client (MTSocketClient): Parameters required to initialize MTSocketClient.
            pubsub_instance (SocketIOServerClient): The client for Pub/Sub messaging.
        """
        self.logger = Logger(name=__class__.__name__)
        self.verbose = verbose

        try:
            self.logger.info("Setting up MetaTrader Socket Client...")
            self.socket_client = MTSocketClient(
                self,
                metatrader_dir_path=mt_client_params.mt_directory_path,
                sleep_delay=mt_client_params.sleep_delay,
                max_retry_command_seconds=mt_client_params.max_retry_command_seconds,
                verbose=mt_client_params.verbose,
                logger=None,
            )
            self.socket_client.clean_files()
            self.socket_client.start()
        except Exception as e:  # Catch more specific errors
            raise ValueError(
                "An error occurred while connecting to MetaTrader: ", e
            ) from e

        self.pubsub = pubsub_instance

    def on_tick(self, symbol, bid, ask):
        """
        Handle incoming tick data.

        Args:
            symbol (str): The symbol of the instrument.
            bid (float): The bid price.
            ask (float): The ask price.
        """
        pass

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
        pass

    def on_historic_data(self, symbol, time_frame, data: Dict[str, dict]):
        """
        Handle incoming historic data.

        Args:
            symbol (str): The symbol of the instrument.
            time_frame (str): The time frame of the data.
            data (Dict[str, dict]): The historic data as a dictionary.
        """
        pass

    def on_historic_trades(self, data: dict):
        """
        Handle incoming historic trades data.
        """
        pass

    def on_symbols_data(self, symbols_data):
        """
        Handle incoming symbols data.

        Args:
            symbols_data (dict): The data related to the symbol.
        """
        pass

    def on_order_event(self, open_orders, closed_orders):
        """
        Handle incoming order events.
        """
        pass

    def on_message(self, message):
        """
        Handle incoming messages.

        Args:
            message (dict): The message data.
        """
        if self.verbose:
            if message["type"] == "ERROR":
                self.logger.error(
                    f"| {message['type']} | {message['error_type']} | {message['description']}"
                )

            if message["type"] == "INFO":
                self.logger.info(f"| {message['type']} | {message['message']}")
