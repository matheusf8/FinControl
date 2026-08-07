"""Endpoints de transações (lançamentos), com filtros de conta/categoria/tipo/data."""
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.dependencies import get_current_user
from app.models.enums import FlowType
from app.models.user import User
from app.schemas.transaction import TransactionCreate, TransactionResponse, TransactionUpdate
from app.services.transaction_service import (
    InvalidAccountError,
    InvalidCategoryError,
    TransactionNotFoundError,
    TransactionService,
)

router = APIRouter()


@router.get("", response_model=list[TransactionResponse])
def list_transactions(
    account_id: str | None = None,
    category_id: str | None = None,
    type: FlowType | None = None,
    date_from: datetime | None = None,
    date_to: datetime | None = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> list[TransactionResponse]:
    return TransactionService(db).list(  # type: ignore[return-value]
        current_user.id,
        account_id=account_id,
        category_id=category_id,
        type=type,
        date_from=date_from,
        date_to=date_to,
    )


@router.post("", response_model=TransactionResponse, status_code=status.HTTP_201_CREATED)
def create_transaction(
    data: TransactionCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> TransactionResponse:
    try:
        return TransactionService(db).create(current_user.id, data)  # type: ignore[return-value]
    except InvalidAccountError as exc:
        raise HTTPException(status_code=400, detail="Conta inválida") from exc
    except InvalidCategoryError as exc:
        raise HTTPException(status_code=400, detail="Categoria inválida") from exc


@router.get("/{transaction_id}", response_model=TransactionResponse)
def get_transaction(
    transaction_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> TransactionResponse:
    try:
        return TransactionService(db).get(transaction_id, current_user.id)  # type: ignore[return-value]
    except TransactionNotFoundError as exc:
        raise HTTPException(status_code=404, detail="Transação não encontrada") from exc


@router.put("/{transaction_id}", response_model=TransactionResponse)
def update_transaction(
    transaction_id: str,
    data: TransactionUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> TransactionResponse:
    try:
        return TransactionService(db).update(transaction_id, current_user.id, data)  # type: ignore[return-value]
    except TransactionNotFoundError as exc:
        raise HTTPException(status_code=404, detail="Transação não encontrada") from exc
    except InvalidAccountError as exc:
        raise HTTPException(status_code=400, detail="Conta inválida") from exc
    except InvalidCategoryError as exc:
        raise HTTPException(status_code=400, detail="Categoria inválida") from exc


@router.delete("/{transaction_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_transaction(
    transaction_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> None:
    try:
        TransactionService(db).delete(transaction_id, current_user.id)
    except TransactionNotFoundError as exc:
        raise HTTPException(status_code=404, detail="Transação não encontrada") from exc
