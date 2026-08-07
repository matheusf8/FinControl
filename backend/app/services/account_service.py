"""Regras de negócio de contas financeiras."""
from sqlalchemy.orm import Session

from app.models.account import Account
from app.repositories.account_repository import AccountRepository
from app.schemas.account import AccountCreate, AccountUpdate


class AccountNotFoundError(Exception):
    """Conta não existe, ou não pertence ao usuário autenticado."""


class AccountService:
    def __init__(self, db: Session):
        self.repo = AccountRepository(db)

    def list(self, user_id: str) -> list[Account]:
        return self.repo.list_by_user(user_id)

    def get(self, account_id: str, user_id: str) -> Account:
        account = self.repo.get_by_id(account_id, user_id)
        if not account:
            raise AccountNotFoundError(account_id)
        return account

    def create(self, user_id: str, data: AccountCreate) -> Account:
        return self.repo.create(user_id=user_id, **data.model_dump())

    def update(self, account_id: str, user_id: str, data: AccountUpdate) -> Account:
        account = self.get(account_id, user_id)
        return self.repo.update(account, **data.model_dump(exclude_unset=True))

    def delete(self, account_id: str, user_id: str) -> None:
        account = self.get(account_id, user_id)
        self.repo.delete(account)
