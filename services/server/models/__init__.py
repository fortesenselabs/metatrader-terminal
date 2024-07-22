from typing import Optional
from pydantic import BaseModel
from .enum_types import *
from .mt_models import *
from .account_models import *
from .exchange_info_models import *
from .kline_models import *
from .orders_models import *
from .events import *


class PingMessage(BaseModel):
    message: str


class ServerTimeResponse(BaseModel):
    timezone: str
    unix_timestamp: int
    server_time: Optional[int] = None


class SystemStatus(Enum):
    NORMAL = 0
    MAINTENANCE = 1


class SystemStatusMessage(Enum):
    NORMAL = "normal"
    MAINTENANCE = "System maintenance"


class SystemStatusResponse(BaseModel):
    status: SystemStatus = SystemStatus.NORMAL
    msg: SystemStatusMessage = SystemStatusMessage.NORMAL


#
# Specify that the time uses standard utc time especially data from metatrader
#
