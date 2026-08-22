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
    real_balance: Decimal | None = None


class AccountResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    name: str
    type: AccountType
    initial_balance: Decimal
    real_balance: Decimal | None
    created_at: datetime


class InvoicePaymentCreate(BaseModel):
    # Valor abatido da fatura fechada (não precisa ser o total dela — dá pra
    # abater parcial, igual pagamento parcial de fatura de verdade).
    amount: Decimal = Field(gt=0)
    description: str | None = Field(default=None, max_length=255)
