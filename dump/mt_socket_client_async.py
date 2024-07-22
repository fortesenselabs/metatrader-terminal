import os
import json
import asyncio
import socket
import aiofiles
import logging
from os.path import join, exists
from traceback import print_exc
from datetime import datetime, timezone, timedelta
from typing import Dict, List, Tuple


class MTSocketClient:
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
        logger: logging.Logger = None,
    ):

        self.logger = (
            logger if logger is not None else logging.getLogger(__class__.__name__)
        )

        if not exists(metatrader_dir_path):
            self.logger.error("ERROR: metatrader_dir_path does not exist!")
            exit()

        self.event_handler = event_handler
        self.sleep_delay = sleep_delay
        self.max_retry_command_seconds = max_retry_command_seconds
        self.load_orders_from_file = load_orders_from_file
        self.verbose = verbose
        self.command_id = 0

        self.host = host
        self.port = port
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

        self.lock = asyncio.Lock()
        self.ACTIVE = True
        self.START = False

        # Run the initializations in the event loop if already running
        loop = asyncio.get_event_loop()
        if loop.is_running():
            loop.create_task(self.load_messages())
            if self.load_orders_from_file:
                loop.create_task(self.load_orders())
            loop.create_task(self.start())
        else:
            asyncio.run(self.load_messages())
            if self.load_orders_from_file:
                asyncio.run(self.load_orders())
            asyncio.run(self.start())

        self.command_queue = asyncio.Queue()

    async def start(self):
        await self.connect()
        await self.initialize_tasks()
        await self.reset_command_ids()
        self.START = True

    def stop(self):
        self.ACTIVE = False
        self.START = False

    async def connect(self):
        try:
            reader, writer = await asyncio.open_connection(self.host, self.port)
            self.reader = reader
            self.writer = writer
            self.connected = True
            self.logger.info(f"Connected to server at {self.host}:{self.port}")
        except socket.error as e:
            self.logger.error(f"Failed to connect: {e}")

    async def initialize_tasks(self):
        await asyncio.gather(
            self.check_open_orders(),
            self.check_messages(),
            self.check_market_data(),
            self.check_bar_data(),
            self.check_historic_data(),
            self.check_historic_trades(),
            self.check_symbols_data(),
            self.command_worker(),
        )

    async def try_read_file(self, file_path):
        try:
            if exists(file_path):
                async with aiofiles.open(file_path, mode="r") as f:
                    return await f.read()
        except (IOError, PermissionError):
            pass
        except Exception:
            print_exc()
        return ""

    async def try_remove_file(self, file_path):
        try:
            os.remove(file_path)
        except (IOError, PermissionError):
            pass
        except Exception:
            print_exc()

    async def check_open_orders(self):
        while self.ACTIVE:
            await asyncio.sleep(self.sleep_delay)
            if not self.START:
                continue

            text = await self.try_read_file(self.path_orders)
            if not text.strip() or text == self._last_open_orders_str:
                continue

            data = dict(json.loads(text))
            new_event = False

            current_order_ids = set(data["orders"].keys())
            previous_order_ids = set(self.open_orders.keys())

            removed_order_ids = previous_order_ids - current_order_ids
            for order_id in removed_order_ids:
                order = self.open_orders[order_id]
                order["order_id"] = order_id
                order["event_type"] = "Order:Removed"
                new_event = True
                if self.verbose:
                    print("Order removed: ", order)
                self.closed_orders.append(order)

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

            for order in data["orders"].values():
                if "open_time_dt" not in order:
                    order["open_time_dt"] = datetime.strptime(
                        order["open_time"], "%Y.%m.%d %H:%M:%S"
                    )

            sorted_open_orders = dict(
                sorted(data["orders"].items(), key=lambda item: item[1]["open_time_dt"])
            )

            for order in sorted_open_orders.values():
                del order["open_time_dt"]

            self.open_orders = sorted_open_orders
            self.account_info = data["account_info"]

            if self.load_orders_from_file:
                async with aiofiles.open(self.path_orders_stored, mode="w") as f:
                    await f.write(json.dumps(data))

            if self.event_handler and new_event:
                self.event_handler.on_order_event(self.open_orders, self.closed_orders)

            self._last_open_orders_str = text

    async def check_messages(self):
        while self.ACTIVE:
            await asyncio.sleep(self.sleep_delay)
            if not self.START:
                continue

            text = await self.try_read_file(self.path_messages)
            if len(text.strip()) == 0 or text == self._last_messages_str:
                continue

            data = json.loads(text)

            for millis, message in sorted(data.items()):
                if int(millis) > self._last_messages_millis:
                    self._last_messages_millis = int(millis)
                    if self.event_handler is not None:
                        self.event_handler.on_message(message)

            async with aiofiles.open(self.path_messages_stored, mode="w") as f:
                await f.write(json.dumps(data))

            self._last_messages_str = text

    async def check_market_data(self):
        while self.ACTIVE:
            await asyncio.sleep(self.sleep_delay)
            if not self.START:
                continue

            text = await self.try_read_file(self.path_market_data)
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

            self._last_market_data = self.market_data
            self._last_market_data_str = text

    async def check_bar_data(self):
        while self.ACTIVE:
            await asyncio.sleep(self.sleep_delay)
            if not self.START:
                continue

            text = await self.try_read_file(self.path_bar_data)
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

            self._last_bar_data = self.bar_data
            self._last_bar_data_str = text

    async def check_historic_data(self):
        while self.ACTIVE:
            await asyncio.sleep(self.sleep_delay)
            if not self.START:
                continue

            text = await self.try_read_file(self.path_historic_data)
            if len(text.strip()) > 0 and text != self._last_historic_data_str:
                data: dict = json.loads(text)

                for st in data.keys():
                    self.historic_data[st] = data[st]
                    if self.event_handler is not None:
                        symbol, time_frame = st.split("_")
                        self.event_handler.on_historic_data(
                            symbol, time_frame, data[st]
                        )

                self._last_historic_data_str = text
                await self.try_remove_file(self.path_historic_data)

    async def check_historic_trades(self):
        while self.ACTIVE:
            await asyncio.sleep(self.sleep_delay)
            if not self.START:
                continue

            text = await self.try_read_file(self.path_historic_trades)
            if len(text.strip()) > 0 and text != self._last_historic_trades_str:
                self.historic_trades: dict = json.loads(text)

                self.event_handler.on_historic_trades(self.historic_trades)

                self._last_historic_trades_str = text
                await self.try_remove_file(self.path_historic_trades)

    async def check_symbols_data(self):
        while self.ACTIVE:
            await asyncio.sleep(self.sleep_delay)
            if not self.START:
                continue

            text = await self.try_read_file(self.path_symbols_data)
            if len(text.strip()) > 0 and text != self._last_symbols_data_str:
                self.symbols_data = json.loads(text)

                if self.event_handler is not None:
                    print(f"self.symbols_data: {self.symbols_data}")
                    self.event_handler.on_symbols_data(self.symbols_data)

                # temp fix => get fresh symbols data always
                self._last_symbols_data_str = ""
                await self.try_remove_file(self.path_symbols_data)

    async def load_orders(self):
        text = await self.try_read_file(self.path_orders_stored)
        if len(text) > 0:
            data = json.loads(text)
            self.account_info = data["account_info"]
            self.open_orders = data["orders"]
            self._last_open_orders_str = text

    async def load_messages(self):
        text = await self.try_read_file(self.path_messages_stored)
        if len(text) > 0:
            data = json.loads(text)
            # here we don't have to sort because we just need the latest millis value.
            for millis in data.keys():
                if int(millis) > self._last_messages_millis:
                    self._last_messages_millis = int(millis)

            self._last_messages_str = text

    async def command_worker(self):
        while self.ACTIVE:
            command, content = await self.command_queue.get()
            await self.process_command(command, content)
            self.command_queue.task_done()

    async def generate_command_id(self):
        self.command_id = round(datetime.now(timezone.utc).timestamp())
        return self.command_id

    async def process_command(self, command: str, content: str):
        command_id = await self.generate_command_id()
        message = f"<:{command_id}|{command}|{content}:>"
        try:
            self.writer.write(message.encode())
            await self.writer.drain()
            response = await self.reader.read(1024)
            response_data = response.decode()
            self.logger.info("Received from server: " + response_data)
        except socket.error as e:
            self.logger.error(f"Failed to send command: {e}")
            self.connected = False

        # Handle the response as needed

    async def send_command(self, command: str, content: str):
        if self.verbose:
            self.logger.info(f"Pushing Command {command} to queue")

        await self.command_queue.put((command, content))

    async def reset_command_ids(self):
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

        await self.send_command("RESET_COMMAND_IDS", "")

    async def subscribe_symbols(self, symbols):
        """Sends a SUBSCRIBE_SYMBOLS command to subscribe to market (tick) data.

        Args:
            symbols (list[str]): List of symbols to subscribe to.

        Returns:
            None

            The data will be stored in self.market_data.
            On receiving the data the event_handler.on_tick()
            function will be triggered.

        """
        await self.send_command("SUBSCRIBE_SYMBOLS", ",".join(symbols))

    async def subscribe_symbols_bar_data(self, symbols=[["EURUSD", "M1"]]):
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
        await self.send_command(
            "SUBSCRIBE_SYMBOLS_BAR_DATA", ",".join(str(p) for p in data)
        )

    async def get_historic_data(
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
        await self.send_command("GET_HISTORIC_DATA", ",".join(str(p) for p in data))

    async def get_historic_trades(self, lookback_days=30):
        """Sends a GET_HISTORIC_TRADES command to request historic trades.

        Kwargs:
            lookback_days (int): Days to look back into the trade history. The history must also be visible in MT4.

        Returns:
            None

            The data will be stored in self.historic_trades.
            On receiving the data the event_handler.on_historic_trades()
            function will be triggered.
        """

        await self.send_command("GET_HISTORIC_TRADES", str(lookback_days))

    async def get_active_symbols(self, symbol=""):
        """
        Sends a GET_ACTIVE_SYMBOLS command to request either all the active symbols information or the specified symbol's information from the trade server.

        Active symbols are defined are those symbols whose spread > 0.

        Pass an empty symbol parameter to get all available symbols in the trade server.
        """

        await self.send_command("GET_ACTIVE_SYMBOLS", str(symbol))

    async def open_order(
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
        await self.send_command("OPEN_ORDER", ",".join(str(p) for p in data))

    async def modify_order(
        self, ticket, price=0, stop_loss=0, take_profit=0, expiration=0
    ):
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
        await self.send_command("MODIFY_ORDER", ",".join(str(p) for p in data))

    async def close_order(self, ticket: str, lots: float = 0):
        """Sends a CLOSE_ORDER command to close an order.

        Args:
            ticket (int): Ticket of the order that should be closed.

        Kwargs:
            lots (float): Volume in lots. If lots=0 it will try to
                close the complete position.

        """
        data = [ticket, lots]
        await self.send_command("CLOSE_ORDER", ",".join(str(p) for p in data))

    async def close_orders_by_symbol(self, symbol):
        """Sends a CLOSE_ORDERS_BY_SYMBOL command to close all orders
        with a given symbol.

        Args:
            symbol (str): Symbol for which all orders should be closed.

        """

        await self.send_command("CLOSE_ORDERS_BY_SYMBOL", symbol)

    async def close_orders_by_magic(self, magic):
        """Sends a CLOSE_ORDERS_BY_MAGIC command to close all orders
        with a given magic number.

        Args:
            magic (str): Magic number for which all orders should
                be closed.

        """

        await self.send_command("CLOSE_ORDERS_BY_MAGIC", magic)

    async def close_all_orders(self):
        """Sends a CLOSE_ALL_ORDERS command to close all orders."""
        await self.send_command("CLOSE_ALL_ORDERS", "")
