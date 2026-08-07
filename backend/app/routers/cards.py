"""Endpoints de cartões de crédito, compras parceladas e fatura mensal."""
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.dependencies import get_current_user
from app.models.user import User
from app.schemas.card import CardCreate, CardResponse, CardUpdate
from app.schemas.installment import InstallmentPurchaseCreate, InstallmentResponse, InvoiceResponse
from app.services.card_service import CardNotFoundError, CardService
from app.services.installment_service import (
    InstallmentService,
    InvalidCategoryError,
    PurchaseGroupNotFoundError,
)

router = APIRouter()


@router.get("", response_model=list[CardResponse])
def list_cards(
    current_user: User = Depends(get_current_user), db: Session = Depends(get_db)
) -> list[CardResponse]:
    return CardService(db).list(current_user.id)  # type: ignore[return-value]


@router.post("", response_model=CardResponse, status_code=status.HTTP_201_CREATED)
def create_card(
    data: CardCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> CardResponse:
    return CardService(db).create(current_user.id, data)  # type: ignore[return-value]


@router.get("/{card_id}", response_model=CardResponse)
def get_card(
    card_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> CardResponse:
    try:
        return CardService(db).get(card_id, current_user.id)  # type: ignore[return-value]
    except CardNotFoundError as exc:
        raise HTTPException(status_code=404, detail="Cartão não encontrado") from exc


@router.put("/{card_id}", response_model=CardResponse)
def update_card(
    card_id: str,
    data: CardUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> CardResponse:
    try:
        return CardService(db).update(card_id, current_user.id, data)  # type: ignore[return-value]
    except CardNotFoundError as exc:
        raise HTTPException(status_code=404, detail="Cartão não encontrado") from exc


@router.delete("/{card_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_card(
    card_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> None:
    try:
        CardService(db).delete(card_id, current_user.id)
    except CardNotFoundError as exc:
        raise HTTPException(status_code=404, detail="Cartão não encontrado") from exc


@router.post(
    "/{card_id}/purchases",
    response_model=list[InstallmentResponse],
    status_code=status.HTTP_201_CREATED,
)
def create_purchase(
    card_id: str,
    data: InstallmentPurchaseCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> list[InstallmentResponse]:
    try:
        return InstallmentService(db).create_purchase(current_user.id, card_id, data)  # type: ignore[return-value]
    except CardNotFoundError as exc:
        raise HTTPException(status_code=404, detail="Cartão não encontrado") from exc
    except InvalidCategoryError as exc:
        raise HTTPException(status_code=400, detail="Categoria inválida") from exc


@router.get("/{card_id}/invoice", response_model=InvoiceResponse)
def get_invoice(
    card_id: str,
    month: str = Query(..., description="Mês da fatura no formato YYYY-MM"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> InvoiceResponse:
    try:
        year_str, month_str = month.split("-")
        year, month_num = int(year_str), int(month_str)
    except (ValueError, AttributeError) as exc:
        raise HTTPException(status_code=422, detail="Formato de mês inválido, use YYYY-MM") from exc

    try:
        return InstallmentService(db).get_invoice(current_user.id, card_id, year, month_num)
    except CardNotFoundError as exc:
        raise HTTPException(status_code=404, detail="Cartão não encontrado") from exc


@router.delete("/purchases/{purchase_group_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_purchase(
    purchase_group_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> None:
    try:
        InstallmentService(db).delete_purchase(current_user.id, purchase_group_id)
    except PurchaseGroupNotFoundError as exc:
        raise HTTPException(status_code=404, detail="Compra não encontrada") from exc
