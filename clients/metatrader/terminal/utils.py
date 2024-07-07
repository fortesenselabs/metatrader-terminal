import time
import json


# def current_timestamp() -> int:
#     return format_timestamp(time.time())


def format_timestamp(t: float) -> int:
    return int(t * 1000)


def new_json(data: bytes) -> dict:
    try:
        return json.loads(data)
    except json.JSONDecodeError as e:
        raise e


def reverse_string(s: str) -> str:
    return s[::-1]


# Utility function
def current_timestamp():
    return int(time.time() * 1000)
