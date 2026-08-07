"""Endpoints de contas financeiras."""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.dependencies import get_current_user
from app.models.user import User
from app.schemas.account import AccountCreate, AccountResponse, AccountUpdate
from app.services.account_service import AccountNotFoundError, AccountService

router = APIRouter()


@router.get("", response_model=list[AccountResponse])
def list_accounts(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> list[AccountResponse]:
    return AccountService(db).list(current_user.id)  # type: ignore[return-value]


@router.post("", response_model=AccountResponse, status_code=status.HTTP_201_CREATED)
def create_account(
    data: AccountCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> AccountResponse:
    return AccountService(db).create(current_user.id, data)  # type: ignore[return-value]


@router.get("/{account_id}", response_model=AccountResponse)
def get_account(
    account_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> AccountResponse:
    try:
        return AccountService(db).get(account_id, current_user.id)  # type: ignore[return-value]
    except AccountNotFoundError as exc:
        raise HTTPException(status_code=404, detail="Conta não encontrada") from exc


@router.put("/{account_id}", response_model=AccountResponse)
def update_account(
    account_id: str,
    data: AccountUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> AccountResponse:
    try:
        return AccountService(db).update(account_id, current_user.id, data)  # type: ignore[return-value]
    except AccountNotFoundError as exc:
        raise HTTPException(status_code=404, detail="Conta não encontrada") from exc


@router.delete("/{account_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_account(
    account_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> None:
    try:
        AccountService(db).delete(account_id, current_user.id)
    except AccountNotFoundError as exc:
        raise HTTPException(status_code=404, detail="Conta não encontrada") from exc
