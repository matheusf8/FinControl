"""Model de cartão de crédito."""
import uuid
from datetime import datetime, timezone
from decimal import Decimal
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, ForeignKey, Integer, Numeric, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base

if TYPE_CHECKING:
    from app.models.transaction import Transaction


def _now_utc() -> datetime:
    return datetime.now(timezone.utc)


class Card(Base):
    __tablename__ = "cards"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("users.id"), nullable=False, index=True
    )
    name: Mapped[str] = mapped_column(String(120), nullable=False)
    closing_day: Mapped[int] = mapped_column(Integer, nullable=False)  # dia de fechamento da fatura
    due_day: Mapped[int] = mapped_column(Integer, nullable=False)  # dia de vencimento
    limit: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False, default=Decimal("0"))
    created_at: Mapped[datetime] = mapped_column(DateTime, default=_now_utc, nullable=False)

    # Apagar o cartão apaga junto todas as parcelas lançadas nele.
    installments: Mapped[list["Transaction"]] = relationship(
        back_populates="card", cascade="all, delete-orphan"
    )
