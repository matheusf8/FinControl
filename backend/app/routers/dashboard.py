"""Endpoints de agregação pro dashboard: saldos, resumo, gastos por categoria, evolução mensal."""
from datetime import date, datetime

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.dependencies import get_current_user
from app.models.enums import FlowType
from app.models.user import User
from app.schemas.dashboard import (
    BalancesResponse,
    CategoryBreakdownItem,
    CycleViewResponse,
    MonthlyEvolutionItem,
    SummaryResponse,
    WeeklySummaryResponse,
)
from app.services.dashboard_service import DashboardService

router = APIRouter()


@router.get("/balances", response_model=BalancesResponse)
def get_balances(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> BalancesResponse:
    return DashboardService(db).balances(current_user.id)


@router.get("/summary", response_model=SummaryResponse)
def get_summary(
    date_from: datetime | None = None,
    date_to: datetime | None = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> SummaryResponse:
    return DashboardService(db).summary(
        current_user.id, current_user.cycle_closing_day, date_from, date_to
    )


@router.get("/by-category", response_model=list[CategoryBreakdownItem])
def get_category_breakdown(
    type: FlowType = FlowType.EXPENSE,
    date_from: datetime | None = None,
    date_to: datetime | None = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> list[CategoryBreakdownItem]:
    return DashboardService(db).category_breakdown(
        current_user.id, current_user.cycle_closing_day, type, date_from, date_to
    )


@router.get("/cycle-view", response_model=CycleViewResponse)
def get_cycle_view(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> CycleViewResponse:
    """Diz pro front se é pra mostrar só a fatura em aberto (ainda não
    fechou esse mês) ou a fatura fechada + a nova em aberto (já fechou)."""
    return DashboardService(db).cycle_view(current_user.id, current_user.cycle_closing_day)


@router.get("/monthly-evolution", response_model=list[MonthlyEvolutionItem])
def get_monthly_evolution(
    months: int = Query(default=6, ge=1, le=24),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> list[MonthlyEvolutionItem]:
    return DashboardService(db).monthly_evolution(current_user.id, months)


@router.get("/weekly", response_model=WeeklySummaryResponse)
def get_weekly_summary(
    week_start: date | None = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> WeeklySummaryResponse:
    """Resumo da semana (segunda a domingo) que contém `week_start` — sem
    esse parâmetro, usa a semana atual. Qualquer dia da semana serve como
    âncora (o service normaliza pra segunda-feira), o que facilita navegar
    "semana anterior/próxima" no front só somando/subtraindo 7 dias."""
    return DashboardService(db).weekly_summary(current_user.id, week_start)
