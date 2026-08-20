"""Schemas Pydantic pras agregações do dashboard."""
from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel


class AccountBalance(BaseModel):
    account_id: str
    account_name: str
    balance: Decimal


class BalancesResponse(BaseModel):
    total_balance: Decimal
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
