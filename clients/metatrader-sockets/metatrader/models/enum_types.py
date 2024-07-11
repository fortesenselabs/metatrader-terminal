from datetime import timedelta
from enum import Enum
from typing import List, Union


class AccountType(Enum):
    HEDGING = "HEDGING"

    @classmethod
    def export_all(cls) -> List[str]:
        return [order_type.value for order_type in cls]


class Permission(str, Enum):
    MARGIN = "MARGIN"
    LEVERAGED = "LEVERAGED"

    @classmethod
    def export_all(cls) -> List[str]:
        return [order_type.value for order_type in cls]


class DataMode(Enum):
    TICK = "TICK"
    BAR = "BAR"

    @classmethod
    def export_all(cls) -> List[str]:
        return [order_type.value for order_type in cls]


class Interval(int, Enum):
    CurrentPeriod = 60

    ThirtySeconds = CurrentPeriod // 2
    Minute = 1 * CurrentPeriod
    ThreeMinutes = 3 * CurrentPeriod
    FiveMinutes = 5 * CurrentPeriod
    FifteenMinutes = 15 * CurrentPeriod
    ThirtyMinutes = 30 * CurrentPeriod
    Hour = 1 * CurrentPeriod * CurrentPeriod
    TwoHours = 2 * CurrentPeriod * CurrentPeriod
    FourHours = 4 * CurrentPeriod * CurrentPeriod
    SixHours = 6 * CurrentPeriod * CurrentPeriod
    EightHours = 8 * CurrentPeriod * CurrentPeriod
    TwelveHours = 12 * CurrentPeriod * CurrentPeriod
    Day = 24 * CurrentPeriod * CurrentPeriod
    ThreeDays = 3 * 24 * CurrentPeriod * CurrentPeriod
    Week = 7 * 24 * CurrentPeriod * CurrentPeriod
    Month = 4 * 7 * 24 * CurrentPeriod * CurrentPeriod


class TimeFrame(Enum):
    CURRENT = "CURRENT"
    M1 = "M1"
    M2 = "M2"
    M3 = "M3"
    M4 = "M4"
    M5 = "M5"
    M6 = "M6"
    M10 = "M10"
    M12 = "M12"
    M15 = "M15"
    M20 = "M20"
    M30 = "M30"
    H1 = "H1"
    H2 = "H2"
    H3 = "H3"
    H4 = "H4"
    H6 = "H6"
    H8 = "H8"
    H12 = "H12"
    D1 = "D1"
    W1 = "W1"
    MN1 = "MN1"

    @classmethod
    def from_string(cls, string) -> Union["TimeFrame", None]:
        try:
            return cls[string]
        except KeyError:
            return None

    @classmethod
    def export_all(cls) -> List[str]:
        return [order_type.value for order_type in cls]

    def to_interval(self):
        interval_mapping = {
            self.CURRENT: Interval.CurrentPeriod,
            self.M1: Interval.Minute,
            self.M2: 2 * Interval.CurrentPeriod,
            self.M3: Interval.ThreeMinutes,
            self.M4: 4 * Interval.CurrentPeriod,
            self.M5: Interval.FiveMinutes,
            self.M6: 6 * Interval.CurrentPeriod,
            self.M10: 10 * Interval.CurrentPeriod,
            self.M12: 12 * Interval.CurrentPeriod,
            self.M15: Interval.FifteenMinutes,
            self.M20: 20 * Interval.CurrentPeriod,
            self.M30: Interval.ThirtyMinutes,
            self.H1: Interval.Hour,
            self.H2: Interval.TwoHours,
            self.H3: 3 * Interval.CurrentPeriod * Interval.CurrentPeriod // 60,
            self.H4: Interval.FourHours,
            self.H6: Interval.SixHours,
            self.H8: Interval.EightHours,
            self.H12: Interval.TwelveHours,
            self.D1: Interval.Day,
            self.W1: Interval.Week,
            self.MN1: Interval.Month,
        }

        return interval_mapping.get(self, None)

    def to_timedelta(self) -> timedelta:
        TIMEFRAME_MAP = {
            TimeFrame.M1: timedelta(minutes=1),
            TimeFrame.M2: timedelta(minutes=2),
            TimeFrame.M3: timedelta(minutes=3),
            TimeFrame.M4: timedelta(minutes=4),
            TimeFrame.M5: timedelta(minutes=5),
            TimeFrame.M6: timedelta(minutes=6),
            TimeFrame.M10: timedelta(minutes=10),
            TimeFrame.M12: timedelta(minutes=12),
            TimeFrame.M15: timedelta(minutes=15),
            TimeFrame.M20: timedelta(minutes=20),
            TimeFrame.M30: timedelta(minutes=30),
            TimeFrame.H1: timedelta(hours=1),
            TimeFrame.H2: timedelta(hours=2),
            TimeFrame.H3: timedelta(hours=3),
            TimeFrame.H4: timedelta(hours=4),
            TimeFrame.H6: timedelta(hours=6),
            TimeFrame.H8: timedelta(hours=8),
            TimeFrame.H12: timedelta(hours=12),
            TimeFrame.D1: timedelta(days=1),
            TimeFrame.W1: timedelta(weeks=1),
            TimeFrame.MN1: timedelta(days=30),  # Approximation
        }

        return TIMEFRAME_MAP.get(self, timedelta())
