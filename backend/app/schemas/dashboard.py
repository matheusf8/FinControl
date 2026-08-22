"""Schemas Pydantic pras agregações do dashboard."""
from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel


class AccountBalance(BaseModel):
    account_id: str
    account_name: str
    balance: Decimal
    real_balance: Decimal | None  # "saldo em conta" editado à mão, ver Account.real_balance


class BalancesResponse(BaseModel):
    total_balance: Decimal
    # Soma do "saldo em conta" das contas que têm o valor configurado; None
    # se nenhuma conta tiver configurado ainda (não confundir com soma zero).
    total_real_balance: Decimal | None
    accounts: list[AccountBalance]


class SummaryResponse(BaseModel):
    date_from: datetime
    date_to: datetime
    total_income: Decimal
    total_expense: Decimal
    net: Decimal


class CategoryBreakdownItem(BaseModel):
    category_id: str | None
    category_name: str
    color: str | None
    total: Decimal


class MonthlyEvolutionItem(BaseModel):
    month: str  # "2026-08"
    income: Decimal
    expense: Decimal


class DayTotal(BaseModel):
    date: str  # "2026-08-17"
    income: Decimal
    expense: Decimal


class WeeklySummaryResponse(BaseModel):
    week_start: str  # segunda-feira, "2026-08-17"
    week_end: str  # domingo, "2026-08-23"
    total_balance: Decimal  # saldo atual (todas as contas, não só da semana)
    total_income: Decimal
    total_expense: Decimal
    net: Decimal
    days: list[DayTotal]  # sempre 7 itens, segunda a domingo, dias sem lançamento vêm zerados


class CyclePeriod(BaseModel):
    date_from: datetime
    date_to: datetime


class CycleViewResponse(BaseModel):
    """Igual fatura de cartão: enquanto o ciclo corrente ainda não fechou,
    só existe uma fatura relevante (`open`, `closed` vem nulo). Depois que
    fecha, `closed` é a fatura que acabou de fechar (valor final, aguardando
    pagamento) e `open` já é a nova, começando a acumular."""

    closed: CyclePeriod | None
    open: CyclePeriod
