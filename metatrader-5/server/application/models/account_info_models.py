from enum import Enum
from typing import List
from pydantic import BaseModel
from application.models.symbol_models import SymbolBalance
from application.models.enum_types import AccountType, Permission


# Define fields for account information (e.g., balance, equity, etc.)
class AccountInfoResponse(BaseModel):
    name: str
    uid: int
    currency: str
    leverage: int
    free_margin: float
    balance: float
    equity: float
    can_trade: bool
    can_withdraw: bool
    can_deposit: bool
    update_time: int
    account_type: AccountType
    balances: List[SymbolBalance]
    permissions: List[Permission]
