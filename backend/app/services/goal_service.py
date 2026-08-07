"""Regras de negócio de metas financeiras."""
from decimal import Decimal

from sqlalchemy.orm import Session

from app.models.goal import Goal
from app.repositories.goal_repository import GoalRepository
from app.schemas.goal import GoalContribute, GoalCreate, GoalResponse, GoalUpdate


class GoalNotFoundError(Exception):
    """Meta não existe, ou não pertence ao usuário autenticado."""


class InvalidContributionError(Exception):
    """A contribuição deixaria o valor atual negativo."""


def _to_response(goal: Goal) -> GoalResponse:
    percent = (
        (goal.current_amount / goal.target_amount * 100) if goal.target_amount else Decimal("0")
    )
    return GoalResponse(
        id=goal.id,
        name=goal.name,
        target_amount=goal.target_amount,
        current_amount=goal.current_amount,
        target_date=goal.target_date,
        created_at=goal.created_at,
        progress_percent=percent.quantize(Decimal("0.01")),
    )


class GoalService:
    def __init__(self, db: Session):
        self.repo = GoalRepository(db)

    def list(self, user_id: str) -> list[GoalResponse]:
        return [_to_response(g) for g in self.repo.list_by_user(user_id)]

    def get(self, goal_id: str, user_id: str) -> GoalResponse:
        goal = self.repo.get_by_id(goal_id, user_id)
        if not goal:
            raise GoalNotFoundError(goal_id)
        return _to_response(goal)

    def create(self, user_id: str, data: GoalCreate) -> GoalResponse:
        goal = self.repo.create(user_id=user_id, **data.model_dump())
        return _to_response(goal)

    def update(self, goal_id: str, user_id: str, data: GoalUpdate) -> GoalResponse:
        goal = self.repo.get_by_id(goal_id, user_id)
        if not goal:
            raise GoalNotFoundError(goal_id)
        goal = self.repo.update(goal, **data.model_dump(exclude_unset=True))
        return _to_response(goal)

    def delete(self, goal_id: str, user_id: str) -> None:
        goal = self.repo.get_by_id(goal_id, user_id)
        if not goal:
            raise GoalNotFoundError(goal_id)
        self.repo.delete(goal)

    def contribute(self, goal_id: str, user_id: str, data: GoalContribute) -> GoalResponse:
        goal = self.repo.get_by_id(goal_id, user_id)
        if not goal:
            raise GoalNotFoundError(goal_id)
        if goal.current_amount + data.amount < 0:
            raise InvalidContributionError(str(data.amount))
        goal = self.repo.adjust_current_amount(goal, data.amount)
        return _to_response(goal)
