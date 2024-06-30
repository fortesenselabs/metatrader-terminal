from typing import Optional
from pydantic import BaseModel
from .mt_models import *
from .account_info_models import *
from .exchange_info_models import *
from .kline_models import *
from .orders_models import *


class PingMessage(BaseModel):
    message: str


class ServerTimeResponse(BaseModel):
    timezone: str
    unix_timestamp: int
    server_time: Optional[int] = None
