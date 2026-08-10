"""Schemas Pydantic pra registro, login e tokens."""
from datetime import datetime

from pydantic import BaseModel, ConfigDict, EmailStr, Field


class UserCreate(BaseModel):
    email: EmailStr
    # bcrypt ignora qualquer coisa além de 72 bytes, então limitamos aqui
    # pra dar um erro 422 claro em vez de truncar a senha silenciosamente.
    password: str = Field(min_length=8, max_length=72)
    full_name: str | None = Field(default=None, max_length=255)
    # Só exigido de verdade se settings.invite_code estiver setado (ver
    # AuthService.register). Opcional aqui pra não quebrar dev/testes locais.
    invite_code: str | None = None


class UserLogin(BaseModel):
    email: EmailStr
    password: str = Field(min_length=1, max_length=72)


class UserResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    email: EmailStr
    full_name: str | None
    created_at: datetime


class Token(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class TokenRefreshRequest(BaseModel):
    refresh_token: str
