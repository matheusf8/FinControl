"""Acesso ao banco pra Card — só queries, nenhuma regra de negócio aqui."""
from typing import Any

from sqlalchemy.orm import Session

from app.models.card import Card


class CardRepository:
    def __init__(self, db: Session):
        self.db = db

    def list_by_user(self, user_id: str) -> list[Card]:
        return self.db.query(Card).filter(Card.user_id == user_id).order_by(Card.created_at).all()

    def get_by_id(self, card_id: str, user_id: str) -> Card | None:
        return self.db.query(Card).filter(Card.id == card_id, Card.user_id == user_id).first()

    def create(self, *, user_id: str, **fields: Any) -> Card:
        card = Card(user_id=user_id, **fields)
        self.db.add(card)
        self.db.commit()
        self.db.refresh(card)
        return card

    def update(self, card: Card, **fields: Any) -> Card:
        for key, value in fields.items():
            setattr(card, key, value)
        self.db.commit()
        self.db.refresh(card)
        return card

    def delete(self, card: Card) -> None:
        self.db.delete(card)
        self.db.commit()
