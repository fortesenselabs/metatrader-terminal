import os
import re
import shutil
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


def delete_folder(folder_path):
    """Deletes a folder and all its contents."""
    if not os.path.exists(folder_path):
        raise FileNotFoundError(f"Folder '{folder_path}' does not exist.")
    try:
        shutil.rmtree(folder_path)
        print(f"Folder '{folder_path}' deleted successfully.")
    except PermissionError:
        raise PermissionError(
            f"Permission denied: Unable to delete folder '{folder_path}'."
        )
    except Exception as e:
        raise RuntimeError(f"Error deleting folder '{folder_path}': {e}")


def ensure_directory_exists(dir_path):
    """Ensures that a directory exists. If it doesn't, create it."""
    if not os.path.exists(dir_path):
        try:
            os.makedirs(dir_path)
            print(f"Directory '{dir_path}' created successfully.")
        except PermissionError:
            raise PermissionError(
                f"Permission denied: Unable to create directory '{dir_path}'."
            )
        except Exception as e:
            raise RuntimeError(f"Error creating directory '{dir_path}': {e}")
    else:
        print(f"Directory '{dir_path}' already exists.")
