"""Acesso ao banco pras parcelas de cartão (Transaction com card_id preenchido)."""
from sqlalchemy import extract
from sqlalchemy.orm import Session

from app.models.transaction import Transaction


class InstallmentRepository:
    def __init__(self, db: Session):
        self.db = db

    def create_many(self, transactions: list[Transaction]) -> list[Transaction]:
        self.db.add_all(transactions)
        self.db.commit()
        for t in transactions:
            self.db.refresh(t)
        return transactions

    def list_by_card_and_month(
        self, card_id: str, user_id: str, year: int, month: int
    ) -> list[Transaction]:
        # extract() em vez de strftime: strftime só existe no SQLite e quebra
        # (função inexistente) no Postgres usado em produção.
        return (
            self.db.query(Transaction)
            .filter(
                Transaction.card_id == card_id,
                Transaction.user_id == user_id,
                extract("year", Transaction.date) == year,
                extract("month", Transaction.date) == month,
            )
            .order_by(Transaction.date)
            .all()
        )

    def list_by_purchase_group(self, purchase_group_id: str, user_id: str) -> list[Transaction]:
        return (
            self.db.query(Transaction)
            .filter(
                Transaction.purchase_group_id == purchase_group_id,
                Transaction.user_id == user_id,
            )
            .order_by(Transaction.installment_number)
            .all()
        )

    def delete_many(self, transactions: list[Transaction]) -> None:
        for t in transactions:
            self.db.delete(t)
        self.db.commit()
