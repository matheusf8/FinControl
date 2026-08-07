"""Model de conta financeira (corrente, poupança, carteira, etc.)."""
import uuid
from datetime import datetime, timezone
from decimal import Decimal
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, ForeignKey, Numeric, String
from sqlalchemy import Enum as SAEnum
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.models.enums import AccountType

if TYPE_CHECKING:
    from app.models.transaction import Transaction


def _now_utc() -> datetime:
    return datetime.now(timezone.utc)


class Account(Base):
    __tablename__ = "accounts"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("users.id"), nullable=False, index=True
    )
    name: Mapped[str] = mapped_column(String(120), nullable=False)
    type: Mapped[AccountType] = mapped_column(
        SAEnum(AccountType), nullable=False, default=AccountType.CHECKING
    )
    # Saldo de partida ao cadastrar a conta; o saldo atual é calculado somando
    # as transações (Sprint 5), não é um campo mantido aqui.
    initial_balance: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False, default=Decimal("0"))
    created_at: Mapped[datetime] = mapped_column(DateTime, default=_now_utc, nullable=False)

    # Apagar a conta apaga junto o histórico de transações dela.
    transactions: Mapped[list["Transaction"]] = relationship(
        back_populates="account", cascade="all, delete-orphan"
    )
