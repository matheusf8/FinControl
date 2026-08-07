"""Hash de senha e criação/validação de tokens JWT (access + refresh).

Nota: usamos a lib `bcrypt` direto (em vez de passlib) porque o passlib
1.7.4 (última versão lançada, sem manutenção há anos) é incompatível com
versões atuais do bcrypt (>=4.1) — quebra com AttributeError/ValueError.
"""
from datetime import datetime, timedelta, timezone
from enum import StrEnum
from typing import Any

import bcrypt
from jose import JWTError, jwt

from app.core.config import settings

# bcrypt trunca (e ignora) qualquer coisa além de 72 bytes — validamos o
# tamanho da senha no schema Pydantic (schemas/auth.py) pra nunca chegar aqui
# maior que isso.


class TokenType(StrEnum):
    ACCESS = "access"
    REFRESH = "refresh"


def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    return bcrypt.checkpw(plain_password.encode("utf-8"), hashed_password.encode("utf-8"))


def _create_token(subject: str, token_type: TokenType, expires_delta: timedelta) -> str:
    now = datetime.now(timezone.utc)
    payload: dict[str, Any] = {
        "sub": subject,
        "type": token_type.value,
        "iat": now,
        "exp": now + expires_delta,
    }
    return jwt.encode(payload, settings.secret_key, algorithm=settings.algorithm)


def create_access_token(user_id: str) -> str:
    return _create_token(
        user_id, TokenType.ACCESS, timedelta(minutes=settings.access_token_expire_minutes)
    )


def create_refresh_token(user_id: str) -> str:
    return _create_token(
        user_id, TokenType.REFRESH, timedelta(days=settings.refresh_token_expire_days)
    )


class InvalidTokenError(Exception):
    """Token ausente, expirado, malformado ou do tipo errado."""


def decode_token(token: str, expected_type: TokenType) -> str:
    """Retorna o user_id (subject) do token, ou levanta InvalidTokenError."""
    try:
        payload = jwt.decode(token, settings.secret_key, algorithms=[settings.algorithm])
    except JWTError as exc:
        raise InvalidTokenError("Token inválido ou expirado") from exc

    if payload.get("type") != expected_type.value:
        raise InvalidTokenError(f"Esperava um token do tipo '{expected_type.value}'")

    subject = payload.get("sub")
    if not subject:
        raise InvalidTokenError("Token sem subject")

    return subject
