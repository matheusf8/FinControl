"""Regras de negócio de transações (lançamentos de receita/despesa)."""
from datetime import datetime

from sqlalchemy.orm import Session

from app.models.enums import FlowType
from app.models.transaction import Transaction
from app.repositories.account_repository import AccountRepository
from app.repositories.category_repository import CategoryRepository
from app.repositories.transaction_repository import TransactionRepository
from app.schemas.transaction import TransactionCreate, TransactionUpdate


class TransactionNotFoundError(Exception):
    """Transação não existe, ou não pertence ao usuário autenticado."""


class InvalidAccountError(Exception):
    """account_id não existe, ou não pertence ao usuário autenticado."""


class InvalidCategoryError(Exception):
    """category_id não existe, ou não pertence ao usuário autenticado."""


class TransactionService:
    def __init__(self, db: Session):
        self.repo = TransactionRepository(db)
        self.accounts = AccountRepository(db)
        self.categories = CategoryRepository(db)

    def list(
        self,
        user_id: str,
        *,
        account_id: str | None = None,
        category_id: str | None = None,
        type: FlowType | None = None,
        date_from: datetime | None = None,
        date_to: datetime | None = None,
    ) -> list[Transaction]:
        return self.repo.list_by_user(
            user_id,
            account_id=account_id,
            category_id=category_id,
            type=type,
            date_from=date_from,
            date_to=date_to,
        )

    def get(self, transaction_id: str, user_id: str) -> Transaction:
        transaction = self.repo.get_by_id(transaction_id, user_id)
        if not transaction:
            raise TransactionNotFoundError(transaction_id)
        return transaction

    def _validate_references(
        self, user_id: str, account_id: str | None, category_id: str | None
    ) -> None:
        # Impede IDOR: um usuário não pode lançar transação numa conta/categoria de outro.
        if account_id is not None and not self.accounts.get_by_id(account_id, user_id):
            raise InvalidAccountError(account_id)
        if category_id is not None and not self.categories.get_by_id(category_id, user_id):
            raise InvalidCategoryError(category_id)

    def create(self, user_id: str, data: TransactionCreate) -> Transaction:
        self._validate_references(user_id, data.account_id, data.category_id)
        return self.repo.create(user_id=user_id, **data.model_dump())

    def update(self, transaction_id: str, user_id: str, data: TransactionUpdate) -> Transaction:
        transaction = self.get(transaction_id, user_id)
        fields = data.model_dump(exclude_unset=True)
        self._validate_references(user_id, fields.get("account_id"), fields.get("category_id"))
        return self.repo.update(transaction, **fields)

    def delete(self, transaction_id: str, user_id: str) -> None:
        transaction = self.get(transaction_id, user_id)
        self.repo.delete(transaction)
