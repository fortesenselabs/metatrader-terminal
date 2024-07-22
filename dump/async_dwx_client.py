import os
import json
import asyncio
import aiofiles
from datetime import datetime, timezone, timedelta
from os.path import join, exists
from traceback import print_exc


class DWXClient:
    """
    DWX Client class for interacting with the DWX EA on Metatrader.
    """

    def __init__(
        self,
        event_handler=None,
        metatrader_dir_path="",
        sleep_delay=0.005,  # 5 ms for asyncio.sleep()
        max_retry_command_seconds=10,  # retry to send the command for 10 seconds if not successful
        load_orders_from_file=True,  # to load orders from file on initialization
        verbose=True,
    ):
        self.event_handler = event_handler
        self.sleep_delay = sleep_delay
        self.max_retry_command_seconds = max_retry_command_seconds
        self.load_orders_from_file = load_orders_from_file
        self.verbose = verbose
        self.command_id = 0

        self.async_loop = asyncio.get_event_loop()

        if not exists(metatrader_dir_path):
            print("ERROR: metatrader_dir_path does not exist!")
            exit()

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

        self.ACTIVE = True
        self.START = False

        self.lock = asyncio.Lock()

        self.async_loop.create_task(self.load_messages())

        if self.load_orders_from_file:
            self.async_loop.create_task(self.load_orders())

        # self.tasks = asyncio.create_task(
        #     [
        #         self.check_messages,
        #         self.check_market_data,
        #         self.check_bar_data,
        #         self.check_open_orders,
        #         self.check_historic_data,
        #         self.check_symbols_data,
        #     ]
        # )

        self.reset_command_ids()

        if self.event_handler is None:
            self.start()

    def start(self):
        self.START = True

    async def try_read_file(self, file_path):
        try:
            if exists(file_path):
                async with aiofiles.open(file_path, mode="r") as f:
                    return await f.read()
        except (IOError, PermissionError):
            pass
        except:
            print_exc()
        return ""

    async def try_remove_file(self, file_path):
        for _ in range(10):
            try:
                os.remove(file_path)
                break
            except (IOError, PermissionError):
                pass
            except:
                print_exc()

    async def check_open_orders(self):
        while self.ACTIVE:
            await asyncio.sleep(self.sleep_delay)
            if not self.START:
                continue

            text = await self.try_read_file(self.path_orders)
            if not text.strip() or text == self._last_open_orders_str:
                continue

            self._last_open_orders_str = text
            data = json.loads(text)
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
                self.event_handler.on_order_event()

    async def check_messages(self):
        while self.ACTIVE:
            await asyncio.sleep(self.sleep_delay)
            if not self.START:
                continue

            text = await self.try_read_file(self.path_messages)
            if len(text.strip()) == 0 or text == self._last_messages_str:
                continue

            self._last_messages_str = text
            data = json.loads(text)

            for millis, message in sorted(data.items()):
                if int(millis) > self._last_messages_millis:
                    self._last_messages_millis = int(millis)
                    if self.event_handler is not None:
                        self.event_handler.on_message(message)

            async with aiofiles.open(self.path_messages_stored, mode="w") as f:
                await f.write(json.dumps(data))

    async def check_market_data(self):
        while self.ACTIVE:
            await asyncio.sleep(self.sleep_delay)
            if not self.START:
                continue

            text = await self.try_read_file(self.path_market_data)
            if len(text.strip()) == 0 or text == self._last_market_data_str:
                continue

            self._last_market_data_str = text
            data = json.loads(text)
            self.market_data = data

            if self.event_handler is not None:
                for symbol in data.keys():
                    if (
                        symbol not in self._last_market_data
                        or self.market_data[symbol] != self._last_market_data[symbol]
                    ):
                        self.event_handler.on_tick(
                            symbol,
                            self.market_data[symbol]["bid"],
                            self.market_data[symbol]["ask"],
                        )
            self._last_market_data = data

    async def check_bar_data(self):
        while self.ACTIVE:
            await asyncio.sleep(self.sleep_delay)
            if not self.START:
                continue

            text = await self.try_read_file(self.path_bar_data)
            if len(text.strip()) == 0 or text == self._last_bar_data_str:
                continue

            self._last_bar_data_str = text
            data = json.loads(text)
            self.bar_data = data

            if self.event_handler is not None:
                for st in data.keys():
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
            self._last_bar_data = data

    async def check_historic_data(self):
        while self.ACTIVE:
            await asyncio.sleep(self.sleep_delay)
            if not self.START:
                continue

            text = await self.try_read_file(self.path_historic_data)
            if len(text.strip()) == 0 or text == self._last_historic_data_str:
                continue

            self._last_historic_data_str = text
            data = json.loads(text)
            self.historic_data = data

            if self.event_handler is not None:
                for st in data.keys():
                    symbol, time_frame = st.split("_")
                    self.event_handler.on_historic_data(
                        symbol,
                        time_frame,
                        self.historic_data[st]["time"],
                        self.historic_data[st]["open"],
                        self.historic_data[st]["high"],
                        self.historic_data[st]["low"],
                        self.historic_data[st]["close"],
                        self.historic_data[st]["tick_volume"],
                    )

    async def check_symbols_data(self):
        while self.ACTIVE:
            await asyncio.sleep(self.sleep_delay)
            if not self.START:
                continue

            text = await self.try_read_file(self.path_symbols_data)
            if len(text.strip()) > 0 and text != self._last_symbols_data_str:
                self._last_symbols_data_str = text
                data = json.loads(text)
                self.symbols_data = data

                if self.event_handler is not None:
                    self.event_handler.on_symbols_data(data)

    def stop(self):
        self.ACTIVE = False
        self.START = False

    def reset_command_ids(self):
        for i in range(self.num_command_files):
            command_file = self.path_commands_prefix + str(i) + ".txt"
            asyncio.run(self.try_remove_file(command_file))

    async def send_command(self, action, **kwargs):
        async with self.lock:
            timestamp = str(datetime.now().timestamp())
            filename = self.path_commands_prefix + str(self.command_id) + ".txt"

            command = {"action": action, "timestamp": timestamp}
            command.update(kwargs)

            for _ in range(self.max_retry_command_seconds):
                try:
                    async with aiofiles.open(filename, mode="w") as f:
                        await f.write(json.dumps(command))
                        self.command_id += 1
                        return filename
                except:
                    await asyncio.sleep(self.sleep_delay)
                    self.command_id = (self.command_id + 1) % self.num_command_files
            return None

    async def load_orders(self):
        if exists(self.path_orders_stored):
            text = await self.try_read_file(self.path_orders_stored)
            if len(text.strip()) > 0:
                data = json.loads(text)
                self.open_orders = data["orders"]
                self.account_info = data["account_info"]

    async def load_messages(self):
        if exists(self.path_messages_stored):
            text = await self.try_read_file(self.path_messages_stored)
            if len(text.strip()) > 0:
                data = json.loads(text)
                self._last_messages_millis = max(map(int, data.keys()))
                if self.event_handler is not None:
                    for millis, message in sorted(data.items()):
                        self.event_handler.on_message(message)
