"""Schemas Pydantic pra compras parceladas no cartão e fatura mensal."""
from datetime import date, datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field

from app.models.enums import FlowType


class InstallmentPurchaseCreate(BaseModel):
    category_id: str | None = None
    description: str | None = Field(default=None, max_length=255)
    total_amount: Decimal = Field(gt=0)
    installments: int = Field(ge=1, le=48)
    purchase_date: date


class InstallmentResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    card_id: str
    category_id: str | None
    type: FlowType
    amount: Decimal
    description: str | None
    date: datetime
    installment_number: int
    installment_total: int
    purchase_group_id: str


class InvoiceResponse(BaseModel):
    month: str  # "2026-09"
    total: Decimal
    installments: list[InstallmentResponse]
