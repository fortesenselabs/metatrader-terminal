import time
import random
from time import sleep
from datetime import datetime, timezone, timedelta
from typing import Dict, List, Union
from .dwx_client import DWXClient
from utils import Logger
from typing import Optional
from models import (
    BarDataEvent,
    MTOrderType,
    MTOrderEvent,
    NewOrderEvent,
    SymbolData,
    TickDataEvent,
    MTOrderStatus,
    Kline,
    TimeFrame,
    DataMode,
    OrderType,
    SideType,
    SymbolMarketData,
)
from utils import date_to_timestamp
 

class MetaTraderDataProcessor:
    """
    !!! ----- IMPORTANT ----- !!!

    If open_test_trades=True, it will open many trades.
    """

    def __init__(
        self,
        mt_directory_path: str,
        sleep_delay: float = 0.005,  # 5 ms for time.sleep()
        max_retry_command_seconds: int = 10,  # retry to send the command for 10 seconds if not successful.
        verbose: bool = True,
    ):
        self.logger = Logger(name=__class__.__name__)
        self.mt_directory_path = mt_directory_path
        self.sleep_delay = sleep_delay
        self.max_retry_command_seconds = max_retry_command_seconds
        self.verbose = verbose

        # Flags and initial times
        self.open_test_trades = False
        self.last_open_time = datetime.now(timezone.utc)
        self.last_modification_time = datetime.now(timezone.utc)

        self.logger.info(
            f"MetaTraderDataProcessor.MT_directory_path: {mt_directory_path}"
        )

        # Initialize DWX client
        self.dwx = DWXClient(
            self,
            mt_directory_path,
            sleep_delay,
            max_retry_command_seconds,
            verbose=verbose,
        )
        sleep(1)
        self.dwx.start()

        # Initialize data containers
        self.current_on_tick_data: Optional[TickDataEvent] = None
        self.current_on_bar_data: Optional[BarDataEvent] = None
        self.symbols_data: Dict[int, SymbolData] = {}
        self.historical_klines: Optional[List[Kline]] = None
        self.historic_trades = None

        #
        self.LOW_RAND_RANGE = 0
        self.HIGH_RAND_RANGE = 1e4

        #
        self.orders: Optional[List[NewOrderEvent]] = None

    def wait_for_event(
        self, event_checker, sleep_delay: float = 0.005, timeout: int = 10
    ) -> bool:
        start_time = datetime.now()
        while (datetime.now() - start_time).seconds < timeout:
            if event_checker():
                return True
            sleep(sleep_delay)
        return False

    def orders_event_checker(self):
        return self.orders is not None

    def get_data(
        self, symbol: str, mode: DataMode
    ) -> Union[TickDataEvent, BarDataEvent, None]:
        current_data = None

        if mode != DataMode.BAR:
            current_data = self.current_on_tick_data
        else:
            current_data = self.current_on_bar_data
            self.current_on_bar_data = None

        return current_data

    def active_symbols_event_checker(self):
        return self.symbols_data is not None

    def historical_klines_event_checker(self):
        return self.historical_klines is not None

    def get_active_symbols(self, symbol: str = "") -> List[SymbolData]:
        self.dwx.get_active_symbols(symbol)
        time.sleep(0.5)

        if len(self.dwx.symbols_data) > 0 and len(self.symbols_data) == 0:
            for symbol_id, symbol_data in self.dwx.symbols_data.items():
                self.symbols_data[symbol_id] = SymbolData(**symbol_data)

        if len(symbol) > 0:
            return [
                data for data in self.symbols_data.values() if data.symbol == symbol
            ]

        return list(self.symbols_data.values())

    def get_account_info(self):
        self.logger.info(f"Account info: {self.dwx.account_info}")
        return self.dwx.account_info

    def get_active_symbol_balances(self) -> List:
        balances = []
        active_symbols = self.get_active_symbols()
        for symbol_data in active_symbols:
            balance = {
                "symbol": symbol_data.symbol,
                "free": "0",
                "locked": "0",
            }
            balances.append(balance)

        return balances

    async def get_historic_data(
        self,
        symbol: str = "EURUSD",
        time_frame: str = "D1",
        start: float = (datetime.now(timezone.utc) - timedelta(days=30)).timestamp(),
        end: float = datetime.now(timezone.utc).timestamp(),
    ) -> Union[List[Kline], None]:
        self.dwx.get_historic_data(symbol, time_frame, start, end)
        # TODO: fix 2024.07.02 12:06:59.187	DWX_Server_MT5 (Volatility 50 Index,M1)	INFO:
        # The difference between requested start date and returned start date is relatively large (1862.1 days).
        # Maybe the data is not available on MetaTrader.

        if self.wait_for_event(
            event_checker=self.historical_klines_event_checker, sleep_delay=0.008
        ):
            if self.historical_klines[0].interval != time_frame:
                time.sleep(0.1)

            return self.historical_klines

        return None

    def subscribe_symbols(
        self,
        symbols_data: Optional[List[SymbolMarketData]] = [
            SymbolMarketData(
                symbol="Step Index", time_frame=TimeFrame.M5, mode=DataMode.BAR
            )
        ],
    ):
        if symbols_data is None:
            return []

        subscribed_symbols = []
        for symbol_data in symbols_data:
            if (
                symbol_data.mode != DataMode.TICK
                and symbol_data.time_frame != TimeFrame.CURRENT
            ):
                self.dwx.subscribe_symbols_bar_data(
                    [[symbol_data.symbol, symbol_data.time_frame.value]]
                )
            else:
                self.dwx.subscribe_symbols([symbol_data.symbol])
            subscribed_symbols.append(symbol_data.symbol)

        return subscribed_symbols

    def open_order(
        self,
        symbol: str,
        order_type: MTOrderType,
        price: float,
        lots: float,
        stop_loss: float = 0,
        take_profit: float = 0,
        magic: int = 0,
        comment: str = "",
        expiration: int = 0,
    ) -> MTOrderEvent:
        if magic <= 0:
            magic = random.randint(self.LOW_RAND_RANGE, self.HIGH_RAND_RANGE)

        self.dwx.open_order(
            symbol=symbol,
            order_type=order_type.value.lower(),
            price=price,
            lots=lots,
            stop_loss=stop_loss,
            take_profit=take_profit,
            magic=magic,
            comment=comment,
            expiration=expiration,
        )

        if self.wait_for_event(event_checker=self.orders_event_checker):
            matching_orders: List[NewOrderEvent] = self.search_orders_by_magic(magic)
            if matching_orders:
                order = matching_orders[0]
                mt_order_event = MTOrderEvent(
                    ticket_id=order.ticket_id,
                    magic=order.magic,
                    symbol=order.symbol,
                    lots=order.lots,
                    price=order.open_price,
                    order_type=order.type,
                    status=MTOrderStatus.FILLED,
                )
                return mt_order_event

        return None

    def close_order(
        self,
        ticket_id: Optional[str] = None,
        symbol: Optional[str] = None,
        magic_id: Optional[int] = None,
        lots: int = 0,
        close_all: bool = False,
    ):
        if close_all:
            self.dwx.close_all_orders()
        elif symbol is not None:
            self.dwx.close_orders_by_symbol(symbol=symbol)
        elif magic_id is not None:
            self.dwx.close_orders_by_magic(magic=magic_id)
        elif ticket_id is not None:
            self.dwx.close_order(ticket=ticket_id, lots=lots)
        else:
            # TODO: return an error
            return None

        _orders = None
        if self.wait_for_event(event_checker=self.orders_event_checker):
            _orders = self.on_order_event()

        # if closing multiple orders that are related by something like a symbol,
        # you can sum it together and return it as one order

        return _orders

    def modify_order(self):
        # modify_order
        return

    def get_open_orders(self):
        open_orders = self.dwx.open_orders
        return open_orders

    def search_orders_by_magic(self, magic_id: int) -> List[NewOrderEvent]:
        """
        Search for orders with a specific magic id.

        :param magic_id: The magic id to search for.
        :return: A list of NewOrderEvent instances that match the magic id.
        """
        open_orders = self.on_order_event()

        if open_orders:
            matching_orders = [
                NewOrderEvent(
                    ticket_id=order_data.ticket_id,
                    magic=order_data.magic,
                    symbol=order_data.symbol,
                    lots=order_data.lots,
                    type=order_data.type,
                    open_price=order_data.open_price,
                    open_time=order_data.open_time,
                    sl=order_data.sl,
                    tp=order_data.tp,
                    pnl=order_data.pnl,
                    swap=order_data.swap,
                    comment=order_data.comment,
                )
                for _, order_data in enumerate(self.orders)
                if order_data.magic == magic_id
            ]

            return matching_orders

        return []

    def test_trades(self, now, symbol, bid, ask, lots=0.5):
        # Test trading by randomly opening and closing orders
        if now > self.last_open_time + timedelta(seconds=3):
            self.last_open_time = now
            order_type = (
                MTOrderType.get_mt_order_type(SideType.BUY, OrderType.MARKET)
                if random.random() > 0.5
                else MTOrderType.get_mt_order_type(SideType.SELL, OrderType.MARKET)
            )
            price = ask if order_type == MTOrderType.BUY else bid
            self.open_order(
                symbol=symbol,
                order_type=MTOrderType.get_mt_order_type(
                    SideType.SELL, OrderType.MARKET
                ),
                price=price,
                lots=lots,
            )

        if now > self.last_modification_time + timedelta(seconds=10):
            self.last_modification_time = now
            for ticket in self.dwx.open_orders.keys():
                self.dwx.close_order(ticket, lots=0.1)

        if len(self.dwx.open_orders) >= 10:
            self.dwx.close_all_orders()

    def on_tick(self, symbol, bid, ask):
        now = datetime.now(timezone.utc)
        self.logger.info(f"on_tick: {now}, {symbol}, {bid}, {ask}")

        tick_event = TickDataEvent(
            symbol=symbol,
            time=now.strftime("%Y-%m-%d %H:%M:%S.%f"),  # + "+" + now.strftime("%z"),
            bid=bid,
            ask=ask,
        )

        self.current_on_tick_data = tick_event

        if self.open_test_trades:
            self.test_trades(now, symbol, bid, ask)

    def on_bar_data(
        self, symbol, time_frame, time, open_price, high, low, close_price, tick_volume
    ):
        self.logger.info(
            f"on_bar_data: {symbol}, {time_frame}, {time}, {open_price}, {high}, {low}, {close_price}"
        )

        bar_event = BarDataEvent(
            symbol=symbol,
            time_frame=time_frame,
            time=time,
            open_price=open_price,
            high=high,
            low=low,
            close_price=close_price,
            tick_volume=tick_volume,
            is_final=True,
        )

        self.current_on_bar_data = bar_event

    def on_historic_data(self, symbol, time_frame, data: Dict[str, dict]):
        self.logger.info(f"historic_data: {symbol}, {time_frame}, {len(data)} bars")
        self.historical_klines = [
            Kline(
                start_time=None,
                end_time=None,
                time=date_to_timestamp(_date),
                symbol=symbol,
                interval=time_frame,
                open=kline.get("open"),
                close=kline.get("close"),
                high=kline.get("high"),
                low=kline.get("low"),
                volume=kline.get("tick_volume"),
                is_final=True,
            )
            for _date, kline in data.items()
        ]

    def on_historic_trades(self):
        self.logger.info(f"historic_trades: {len(self.dwx.historic_trades)}")
        self.historic_trades = self.dwx.historic_trades

    def on_message(self, message):
        if message["type"] == "ERROR":
            self.logger.info(
                f"{message['type']} | {message['error_type']} | {message['description']}"
            )
        elif message["type"] == "INFO":
            self.logger.info(f"{message['type']} | {message['message']}")

    def on_symbols_data(self, symbol_id, symbol_data):
        self.symbols_data[symbol_id] = SymbolData(**symbol_data)
        self.logger.info(
            f"on_symbols_data: symbol_id={symbol_id}, symbol_data={symbol_data}"
        )

    def on_order_event(self):
        self.logger.info(
            f"on_order_event. open_orders: {len(self.dwx.open_orders)} open orders"
        )

        if self.dwx.open_orders:
            self.orders = [
                NewOrderEvent(
                    ticket_id=order_id,
                    symbol=order_data.get("symbol"),
                    lots=order_data.get("lots"),
                    type=MTOrderType(order_data.get("type")),
                    magic=order_data.get("magic"),
                    open_price=order_data.get("open_price"),
                    open_time=order_data.get("open_time"),
                    sl=order_data.get("SL", 0.0),
                    tp=order_data.get("TP", 0.0),
                    pnl=order_data.get("pnl", 0.0),
                    swap=order_data.get("swap", 0.0),
                    comment=order_data.get("comment", ""),
                )
                for order_id, order_data in self.dwx.open_orders.items()
            ]
        else:
            self.orders = None

        return self.orders
