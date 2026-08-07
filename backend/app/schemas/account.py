"""Schemas Pydantic pra contas financeiras."""
from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field

from app.models.enums import AccountType


class AccountCreate(BaseModel):
    name: str = Field(min_length=1, max_length=120)
    type: AccountType = AccountType.CHECKING
    initial_balance: Decimal = Decimal("0")


class AccountUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=120)
    type: AccountType | None = None
    initial_balance: Decimal | None = None


class AccountResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    name: str
    type: AccountType
    initial_balance: Decimal
    created_at: datetime
