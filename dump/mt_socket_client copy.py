import os
import json
import queue
import socket
from time import sleep
from threading import Thread, Lock
from os.path import join, exists
from traceback import print_exc
from datetime import datetime, timezone, timedelta
from typing import Dict, List, Tuple

#
# TODO: instead of using file for communication
# why not use file and server as p=you have previously done
# the file would be used for transferring heavy data to the client like historical data
# the server can be a simple sockets server with a text protocol
# <:command:>
#
# the library: socket-library-mt4-mt5.mqh should suffice or you can check the mtservices repo for references
# instead of using json, a lighter protocol can be employed
# or if we opt of just pure text, then we have to compress it before sending it.
#
#


class MTSocketClient:
    """
    MTSocket Client class for interacting with the DWX Expert Advisor (EA) on MetaTrader.

    This class provides methods for sending commands and receiving data such as market data,
    orders, messages, and historical data from MetaTrader. It manages the communication
    via file I/O, allowing interaction with the trading platform.

    Attributes:
        event_handler: An optional event handler for processing incoming events.
        metatrader_dir_path (str): Directory path for MetaTrader files.
        sleep_delay (float): Delay time for polling files (default is 0.005 seconds).
        max_retry_command_seconds (int): Max time to retry sending a command (default is 15).
        load_orders_from_file (bool): Whether to load orders from file at initialization.
        verbose (bool): Enable verbose logging.

        open_orders (dict): Currently open orders.
        closed_orders (list): List of closed orders.
        account_info (dict): Account information.
        market_data (dict): Current market data.
        bar_data (dict): Current bar data.
        historic_data (dict): Historical data.
        historic_trades (dict): Historical trades.
        symbols_data (dict): Symbols data.

    Methods:
        start(): Marks the client as initialized.
        subscribe_symbols(symbols): Subscribe to market data for specified symbols.
        open_order(...): Open a new order.
        modify_order(...): Modify an existing order.
        close_order(...): Close an order.
        get_historic_data(...): Request historical data for a symbol.
        get_historic_trades(...): Request historical trades.
    """

    def __init__(
        self,
        event_handler=None,
        host="127.0.0.1",
        port=5000,
        metatrader_dir_path="",
        sleep_delay=0.005,
        max_retry_command_seconds=15,
        load_orders_from_file=True,
        verbose=True,
    ):
        if not exists(metatrader_dir_path):
            print("ERROR: metatrader_dir_path does not exist!")
            exit()

        self.event_handler = event_handler
        self.sleep_delay = sleep_delay
        self.max_retry_command_seconds = max_retry_command_seconds
        self.load_orders_from_file = load_orders_from_file
        self.verbose = verbose
        self.command_id = 0

        self.host = host
        self.port = port
        self.open_socket = socket.socket()
        self.connected = False

        self.path_orders = join(metatrader_dir_path, "DWX", "DWX_Orders.txt")
        self.path_messages = join(metatrader_dir_path, "DWX", "DWX_Messages.txt")
        self.path_market_data = join(metatrader_dir_path, "DWX", "DWX_Market_Data.txt")
        self.path_bar_data = join(metatrader_dir_path, "DWX", "DWX_Bar_Data.txt")
        self.path_historic_data = join(
            metatrader_dir_path, "DWX", "DWX_Historic_Data.txt"
        )
        self.path_historic_trades = join(
            metatrader_dir_path, "DWX", "DWX_Historic_Trades.txt"
        )
        self.path_symbols_data = join(
            metatrader_dir_path, "DWX", "DWX_Symbols_Data.txt"
        )
        self.path_orders_stored = join(
            metatrader_dir_path, "DWX", "DWX_Orders_Stored.txt"
        )
        self.path_messages_stored = join(
            metatrader_dir_path, "DWX", "DWX_Messages_Stored.txt"
        )
        self.path_commands_prefix = join(metatrader_dir_path, "DWX", "DWX_Commands_")

        self.num_command_files = 50

        self._last_messages_millis = 0
        self._last_open_orders_str = ""
        self._last_messages_str = ""
        self._last_market_data_str = ""
        self._last_bar_data_str = ""
        self._last_historic_data_str = ""
        self._last_historic_trades_str = ""
        self._last_symbols_data_str = ""

        self.open_orders = {}
        self.closed_orders = []
        self.account_info = {}
        self.market_data = {}
        self.bar_data = {}
        self.historic_data = {}
        self.historic_trades = {}
        self.symbols_data = {}

        self._last_bar_data = {}
        self._last_market_data = {}

        self.lock = Lock()
        self.ACTIVE = True
        self.START = False

        self.load_messages()

        if self.load_orders_from_file:
            self.load_orders()

        self.command_queue = queue.Queue()

        if self.event_handler is None:
            self.start()

    def start(self):
        """Marks the client as initialized."""
        self.connect()
        self.initialize_threads()
        self.reset_command_ids()
        self.START = True

    def connect(self):
        try:
            self.open_socket.connect((self.host, self.port))
            self.connected = True
            print(f"Connected to server at {self.host}:{self.port}")
        except socket.error as e:
            print(f"Failed to connect: {e}")

    def initialize_threads(self):
        """Initializes threads for checking various data sources."""
        Thread(target=self.check_open_orders, daemon=True).start()
        Thread(target=self.check_messages, daemon=True).start()
        Thread(target=self.check_market_data, daemon=True).start()
        Thread(target=self.check_bar_data, daemon=True).start()
        Thread(target=self.check_historic_data, daemon=True).start()
        Thread(target=self.check_historic_trades, daemon=True).start()
        Thread(target=self.check_symbols_data, daemon=True).start()

        self.worker_thread = Thread(target=self.command_worker)
        self.worker_thread.daemon = True
        self.worker_thread.start()

    def try_read_file(self, file_path):
        """Attempts to read the contents of a file."""
        try:
            if exists(file_path):
                with open(file_path) as f:
                    return f.read()
        except (IOError, PermissionError):
            pass
        except Exception:
            print_exc()
        return ""

    def try_remove_file(self, file_path):
        """Attempts to remove a specified file."""
        for _ in range(10):
            try:
                os.remove(file_path)
                break
            except (IOError, PermissionError):
                pass
            except Exception:
                print_exc()

    def check_open_orders(self):
        """Regularly checks for open orders and triggers events accordingly."""
        while self.ACTIVE:
            sleep(self.sleep_delay)
            if not self.START:
                continue

            text = self.try_read_file(self.path_orders)
            if not text.strip() or text == self._last_open_orders_str:
                continue

            data = dict(json.loads(text))
            new_event = False

            # Set to keep track of current orders
            current_order_ids = set(data["orders"].keys())
            previous_order_ids = set(self.open_orders.keys())

            # Orders removed
            removed_order_ids = previous_order_ids - current_order_ids
            for order_id in removed_order_ids:
                order = self.open_orders[order_id]
                order["order_id"] = order_id
                order["event_type"] = "Order:Removed"
                new_event = True
                if self.verbose:
                    print("Order removed: ", order)
                self.closed_orders.append(order)

            # New Orders added
            added_order_ids = current_order_ids - previous_order_ids
            for order_id in added_order_ids:
                order = data["orders"][order_id]
                order["order_id"] = order_id
                order["event_type"] = "Order:Created"
                order["open_time_dt"] = datetime.strptime(
                    order["open_time"], "%Y.%m.%d %H:%M:%S"
                )
                new_event = True
                if self.verbose:
                    print("New order: ", order)

            # Ensure all orders have the open_time_dt field
            for order in data["orders"].values():
                if "open_time_dt" not in order:
                    order["open_time_dt"] = datetime.strptime(
                        order["open_time"], "%Y.%m.%d %H:%M:%S"
                    )

            # Sorting orders by open_time
            sorted_open_orders = dict(
                sorted(data["orders"].items(), key=lambda item: item[1]["open_time_dt"])
            )

            for order in sorted_open_orders.values():
                del order["open_time_dt"]

            self.open_orders = sorted_open_orders
            self.account_info = data["account_info"]

            if self.load_orders_from_file:
                with open(self.path_orders_stored, "w") as f:
                    f.write(json.dumps(data))

            if self.event_handler and new_event:
                self.event_handler.on_order_event()

            self._last_open_orders_str = text

    def check_messages(self):
        """Regularly checks for new messages and triggers events."""
        while self.ACTIVE:
            sleep(self.sleep_delay)
            if not self.START:
                continue

            text = self.try_read_file(self.path_messages)
            if len(text.strip()) == 0 or text == self._last_messages_str:
                continue

            self._last_messages_str = text
            data = json.loads(text)

            for millis, message in sorted(data.items()):
                if int(millis) > self._last_messages_millis:
                    self._last_messages_millis = int(millis)
                    if self.event_handler is not None:
                        self.event_handler.on_message(message)

            with open(self.path_messages_stored, "w") as f:
                f.write(json.dumps(data))

    def check_market_data(self):
        """Regularly checks for market data updates and triggers events."""
        while self.ACTIVE:
            sleep(self.sleep_delay)
            if not self.START:
                continue

            text = self.try_read_file(self.path_market_data)
            if len(text.strip()) == 0 or text == self._last_market_data_str:
                continue

            self.market_data = json.loads(text)

            if self.event_handler is not None:
                for symbol in self.market_data.keys():
                    if (
                        symbol not in self._last_market_data
                        or self.market_data[symbol] != self._last_market_data[symbol]
                    ):
                        self.event_handler.on_tick(
                            symbol,
                            self.market_data[symbol]["bid"],
                            self.market_data[symbol]["ask"],
                        )

            self._last_market_data_str = text
            self._last_market_data = self.market_data

    def check_bar_data(self):
        """Regularly checks for bar data updates and triggers events."""
        while self.ACTIVE:
            sleep(self.sleep_delay)
            if not self.START:
                continue

            text = self.try_read_file(self.path_bar_data)
            if len(text.strip()) == 0 or text == self._last_bar_data_str:
                continue
            self.bar_data = json.loads(text)

            if self.event_handler is not None:
                for st in self.bar_data.keys():
                    if (
                        st not in self._last_bar_data
                        or self.bar_data[st] != self._last_bar_data[st]
                    ):
                        symbol, time_frame = st.split("_")
                        self.event_handler.on_bar_data(
                            symbol,
                            time_frame,
                            self.bar_data[st]["time"],
                            self.bar_data[st]["open"],
                            self.bar_data[st]["high"],
                            self.bar_data[st]["low"],
                            self.bar_data[st]["close"],
                            self.bar_data[st]["tick_volume"],
                        )

            self._last_bar_data_str = text
            self._last_bar_data = self.bar_data

    def check_historic_data(self):
        """Checks for historical data and triggers events."""
        while self.ACTIVE:
            sleep(self.sleep_delay)
            if not self.START:
                continue

            text = self.try_read_file(self.path_historic_data)
            if len(text.strip()) > 0 and text != self._last_historic_data_str:
                self.historic_data = json.loads(text)

                for st in dict(self.historic_data).keys():
                    self.historic_data[st] = self.historic_data[st]
                    if self.event_handler is not None:
                        symbol, time_frame = st.split("_")
                        self.event_handler.on_historic_data(
                            symbol, time_frame, self.historic_data[st]
                        )

                    sleep(self.sleep_delay * 2)

                self._last_historic_data_str = text
                self.try_remove_file(self.path_historic_data)

    def check_historic_trades(self):
        """Checks for historical trades and triggers events."""
        while self.ACTIVE:
            sleep(self.sleep_delay)
            if not self.START:
                continue

            text = self.try_read_file(self.path_historic_trades)
            if len(text.strip()) > 0 and text != self._last_historic_trades_str:
                self.historic_trades = json.loads(text)
                self.event_handler.on_historic_trades(self.historic_trades)

                self._last_historic_trades_str = text
                self.try_remove_file(self.path_historic_trades)

    def check_symbols_data(self):
        """Checks for symbols data updates and triggers events."""
        while self.ACTIVE:
            sleep(self.sleep_delay)
            if not self.START:
                continue

            text = self.try_read_file(self.path_symbols_data)
            if len(text.strip()) > 0 and text != self._last_symbols_data_str:
                if self.event_handler is not None:
                    self.symbols_data = json.loads(text)
                    print(self.symbols_data)
                    self.event_handler.on_symbols_data(self.symbols_data)

                self.try_remove_file(self.path_symbols_data)
                self._last_symbols_data_str = ""  # temp fix
                # self._last_symbols_data_str = text

    def load_orders(self):
        """Loads orders from the stored file."""
        text = self.try_read_file(self.path_orders_stored)
        if len(text) > 0:
            self._last_open_orders_str = text
            data = json.loads(text)
            self.account_info = data["account_info"]
            self.open_orders = data["orders"]

    def load_messages(self):
        """Loads messages from the stored file."""
        text = self.try_read_file(self.path_messages_stored)
        if len(text) > 0:
            self._last_messages_str = text
            data = json.loads(text)

            # here we don't have to sort because we just need the latest millis value.
            for millis in data.keys():
                if int(millis) > self._last_messages_millis:
                    self._last_messages_millis = int(millis)

    def reset_command_ids(self):
        """Resets the command IDs."""
        self.command_id = 0
        self._last_open_orders_str = ""
        self._last_messages_str = ""
        self._last_market_data_str = ""
        self._last_bar_data_str = ""
        self._last_historic_data_str = ""
        self._last_historic_trades_str = ""
        self._last_symbols_data_str = ""
        self._last_messages_millis = 0

        self.send_command("RESET_COMMAND_IDS", "")

    def command_worker(self):
        """Processes commands from the command queue."""
        while self.ACTIVE:
            try:
                command, content = self.command_queue.get(timeout=1)
                self.execute_command(command, content)
            except queue.Empty:
                continue

    def generate_command_id(self):
        now = datetime.now(timezone.utc)
        return round(now.timestamp())

    def execute_command(self, command, content):
        """Executes a command by writing to the appropriate command file."""
        self.lock.acquire()
        # self.command_id = (self.command_id + 1) % 100000
        # end_time = datetime.now(timezone.utc) + timedelta(
        #     seconds=self.max_retry_command_seconds
        # )
        if not self.connected:
            print("Not connected to server.")
            return

        command_id = self.generate_command_id()
        message = f"<:{command_id}|{command}|{content}:>"
        try:
            self.open_socket.send(message.encode())
            data = self.open_socket.recv(1024).decode()
            print("Received from server: " + data)
            self.command_queue.task_done()
        except socket.error as e:
            print(f"Failed to send command: {e}")
            self.connected = False

        self.lock.release()

    def send_command(self, command: str, content):
        """Adds a command to the command queue for processing."""
        if self.verbose:
            print(f"Pushing Command {command} to queue")

        # if command.strip() != "RESET_COMMAND_IDS":
        #     sleep(self.sleep_delay)
        # else:
        #     sleep(self.sleep_delay / 2)

        if self.connected:
            self.command_queue.put((command, content))

    def subscribe_symbols(self, symbols):
        """Sends a SUBSCRIBE_SYMBOLS command to subscribe to market (tick) data.

        Args:
            symbols (list[str]): List of symbols to subscribe to.

        Returns:
            None

            The data will be stored in self.market_data.
            On receiving the data the event_handler.on_tick()
            function will be triggered.

        """
        self.send_command("SUBSCRIBE_SYMBOLS", ",".join(symbols))

    def subscribe_symbols_bar_data(self, symbols=[["EURUSD", "M1"]]):
        """Sends a SUBSCRIBE_SYMBOLS_BAR_DATA command to subscribe to bar data.

        Kwargs:
            symbols (list[list[str]]): List of lists containing symbol/time frame
            combinations to subscribe to. For example:
            symbols = [['EURUSD', 'M1'], ['GBPUSD', 'H1']]

        Returns:
            None

            The data will be stored in self.bar_data.
            On receiving the data the event_handler.on_bar_data()
            function will be triggered.

        """
        data = [f"{st[0]},{st[1]}" for st in symbols]
        self.send_command("SUBSCRIBE_SYMBOLS_BAR_DATA", ",".join(str(p) for p in data))

    def get_historic_data(
        self,
        symbol="EURUSD",
        time_frame="D1",
        start=(datetime.now(timezone.utc) - timedelta(days=30)).timestamp(),
        end=datetime.now(timezone.utc).timestamp(),
    ):
        """Sends a GET_HISTORIC_DATA command to request historic data.

        Kwargs:
            symbol (str): Symbol to get historic data.
            time_frame (str): Time frame for the requested data.
            start (int): Start timestamp (seconds since epoch) of the requested data.
            end (int): End timestamp of the requested data.

        Returns:
            None

            The data will be stored in self.historic_data.
            On receiving the data the event_handler.on_historic_data()
            function will be triggered.
        """

        # start_date.strftime('%Y.%m.%d %H:%M:00')
        data = [symbol, time_frame, int(start), int(end)]
        self.send_command("GET_HISTORIC_DATA", ",".join(str(p) for p in data))

    def get_historic_trades(self, lookback_days=30):
        """Sends a GET_HISTORIC_TRADES command to request historic trades.

        Kwargs:
            lookback_days (int): Days to look back into the trade history. The history must also be visible in MT4.

        Returns:
            None

            The data will be stored in self.historic_trades.
            On receiving the data the event_handler.on_historic_trades()
            function will be triggered.
        """

        self.send_command("GET_HISTORIC_TRADES", str(lookback_days))

    def get_active_symbols(self, symbol=""):
        """
        Sends a GET_ACTIVE_SYMBOLS command to request either all the active symbols information or the specified symbol's information from the trade server.

        Active symbols are defined are those symbols whose spread > 0.

        Pass an empty symbol parameter to get all available symbols in the trade server.
        """

        self.send_command("GET_ACTIVE_SYMBOLS", str(symbol))

    def open_order(
        self,
        symbol="EURUSD",
        order_type="buy",
        lots=0.01,
        price=0,
        stop_loss=0,
        take_profit=0,
        magic=0,
        comment="",
        expiration=0,
    ):
        """Sends an OPEN_ORDER command to open an order.

        Kwargs:
            symbol (str): Symbol for which an order should be opened.
            order_type (str): Order type. Can be one of:
                'buy', 'sell', 'buylimit', 'selllimit', 'buystop', 'sellstop'
            lots (float): Volume in lots
            price (float): Price of the (pending) order. Can be zero
                for market orders.
            stop_loss (float): SL as absoute price. Can be zero
                if the order should not have an SL.
            take_profit (float): TP as absoute price. Can be zero
                if the order should not have a TP.
            magic (int): Magic number
            comment (str): Order comment
            expiration (int): Expiration time given as timestamp in seconds.
                Can be zero if the order should not have an expiration time.

        """

        data = [
            symbol,
            order_type,
            lots,
            price,
            stop_loss,
            take_profit,
            magic,
            comment,
            expiration,
        ]
        self.send_command("OPEN_ORDER", ",".join(str(p) for p in data))

    def modify_order(self, ticket, price=0, stop_loss=0, take_profit=0, expiration=0):
        """Sends a MODIFY_ORDER command to modify an order.

        Args:
            ticket (int): Ticket of the order that should be modified.

        Kwargs:
            price (float): Price of the (pending) order. Non-zero only
                works for pending orders.
            stop_loss (float): New stop loss price.
            take_profit (float): New take profit price.
            expiration (int): New expiration time given as timestamp in seconds.
                Can be zero if the order should not have an expiration time.

        """
        data = [ticket, price, stop_loss, take_profit, expiration]
        self.send_command("MODIFY_ORDER", ",".join(str(p) for p in data))

    def close_order(self, ticket: str, lots: float = 0):
        """Sends a CLOSE_ORDER command to close an order.

        Args:
            ticket (int): Ticket of the order that should be closed.

        Kwargs:
            lots (float): Volume in lots. If lots=0 it will try to
                close the complete position.

        """
        data = [ticket, lots]
        self.send_command("CLOSE_ORDER", ",".join(str(p) for p in data))

    def close_orders_by_symbol(self, symbol):
        """Sends a CLOSE_ORDERS_BY_SYMBOL command to close all orders
        with a given symbol.

        Args:
            symbol (str): Symbol for which all orders should be closed.

        """

        self.send_command("CLOSE_ORDERS_BY_SYMBOL", symbol)

    def close_orders_by_magic(self, magic):
        """Sends a CLOSE_ORDERS_BY_MAGIC command to close all orders
        with a given magic number.

        Args:
            magic (str): Magic number for which all orders should
                be closed.

        """

        self.send_command("CLOSE_ORDERS_BY_MAGIC", magic)

    def close_all_orders(self):
        """Sends a CLOSE_ALL_ORDERS command to close all orders."""
        self.send_command("CLOSE_ALL_ORDERS", "")
