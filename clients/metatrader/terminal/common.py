import math
import json
from io import BytesIO


# helpers.py
def amount_to_lot_size(lot: float, precision: int, amount: float) -> float:
    return math.trunc(math.floor(amount / lot) * lot * 10**precision) / 10**precision


def to_json_list(v: bytes) -> bytes:
    if len(v) > 0 and v[0] == ord("{"):
        buffer = BytesIO()
        buffer.write(b"[")
        buffer.write(v)
        buffer.write(b"]")
        return buffer.getvalue()
    return v


# Example usage
# if __name__ == "__main__":
#     lot_size = amount_to_lot_size(0.1, 2, 123.456)
#     print(f"Lot size: {lot_size}")

#     json_bytes = to_json_list(b'{"key": "value"}')
#     print(f"JSON list: {json_bytes.decode()}")

#     api_error = APIError(404, "Not Found")
#     print(str(api_error))
#     print(is_api_error(api_error))
#     print(is_api_error(ValueError("A different error")))
