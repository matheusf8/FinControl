"""Regras de negócio das agregações do dashboard (período padrão, ordenação, etc.)."""
from datetime import date, datetime, timedelta, timezone
from decimal import Decimal

from sqlalchemy.orm import Session

from app.models.enums import FlowType
from app.repositories.dashboard_repository import DashboardRepository
from app.schemas.dashboard import (
    AccountBalance,
    BalancesResponse,
    CategoryBreakdownItem,
    DayTotal,
    MonthlyEvolutionItem,
    SummaryResponse,
    WeeklySummaryResponse,
)


def _month_start(dt: datetime) -> datetime:
    return dt.replace(day=1, hour=0, minute=0, second=0, microsecond=0)


def _month_end(month_start: datetime) -> datetime:
    """Último instante do mês de `month_start` (que já deve ser o dia 1)."""
    if month_start.month == 12:
        next_month = month_start.replace(year=month_start.year + 1, month=1)
    else:
        next_month = month_start.replace(month=month_start.month + 1)
    return next_month - timedelta(microseconds=1)


class DashboardService:
    def __init__(self, db: Session):
        self.repo = DashboardRepository(db)

    def balances(self, user_id: str) -> BalancesResponse:
        rows = self.repo.account_balances(user_id)
        accounts = [
            AccountBalance(account_id=account.id, account_name=account.name, balance=balance)
            for account, balance in rows
        ]
        total = sum((a.balance for a in accounts), Decimal("0"))
        return BalancesResponse(total_balance=total, accounts=accounts)

    def _default_period(
        self, date_from: datetime | None, date_to: datetime | None
    ) -> tuple[datetime, datetime]:
        if date_from is None and date_to is None:
            # Nenhum período informado: mês corrente INTEIRO (dia 1 até o
            # último instante do mês) — não limitar em "agora", senão um
            # lançamento datado mais tarde no mês (ex: uma conta que já foi
            # lançada mas vence depois) some do resumo.
            month_start = _month_start(datetime.now(timezone.utc))
            return month_start, _month_end(month_start)
        if date_to is None:
            date_to = datetime.now(timezone.utc)
        if date_from is None:
            date_from = _month_start(date_to)
        return date_from, date_to

    def summary(
        self, user_id: str, date_from: datetime | None, date_to: datetime | None
    ) -> SummaryResponse:
        date_from, date_to = self._default_period(date_from, date_to)
        totals = self.repo.totals_by_type(user_id, date_from, date_to)
        income = totals[FlowType.INCOME]
        expense = totals[FlowType.EXPENSE]
        return SummaryResponse(
            date_from=date_from,
            date_to=date_to,
            total_income=income,
            total_expense=expense,
            net=income - expense,
        )

    def category_breakdown(
        self,
        user_id: str,
        type: FlowType,
        date_from: datetime | None,
        date_to: datetime | None,
    ) -> list[CategoryBreakdownItem]:
        date_from, date_to = self._default_period(date_from, date_to)
        rows = self.repo.totals_by_category(user_id, date_from, date_to, type)
        items = [
            CategoryBreakdownItem(
                category_id=category.id if category else None,
                category_name=category.name if category else "Sem categoria",
                color=category.color if category else None,
                total=total,
            )
            for category, total in rows
        ]
        items.sort(key=lambda i: i.total, reverse=True)
        return items

    def monthly_evolution(self, user_id: str, months: int) -> list[MonthlyEvolutionItem]:
        rows = self.repo.monthly_evolution(user_id, months)
        return [
            MonthlyEvolutionItem(month=month, income=income, expense=expense)
            for month, income, expense in rows
        ]

    def weekly_summary(self, user_id: str, week_start: date | None) -> WeeklySummaryResponse:
        # Segunda-feira da semana pedida (ou da semana atual se nada vier) —
        # date.weekday() já é 0=segunda...6=domingo, então basta voltar esses
        # dias pra achar a segunda. Isso também "normaliza" qualquer data no
        # meio da semana que o front mande pra a segunda daquela semana.
        anchor = week_start or datetime.now(timezone.utc).date()
        monday = anchor - timedelta(days=anchor.weekday())
        sunday = monday + timedelta(days=6)

        range_start = datetime.combine(monday, datetime.min.time(), tzinfo=timezone.utc)
        range_end = datetime.combine(sunday, datetime.max.time(), tzinfo=timezone.utc)

        totals = self.repo.totals_by_type(user_id, range_start, range_end)
        daily = self.repo.daily_totals(user_id, range_start, range_end)

        days = []
        for i in range(7):
            day = monday + timedelta(days=i)
            key = day.isoformat()
            day_totals = daily.get(key, {})
            days.append(
                DayTotal(
                    date=key,
                    income=day_totals.get("income", Decimal("0")),
                    expense=day_totals.get("expense", Decimal("0")),
                )
            )

        income = totals[FlowType.INCOME]
        expense = totals[FlowType.EXPENSE]
        return WeeklySummaryResponse(
            week_start=monday.isoformat(),
            week_end=sunday.isoformat(),
            total_balance=self.balances(user_id).total_balance,
            total_income=income,
            total_expense=expense,
            net=income - expense,
            days=days,
        )
