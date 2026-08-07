"""Acesso ao banco pra Category — só queries, nenhuma regra de negócio aqui."""
from typing import Any

from sqlalchemy.orm import Session

from app.models.category import Category


class CategoryRepository:
    def __init__(self, db: Session):
        self.db = db

    def list_by_user(self, user_id: str) -> list[Category]:
        return (
            self.db.query(Category)
            .filter(Category.user_id == user_id)
            .order_by(Category.created_at)
            .all()
        )

    def get_by_id(self, category_id: str, user_id: str) -> Category | None:
        return (
            self.db.query(Category)
            .filter(Category.id == category_id, Category.user_id == user_id)
            .first()
        )

    def create(self, *, user_id: str, **fields: Any) -> Category:
        category = Category(user_id=user_id, **fields)
        self.db.add(category)
        self.db.commit()
        self.db.refresh(category)
        return category

    def update(self, category: Category, **fields: Any) -> Category:
        for key, value in fields.items():
            setattr(category, key, value)
        self.db.commit()
        self.db.refresh(category)
        return category

    def delete(self, category: Category) -> None:
        self.db.delete(category)
        self.db.commit()
