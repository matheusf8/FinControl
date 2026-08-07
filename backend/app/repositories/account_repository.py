"""Acesso ao banco pra Account — só queries, nenhuma regra de negócio aqui."""
from typing import Any

from sqlalchemy.orm import Session

from app.models.account import Account


class AccountRepository:
    def __init__(self, db: Session):
        self.db = db

    def list_by_user(self, user_id: str) -> list[Account]:
        return (
            self.db.query(Account)
            .filter(Account.user_id == user_id)
            .order_by(Account.created_at)
            .all()
        )

    def get_by_id(self, account_id: str, user_id: str) -> Account | None:
        return (
            self.db.query(Account)
            .filter(Account.id == account_id, Account.user_id == user_id)
            .first()
        )

    def create(self, *, user_id: str, **fields: Any) -> Account:
        account = Account(user_id=user_id, **fields)
        self.db.add(account)
        self.db.commit()
        self.db.refresh(account)
        return account

    def update(self, account: Account, **fields: Any) -> Account:
        for key, value in fields.items():
            setattr(account, key, value)
        self.db.commit()
        self.db.refresh(account)
        return account

    def delete(self, account: Account) -> None:
        self.db.delete(account)
        self.db.commit()
