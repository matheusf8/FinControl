"""Queries de agregação pro dashboard — só leitura, nenhuma regra de negócio aqui."""
from datetime import datetime, timezone
from decimal import Decimal

from sqlalchemy import func
from sqlalchemy.orm import Session

from app.models.account import Account
from app.models.category import Category
from app.models.enums import FlowType
from app.models.transaction import Transaction


def _to_decimal(value: object) -> Decimal:
    """SQLite não tem tipo decimal nativo — soma agregada pode voltar como
    float/str dependendo do driver. Passar por str() evita erro de precisão
    binária (ex: virar 29.999999999998 em vez de 30.00)."""
    if isinstance(value, Decimal):
        return value
    return Decimal(str(value or 0))


class DashboardRepository:
    def __init__(self, db: Session):
        self.db = db

    def _sum_by_type(self, account_id: str, type: FlowType) -> Decimal:
        total = (
            self.db.query(func.coalesce(func.sum(Transaction.amount), 0))
            .filter(Transaction.account_id == account_id, Transaction.type == type)
            .scalar()
        )
        return _to_decimal(total)

    def account_balances(self, user_id: str) -> list[tuple[Account, Decimal]]:
        accounts = (
            self.db.query(Account).filter(Account.user_id == user_id).order_by(Account.created_at).all()
        )
        results = []
        for account in accounts:
            income = self._sum_by_type(account.id, FlowType.INCOME)
            expense = self._sum_by_type(account.id, FlowType.EXPENSE)
            balance = account.initial_balance + income - expense
            results.append((account, balance))
        return results

    def totals_by_type(
        self, user_id: str, date_from: datetime, date_to: datetime
    ) -> dict[FlowType, Decimal]:
        rows = (
            self.db.query(Transaction.type, func.coalesce(func.sum(Transaction.amount), 0))
            .filter(
                Transaction.user_id == user_id,
                Transaction.date >= date_from,
                Transaction.date <= date_to,
            )
            .group_by(Transaction.type)
            .all()
        )
        totals = {FlowType.INCOME: Decimal("0"), FlowType.EXPENSE: Decimal("0")}
        for type_, total in rows:
            totals[FlowType(type_)] = _to_decimal(total)
        return totals

    def totals_by_category(
        self, user_id: str, date_from: datetime, date_to: datetime, type: FlowType
    ) -> list[tuple[Category | None, Decimal]]:
        rows = (
            self.db.query(Category, func.coalesce(func.sum(Transaction.amount), 0))
            .join(Transaction, Transaction.category_id == Category.id)
            .filter(
                Transaction.user_id == user_id,
                Transaction.type == type,
                Transaction.date >= date_from,
                Transaction.date <= date_to,
            )
            .group_by(Category.id)
            .all()
        )
        result = [(category, _to_decimal(total)) for category, total in rows]

        uncategorized = (
            self.db.query(func.coalesce(func.sum(Transaction.amount), 0))
            .filter(
                Transaction.user_id == user_id,
                Transaction.type == type,
                Transaction.category_id.is_(None),
                Transaction.date >= date_from,
                Transaction.date <= date_to,
            )
            .scalar()
        )
        uncategorized_total = _to_decimal(uncategorized)
        if uncategorized_total > 0:
            result.append((None, uncategorized_total))
        return result

    def monthly_evolution(self, user_id: str, months: int) -> list[tuple[str, Decimal, Decimal]]:
        month_expr = func.strftime("%Y-%m", Transaction.date)
        rows = (
            self.db.query(month_expr, Transaction.type, func.coalesce(func.sum(Transaction.amount), 0))
            .filter(Transaction.user_id == user_id)
            .group_by(month_expr, Transaction.type)
            .all()
        )
        totals: dict[str, dict[str, Decimal]] = {}
        for month, type_, total in rows:
            totals.setdefault(month, {})[FlowType(type_).value] = _to_decimal(total)

        today = datetime.now(timezone.utc)
        result = []
        for i in range(months - 1, -1, -1):
            year = today.year
            month_num = today.month - i
            while month_num <= 0:
                month_num += 12
                year -= 1
            key = f"{year:04d}-{month_num:02d}"
            month_totals = totals.get(key, {})
            result.append(
                (
                    key,
                    month_totals.get("income", Decimal("0")),
                    month_totals.get("expense", Decimal("0")),
                )
            )
        return result
