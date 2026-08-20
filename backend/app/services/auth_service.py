"""Regras de negócio de autenticação: registro, login e refresh de token."""
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.security import (
    InvalidTokenError,
    TokenType,
    create_access_token,
    create_refresh_token,
    decode_token,
    hash_password,
    verify_password,
)
from app.models.user import User
from app.repositories.user_repository import UserRepository
from app.schemas.auth import Token, UserCreate


class EmailAlreadyRegisteredError(Exception):
    """Já existe um usuário com esse e-mail."""


class InvalidCredentialsError(Exception):
    """E-mail/senha incorretos, ou refresh token inválido."""


class UserNotFoundError(Exception):
    """Token válido, mas o usuário não existe mais (ex: foi deletado)."""


class InvalidInviteCodeError(Exception):
    """Código de convite ausente ou incorreto (só levantado quando
    settings.invite_code está configurado)."""


class AuthService:
    def __init__(self, db: Session):
        self.db = db
        self.users = UserRepository(db)

    def register(self, data: UserCreate) -> User:
        if settings.invite_code and data.invite_code != settings.invite_code:
            raise InvalidInviteCodeError()
        if self.users.get_by_email(data.email):
            raise EmailAlreadyRegisteredError(data.email)
        return self.users.create(
            email=data.email,
            hashed_password=hash_password(data.password),
            full_name=data.full_name,
        )

    def authenticate(self, email: str, password: str) -> User:
        user = self.users.get_by_email(email)
        if not user or not verify_password(password, user.hashed_password):
            raise InvalidCredentialsError()
        return user

    def login(self, email: str, password: str) -> Token:
        user = self.authenticate(email, password)
        return self._issue_tokens(user.id)

    def refresh(self, refresh_token: str) -> Token:
        try:
            user_id = decode_token(refresh_token, TokenType.REFRESH)
        except InvalidTokenError as exc:
            raise InvalidCredentialsError() from exc

        if not self.users.get_by_id(user_id):
            raise UserNotFoundError(user_id)

        return self._issue_tokens(user_id)

    def update_cycle_closing_day(self, user_id: str, cycle_closing_day: int) -> User:
        user = self.users.get_by_id(user_id)
        if not user:
            raise UserNotFoundError(user_id)
        return self.users.update_cycle_closing_day(user, cycle_closing_day)

    def _issue_tokens(self, user_id: str) -> Token:
        return Token(
            access_token=create_access_token(user_id),
            refresh_token=create_refresh_token(user_id),
        )
