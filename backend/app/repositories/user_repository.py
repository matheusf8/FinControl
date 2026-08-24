"""Acesso ao banco pra User — só queries, nenhuma regra de negócio aqui."""
from datetime import datetime

from sqlalchemy.orm import Session

from app.models.user import User


class UserRepository:
    def __init__(self, db: Session):
        self.db = db

    def get_by_email(self, email: str) -> User | None:
        return self.db.query(User).filter(User.email == email).first()

    def get_by_id(self, user_id: str) -> User | None:
        return self.db.query(User).filter(User.id == user_id).first()

    def get_by_reset_token_hash(self, token_hash: str) -> User | None:
        return self.db.query(User).filter(User.reset_token_hash == token_hash).first()

    def create(self, *, email: str, hashed_password: str, full_name: str | None) -> User:
        user = User(email=email, hashed_password=hashed_password, full_name=full_name)
        self.db.add(user)
        self.db.commit()
        self.db.refresh(user)
        return user

    def update_cycle_closing_day(self, user: User, cycle_closing_day: int) -> User:
        user.cycle_closing_day = cycle_closing_day
        self.db.commit()
        self.db.refresh(user)
        return user

    def set_reset_token(self, user: User, token_hash: str, expires_at: datetime) -> User:
        user.reset_token_hash = token_hash
        user.reset_token_expires_at = expires_at
        self.db.commit()
        self.db.refresh(user)
        return user

    def update_password(self, user: User, hashed_password: str) -> User:
        user.hashed_password = hashed_password
        user.reset_token_hash = None
        user.reset_token_expires_at = None
        self.db.commit()
        self.db.refresh(user)
        return user
