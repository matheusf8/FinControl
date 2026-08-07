"""Model de transação (lançamento de receita/despesa avulso, ou parcela de cartão)."""
import uuid
from datetime import datetime, timezone
from decimal import Decimal

from sqlalchemy import CheckConstraint, DateTime, ForeignKey, Integer, Numeric, String
from sqlalchemy import Enum as SAEnum
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.models.account import Account
from app.models.card import Card
from app.models.category import Category
from app.models.enums import FlowType


def _now_utc() -> datetime:
    return datetime.now(timezone.utc)


class Transaction(Base):
    __tablename__ = "transactions"
    __table_args__ = (
        # Toda transação pertence a uma conta OU a um cartão, nunca os dois
        # nem nenhum — lançamento direto (Sprint 4) usa account_id, parcela
        # de cartão (Sprint 6) usa card_id.
        CheckConstraint(
            "(account_id IS NOT NULL) != (card_id IS NOT NULL)",
            name="ck_transactions_account_xor_card",
        ),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("users.id"), nullable=False, index=True
    )
    account_id: Mapped[str | None] = mapped_column(
        String(36), ForeignKey("accounts.id"), nullable=True, index=True
    )
    card_id: Mapped[str | None] = mapped_column(
        String(36), ForeignKey("cards.id"), nullable=True, index=True
    )
    category_id: Mapped[str | None] = mapped_column(
        String(36), ForeignKey("categories.id"), nullable=True, index=True
    )
    type: Mapped[FlowType] = mapped_column(SAEnum(FlowType), nullable=False)
    amount: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    description: Mapped[str | None] = mapped_column(String(255), nullable=True)
    # Data do lançamento (o que aparece nos filtros/relatórios). Numa parcela
    # de cartão, é a data de vencimento daquela fatura, não a data da compra.
    date: Mapped[datetime] = mapped_column(DateTime, nullable=False, index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=_now_utc, nullable=False)

    # Parcelamento de cartão — nulos numa transação normal de conta.
    installment_number: Mapped[int | None] = mapped_column(Integer, nullable=True)
    installment_total: Mapped[int | None] = mapped_column(Integer, nullable=True)
    # Agrupa as N parcelas da mesma compra (pra listar/apagar a compra inteira de uma vez).
    purchase_group_id: Mapped[str | None] = mapped_column(String(36), nullable=True, index=True)

    account: Mapped["Account | None"] = relationship(back_populates="transactions")
    card: Mapped["Card | None"] = relationship(back_populates="installments")
    category: Mapped["Category | None"] = relationship(back_populates="transactions")
