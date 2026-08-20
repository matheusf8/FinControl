"""Model do usuário — base de tudo (cada Account/Transaction pertence a um User)."""
import uuid
from datetime import datetime, timezone

from sqlalchemy import DateTime, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


def _now_utc() -> datetime:
    return datetime.now(timezone.utc)


class User(Base):
    __tablename__ = "users"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True, nullable=False)
    hashed_password: Mapped[str] = mapped_column(String(255), nullable=False)
    full_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=_now_utc, nullable=False)
    # Dia do mês que fecha o "ciclo financeiro" do usuário (igual fechamento
    # de fatura de cartão — ver Card.closing_day) — define o período do
    # resumo do dashboard (dashboard_service._cycle_period), no lugar do mês
    # calendário. Cada pessoa configura o seu (o dia de pagar as contas varia
    # de pessoa pra pessoa). Default 24 só pra já vir com algo sensato antes
    # do usuário ajustar.
    cycle_closing_day: Mapped[int] = mapped_column(Integer, nullable=False, default=24)
