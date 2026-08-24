"""Regras de negócio de autenticação: registro, login e refresh de token."""
import hashlib
import secrets
from datetime import datetime, timedelta, timezone

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
from app.services.email_service import send_email

# Link de redefinição válido por 1h — janela curta o bastante pra não valer a
# pena atacar, longa o bastante pra dar tempo de abrir o e-mail com calma.
RESET_TOKEN_TTL = timedelta(hours=1)


class EmailAlreadyRegisteredError(Exception):
    """Já existe um usuário com esse e-mail."""


class InvalidCredentialsError(Exception):
    """E-mail/senha incorretos, ou refresh token inválido."""


class UserNotFoundError(Exception):
    """Token válido, mas o usuário não existe mais (ex: foi deletado)."""


class InvalidInviteCodeError(Exception):
    """Código de convite ausente ou incorreto (só levantado quando
    settings.invite_code está configurado)."""


class InvalidResetTokenError(Exception):
    """Token de redefinição de senha ausente, inválido, já usado ou expirado."""


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

    def forgot_password(self, email: str, reset_url_base: str) -> None:
        """Sempre "funciona" do ponto de vista de quem chamou, exista ou não
        esse e-mail — não dá pra deixar alguém descobrir quais e-mails têm
        conta só testando esse endpoint (user enumeration)."""
        user = self.users.get_by_email(email)
        if not user:
            return

        token = secrets.token_urlsafe(32)
        token_hash = hashlib.sha256(token.encode()).hexdigest()
        expires_at = datetime.now(timezone.utc) + RESET_TOKEN_TTL
        self.users.set_reset_token(user, token_hash, expires_at)

        link = f"{reset_url_base.rstrip('/')}/reset-password?token={token}"
        send_email(
            to=user.email,
            subject="Redefinir senha — FinControl",
            html=(
                "<p>Foi pedida a redefinição de senha da sua conta no FinControl.</p>"
                f'<p><a href="{link}">Clique aqui pra escolher uma senha nova</a> '
                "(link válido por 1 hora).</p>"
                "<p>Se não foi você quem pediu, é só ignorar este e-mail — sua senha "
                "continua a mesma.</p>"
            ),
        )

    def reset_password(self, token: str, new_password: str) -> None:
        token_hash = hashlib.sha256(token.encode()).hexdigest()
        user = self.users.get_by_reset_token_hash(token_hash)
        if not user or user.reset_token_expires_at is None:
            raise InvalidResetTokenError()

        expires_at = user.reset_token_expires_at
        if expires_at.tzinfo is None:
            expires_at = expires_at.replace(tzinfo=timezone.utc)
        if expires_at < datetime.now(timezone.utc):
            raise InvalidResetTokenError()

        self.users.update_password(user, hash_password(new_password))

    def _issue_tokens(self, user_id: str) -> Token:
        return Token(
            access_token=create_access_token(user_id),
            refresh_token=create_refresh_token(user_id),
        )
