"""Acesso ao banco pra Transaction — só queries, nenhuma regra de negócio aqui."""
from datetime import datetime
from typing import Any

from sqlalchemy.orm import Session

from app.models.enums import FlowType
from app.models.transaction import Transaction


class TransactionRepository:
    def __init__(self, db: Session):
        self.db = db

    def list_by_user(
        self,
        user_id: str,
        *,
        account_id: str | None = None,
        category_id: str | None = None,
        type: FlowType | None = None,
        date_from: datetime | None = None,
        date_to: datetime | None = None,
        counts_in_cycle: bool | None = None,
    ) -> list[Transaction]:
        query = self.db.query(Transaction).filter(Transaction.user_id == user_id)
        if account_id:
            query = query.filter(Transaction.account_id == account_id)
        if category_id:
            query = query.filter(Transaction.category_id == category_id)
        if type:
            query = query.filter(Transaction.type == type)
        if counts_in_cycle is not None:
            query = query.filter(Transaction.counts_in_cycle.is_(counts_in_cycle))
        if date_from:
            query = query.filter(Transaction.date >= date_from)
        if date_to:
            query = query.filter(Transaction.date <= date_to)
        return query.order_by(Transaction.date.desc()).all()

    def get_by_id(self, transaction_id: str, user_id: str) -> Transaction | None:
        return (
            self.db.query(Transaction)
            .filter(Transaction.id == transaction_id, Transaction.user_id == user_id)
            .first()
        )

    def create(self, *, user_id: str, **fields: Any) -> Transaction:
        transaction = Transaction(user_id=user_id, **fields)
        self.db.add(transaction)
        self.db.commit()
        self.db.refresh(transaction)
        return transaction

    def update(self, transaction: Transaction, **fields: Any) -> Transaction:
        for key, value in fields.items():
            setattr(transaction, key, value)
        self.db.commit()
        self.db.refresh(transaction)
        return transaction

    def delete(self, transaction: Transaction) -> None:
        self.db.delete(transaction)
        self.db.commit()

    def count_by_category(self, category_id: str, user_id: str) -> int:
        return (
            self.db.query(Transaction)
            .filter(Transaction.category_id == category_id, Transaction.user_id == user_id)
            .count()
        )
