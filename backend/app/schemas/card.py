"""Schemas Pydantic pra cartões de crédito."""
from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field


class CardCreate(BaseModel):
    name: str = Field(min_length=1, max_length=120)
    closing_day: int = Field(ge=1, le=31)
    due_day: int = Field(ge=1, le=31)
    limit: Decimal = Decimal("0")


class CardUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=120)
    closing_day: int | None = Field(default=None, ge=1, le=31)
    due_day: int | None = Field(default=None, ge=1, le=31)
    limit: Decimal | None = None


class CardResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    name: str
    closing_day: int
    due_day: int
    limit: Decimal
    created_at: datetime
