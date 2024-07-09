import re
from typing import List
from datetime import datetime, timezone
from models import ServerTimeResponse


def get_server_time() -> ServerTimeResponse:
    """
    Retrieves the current server time as a Unix timestamp and timezone.

    Returns:
        ServerTimeResponse: Current server time with timezone and Unix timestamp.
    """
    now = datetime.now(timezone.utc)
    response = {"timezone": "UTC", "unix_timestamp": int(now.timestamp())}
    return ServerTimeResponse(**response)


def detect_format(date_str: str, formats: List[str]) -> str:
    for date_format in formats:
        try:
            datetime.strptime(date_str, date_format)
            return date_format
        except ValueError:
            continue

    raise ValueError(f"Time data '{date_str}' does not match any known formats.")


def date_to_timestamp(date_str: str) -> int:
    # List of potential date formats
    date_formats = [
        "%Y-%m-%d %H:%M:%S.%f",
        "%Y.%m.%d %H:%M",
        "%Y.%m.%d %H:%M:%S",
        "%Y-%m-%d %H:%M:%S.%f%z",
        "%Y-%m-%d %H:%M:%S%z",
        "%Y-%m-%d %H:%M:%S",
        "%Y-%m-%d %H:%M",
        "%Y/%m/%d %H:%M:%S.%f%z",
        "%Y/%m/%d %H:%M:%S%z",
        "%Y/%m/%d %H:%M:%S",
        "%Y/%m/%d %H:%M",
    ]

    # Detect the correct date format
    date_format = detect_format(date_str, date_formats)

    # Convert the date string to a datetime object
    dt_obj = datetime.strptime(date_str, date_format)

    # Convert the datetime object to a timestamp
    timestamp = int(dt_obj.timestamp())

    return timestamp


def split_by_number(timeframe: str):
    # Regular expression to find the number in the string
    match = re.search(r"(\d+)", timeframe)
    if match:
        # Extract the prefix and the number
        number = match.group(1)
        parts = re.split(number, timeframe)
        return parts[0], number
    return None, None
