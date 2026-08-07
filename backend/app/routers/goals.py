"""Endpoints de metas financeiras."""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.dependencies import get_current_user
from app.models.user import User
from app.schemas.goal import GoalContribute, GoalCreate, GoalResponse, GoalUpdate
from app.services.goal_service import GoalNotFoundError, GoalService, InvalidContributionError

router = APIRouter()


@router.get("", response_model=list[GoalResponse])
def list_goals(
    current_user: User = Depends(get_current_user), db: Session = Depends(get_db)
) -> list[GoalResponse]:
    return GoalService(db).list(current_user.id)


@router.post("", response_model=GoalResponse, status_code=status.HTTP_201_CREATED)
def create_goal(
    data: GoalCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> GoalResponse:
    return GoalService(db).create(current_user.id, data)


@router.get("/{goal_id}", response_model=GoalResponse)
def get_goal(
    goal_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> GoalResponse:
    try:
        return GoalService(db).get(goal_id, current_user.id)
    except GoalNotFoundError as exc:
        raise HTTPException(status_code=404, detail="Meta não encontrada") from exc


@router.put("/{goal_id}", response_model=GoalResponse)
def update_goal(
    goal_id: str,
    data: GoalUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> GoalResponse:
    try:
        return GoalService(db).update(goal_id, current_user.id, data)
    except GoalNotFoundError as exc:
        raise HTTPException(status_code=404, detail="Meta não encontrada") from exc


@router.delete("/{goal_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_goal(
    goal_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> None:
    try:
        GoalService(db).delete(goal_id, current_user.id)
    except GoalNotFoundError as exc:
        raise HTTPException(status_code=404, detail="Meta não encontrada") from exc


@router.post("/{goal_id}/contribute", response_model=GoalResponse)
def contribute_to_goal(
    goal_id: str,
    data: GoalContribute,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> GoalResponse:
    try:
        return GoalService(db).contribute(goal_id, current_user.id, data)
    except GoalNotFoundError as exc:
        raise HTTPException(status_code=404, detail="Meta não encontrada") from exc
    except InvalidContributionError as exc:
        raise HTTPException(
            status_code=400, detail="Isso deixaria o valor atual negativo"
        ) from exc
