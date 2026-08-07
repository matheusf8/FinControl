"""Schemas Pydantic pra categorias."""
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from app.models.enums import FlowType

_COLOR_PATTERN = r"^#[0-9a-fA-F]{6}$"


class CategoryCreate(BaseModel):
    name: str = Field(min_length=1, max_length=120)
    type: FlowType
    color: str | None = Field(default=None, pattern=_COLOR_PATTERN)


class CategoryUpdate(BaseModel):
    # `type` não é editável de propósito: mudar o tipo de uma categoria já
    # usada em transações passadas deixaria os relatórios inconsistentes.
    name: str | None = Field(default=None, min_length=1, max_length=120)
    color: str | None = Field(default=None, pattern=_COLOR_PATTERN)


class CategoryResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    name: str
    type: FlowType
    color: str | None
    created_at: datetime
