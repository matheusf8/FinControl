"""Schemas Pydantic pra transações (lançamentos de receita/despesa)."""
from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field

from app.models.enums import FlowType


class TransactionCreate(BaseModel):
    account_id: str
    category_id: str | None = None
    type: FlowType
    amount: Decimal = Field(gt=0)  # sempre positivo; o sinal vem do campo "type"
    description: str | None = Field(default=None, max_length=255)
    date: datetime


class TransactionUpdate(BaseModel):
    account_id: str | None = None
    category_id: str | None = None
    type: FlowType | None = None
    amount: Decimal | None = Field(default=None, gt=0)
    description: str | None = Field(default=None, max_length=255)
    date: datetime | None = None


class TransactionResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    account_id: str
    category_id: str | None
    type: FlowType
    amount: Decimal
    description: str | None
    date: datetime
    created_at: datetime
