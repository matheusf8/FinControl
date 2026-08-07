"""Schemas Pydantic pra metas financeiras."""
from datetime import date, datetime
from decimal import Decimal

from pydantic import BaseModel, Field, field_validator


class GoalCreate(BaseModel):
    name: str = Field(min_length=1, max_length=120)
    target_amount: Decimal = Field(gt=0)
    target_date: date | None = None


class GoalUpdate(BaseModel):
    # current_amount de propósito não está aqui — só muda via /contribute,
    # pra sempre passar pela validação de não ficar negativo.
    name: str | None = Field(default=None, min_length=1, max_length=120)
    target_amount: Decimal | None = Field(default=None, gt=0)
    target_date: date | None = None


class GoalContribute(BaseModel):
    # Positivo pra depositar, negativo pra retirar.
    amount: Decimal

    @field_validator("amount")
    @classmethod
    def amount_not_zero(cls, v: Decimal) -> Decimal:
        # Pydantic não tem um Field(ne=...) pra numéricos — validador manual.
        if v == 0:
            raise ValueError("O valor não pode ser zero")
        return v


class GoalResponse(BaseModel):
    id: str
    name: str
    target_amount: Decimal
    current_amount: Decimal
    target_date: date | None
    created_at: datetime
    progress_percent: Decimal
