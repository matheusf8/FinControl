"""Acesso ao banco pra Goal — só queries, nenhuma regra de negócio aqui."""
from decimal import Decimal
from typing import Any

from sqlalchemy.orm import Session

from app.models.goal import Goal


class GoalRepository:
    def __init__(self, db: Session):
        self.db = db

    def list_by_user(self, user_id: str) -> list[Goal]:
        return self.db.query(Goal).filter(Goal.user_id == user_id).order_by(Goal.created_at).all()

    def get_by_id(self, goal_id: str, user_id: str) -> Goal | None:
        return self.db.query(Goal).filter(Goal.id == goal_id, Goal.user_id == user_id).first()

    def create(self, *, user_id: str, **fields: Any) -> Goal:
        goal = Goal(user_id=user_id, **fields)
        self.db.add(goal)
        self.db.commit()
        self.db.refresh(goal)
        return goal

    def update(self, goal: Goal, **fields: Any) -> Goal:
        for key, value in fields.items():
            setattr(goal, key, value)
        self.db.commit()
        self.db.refresh(goal)
        return goal

    def delete(self, goal: Goal) -> None:
        self.db.delete(goal)
        self.db.commit()

    def adjust_current_amount(self, goal: Goal, delta: Decimal) -> Goal:
        goal.current_amount = goal.current_amount + delta
        self.db.commit()
        self.db.refresh(goal)
        return goal
