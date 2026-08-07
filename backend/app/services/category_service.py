"""Regras de negócio de categorias."""
from sqlalchemy.orm import Session

from app.models.category import Category
from app.repositories.category_repository import CategoryRepository
from app.repositories.transaction_repository import TransactionRepository
from app.schemas.category import CategoryCreate, CategoryUpdate


class CategoryNotFoundError(Exception):
    """Categoria não existe, ou não pertence ao usuário autenticado."""


class CategoryInUseError(Exception):
    """Categoria tem transações associadas, não pode ser apagada."""


class CategoryService:
    def __init__(self, db: Session):
        self.repo = CategoryRepository(db)
        self.transactions = TransactionRepository(db)

    def list(self, user_id: str) -> list[Category]:
        return self.repo.list_by_user(user_id)

    def get(self, category_id: str, user_id: str) -> Category:
        category = self.repo.get_by_id(category_id, user_id)
        if not category:
            raise CategoryNotFoundError(category_id)
        return category

    def create(self, user_id: str, data: CategoryCreate) -> Category:
        return self.repo.create(user_id=user_id, **data.model_dump())

    def update(self, category_id: str, user_id: str, data: CategoryUpdate) -> Category:
        category = self.get(category_id, user_id)
        return self.repo.update(category, **data.model_dump(exclude_unset=True))

    def delete(self, category_id: str, user_id: str) -> None:
        category = self.get(category_id, user_id)
        if self.transactions.count_by_category(category_id, user_id) > 0:
            raise CategoryInUseError(category_id)
        self.repo.delete(category)
