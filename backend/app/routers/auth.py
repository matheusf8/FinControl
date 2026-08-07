"""Endpoints de autenticação: registro, login, refresh, usuário atual."""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.dependencies import get_current_user
from app.core.rate_limit import is_locked, register_failure, register_success
from app.models.user import User
from app.schemas.auth import Token, TokenRefreshRequest, UserCreate, UserLogin, UserResponse
from app.services.auth_service import (
    AuthService,
    EmailAlreadyRegisteredError,
    InvalidCredentialsError,
    UserNotFoundError,
)

router = APIRouter()


@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
def register(data: UserCreate, db: Session = Depends(get_db)) -> User:
    try:
        return AuthService(db).register(data)
    except EmailAlreadyRegisteredError as exc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT, detail="E-mail já cadastrado"
        ) from exc


@router.post("/login", response_model=Token)
def login(data: UserLogin, db: Session = Depends(get_db)) -> Token:
    # Rate limit por e-mail (não por IP — é um app local, o IP é sempre o mesmo).
    rate_limit_key = data.email.lower()
    remaining = is_locked(rate_limit_key)
    if remaining is not None:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=f"Muitas tentativas. Tente novamente em {int(remaining // 60) + 1} minuto(s).",
        )

    try:
        token = AuthService(db).login(data.email, data.password)
    except InvalidCredentialsError as exc:
        register_failure(rate_limit_key)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="E-mail ou senha incorretos"
        ) from exc

    register_success(rate_limit_key)
    return token


@router.post("/refresh", response_model=Token)
def refresh(data: TokenRefreshRequest, db: Session = Depends(get_db)) -> Token:
    try:
        return AuthService(db).refresh(data.refresh_token)
    except (InvalidCredentialsError, UserNotFoundError) as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Refresh token inválido ou expirado",
        ) from exc


@router.get("/me", response_model=UserResponse)
def me(current_user: User = Depends(get_current_user)) -> User:
    return current_user
