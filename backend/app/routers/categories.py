"""Endpoints de categorias."""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.dependencies import get_current_user
from app.models.user import User
from app.schemas.category import CategoryCreate, CategoryResponse, CategoryUpdate
from app.services.category_service import CategoryInUseError, CategoryNotFoundError, CategoryService

router = APIRouter()


@router.get("", response_model=list[CategoryResponse])
def list_categories(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> list[CategoryResponse]:
    return CategoryService(db).list(current_user.id)  # type: ignore[return-value]


@router.post("", response_model=CategoryResponse, status_code=status.HTTP_201_CREATED)
def create_category(
    data: CategoryCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> CategoryResponse:
    return CategoryService(db).create(current_user.id, data)  # type: ignore[return-value]


@router.get("/{category_id}", response_model=CategoryResponse)
def get_category(
    category_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> CategoryResponse:
    try:
        return CategoryService(db).get(category_id, current_user.id)  # type: ignore[return-value]
    except CategoryNotFoundError as exc:
        raise HTTPException(status_code=404, detail="Categoria não encontrada") from exc


@router.put("/{category_id}", response_model=CategoryResponse)
def update_category(
    category_id: str,
    data: CategoryUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> CategoryResponse:
    try:
        return CategoryService(db).update(category_id, current_user.id, data)  # type: ignore[return-value]
    except CategoryNotFoundError as exc:
        raise HTTPException(status_code=404, detail="Categoria não encontrada") from exc


@router.delete("/{category_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_category(
    category_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> None:
    try:
        CategoryService(db).delete(category_id, current_user.id)
    except CategoryNotFoundError as exc:
        raise HTTPException(status_code=404, detail="Categoria não encontrada") from exc
    except CategoryInUseError as exc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Categoria tem transações associadas, não pode ser apagada",
        ) from exc
