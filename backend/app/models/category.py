"""Model de categoria (ex: Alimentação, Salário, Transporte)."""
import uuid
from datetime import datetime, timezone
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, ForeignKey, String
from sqlalchemy import Enum as SAEnum
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.models.enums import FlowType

if TYPE_CHECKING:
    from app.models.transaction import Transaction


def _now_utc() -> datetime:
    return datetime.now(timezone.utc)


class Category(Base):
    __tablename__ = "categories"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("users.id"), nullable=False, index=True
    )
    name: Mapped[str] = mapped_column(String(120), nullable=False)
    type: Mapped[FlowType] = mapped_column(SAEnum(FlowType), nullable=False)
    color: Mapped[str | None] = mapped_column(String(7), nullable=True)  # ex: "#22c55e"
    created_at: Mapped[datetime] = mapped_column(DateTime, default=_now_utc, nullable=False)

    transactions: Mapped[list["Transaction"]] = relationship(back_populates="category")
