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
    CyclePeriod,
    CycleViewResponse,
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


def _last_day_of_month(year: int, month: int) -> int:
    if month == 12:
        next_year, next_month = year + 1, 1
    else:
        next_year, next_month = year, month + 1
    return (date(next_year, next_month, 1) - date(year, month, 1)).days


def _add_months(year: int, month: int, n: int) -> tuple[int, int]:
    total = year * 12 + (month - 1) + n
    return total // 12, total % 12 + 1


def _closing_instant(closing_day: int, year: int, month: int) -> datetime:
    """Último instante do dia de fechamento nesse mês (clampado pro último
    dia do mês, igual due_day de cartão — ex: fechamento configurado como 31
    "fecha" no dia 28/29 em fevereiro)."""
    day = min(closing_day, _last_day_of_month(year, month))
    return datetime(year, month, day, 23, 59, 59, 999999, tzinfo=timezone.utc)


def _cycle_period(closing_day: int, now: datetime) -> tuple[datetime, datetime]:
    """Ciclo financeiro do usuário — igual fechamento de fatura de cartão
    (ver installment_service._first_invoice_month): o ciclo fecha no dia
    `closing_day` de cada mês, e a partir do dia seguinte já conta pro
    próximo ciclo. Retorna (início, fim) do ciclo que contém `now`."""
    this_month_close = _closing_instant(closing_day, now.year, now.month)
    if now > this_month_close:
        end_year, end_month = _add_months(now.year, now.month, 1)
    else:
        end_year, end_month = now.year, now.month
    end = _closing_instant(closing_day, end_year, end_month)

    prev_year, prev_month = _add_months(end_year, end_month, -1)
    prev_end = _closing_instant(closing_day, prev_year, prev_month)
    start = prev_end + timedelta(microseconds=1)
    return start, end


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
        self, closing_day: int, date_from: datetime | None, date_to: datetime | None
    ) -> tuple[datetime, datetime]:
        if date_from is None and date_to is None:
            # Nenhum período informado: usa o ciclo financeiro do usuário
            # (fecha no dia `closing_day`, igual fatura de cartão), não o mês
            # calendário — reflete melhor "quanto gastei desde que paguei as
            # contas" do que dia 1 a dia 1.
            return _cycle_period(closing_day, datetime.now(timezone.utc))
        if date_to is None:
            date_to = datetime.now(timezone.utc)
        if date_from is None:
            date_from = _month_start(date_to)
        return date_from, date_to

    def summary(
        self,
        user_id: str,
        closing_day: int,
        date_from: datetime | None,
        date_to: datetime | None,
    ) -> SummaryResponse:
        date_from, date_to = self._default_period(closing_day, date_from, date_to)
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
        closing_day: int,
        type: FlowType,
        date_from: datetime | None,
        date_to: datetime | None,
    ) -> list[CategoryBreakdownItem]:
        date_from, date_to = self._default_period(closing_day, date_from, date_to)
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

    def cycle_view(self, closing_day: int) -> CycleViewResponse:
        """Decide se mostra só o ciclo em aberto (ainda não chegou no dia de
        fechamento desse mês) ou o ciclo fechado + o novo em aberto (já
        passou do fechamento). Ver CycleViewResponse."""
        now = datetime.now(timezone.utc)
        this_month_close = _closing_instant(closing_day, now.year, now.month)
        open_start, open_end = _cycle_period(closing_day, now)
        open_period = CyclePeriod(date_from=open_start, date_to=open_end)

        if now <= this_month_close:
            return CycleViewResponse(closed=None, open=open_period)

        closed_start, closed_end = _cycle_period(closing_day, this_month_close)
        closed_period = CyclePeriod(date_from=closed_start, date_to=closed_end)
        return CycleViewResponse(closed=closed_period, open=open_period)

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
