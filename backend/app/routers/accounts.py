"""Endpoints de contas financeiras."""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.dependencies import get_current_user
from app.models.user import User
from app.schemas.account import AccountCreate, AccountResponse, AccountUpdate, InvoicePaymentCreate
from app.services.account_service import AccountNotFoundError, AccountService, NoClosedInvoiceError

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


@router.post("/{account_id}/pay-invoice", response_model=AccountResponse)
def pay_invoice(
    account_id: str,
    data: InvoicePaymentCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> AccountResponse:
    """Abate um valor da fatura fechada usando o "saldo em conta" — lança o
    abatimento e desconta o mesmo valor do saldo. Ver AccountService.pay_invoice."""
    try:
        return AccountService(db).pay_invoice(  # type: ignore[return-value]
            account_id, current_user.id, current_user.cycle_closing_day, data.amount, data.description
        )
    except AccountNotFoundError as exc:
        raise HTTPException(status_code=404, detail="Conta não encontrada") from exc
    except NoClosedInvoiceError as exc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="O ciclo atual ainda não fechou — não tem fatura fechada pra abater",
        ) from exc


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
