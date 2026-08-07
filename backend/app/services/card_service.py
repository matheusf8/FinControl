"""Regras de negócio de cartões de crédito."""
from sqlalchemy.orm import Session

from app.models.card import Card
from app.repositories.card_repository import CardRepository
from app.schemas.card import CardCreate, CardUpdate


class CardNotFoundError(Exception):
    """Cartão não existe, ou não pertence ao usuário autenticado."""


class CardService:
    def __init__(self, db: Session):
        self.repo = CardRepository(db)

    def list(self, user_id: str) -> list[Card]:
        return self.repo.list_by_user(user_id)

    def get(self, card_id: str, user_id: str) -> Card:
        card = self.repo.get_by_id(card_id, user_id)
        if not card:
            raise CardNotFoundError(card_id)
        return card

    def create(self, user_id: str, data: CardCreate) -> Card:
        return self.repo.create(user_id=user_id, **data.model_dump())

    def update(self, card_id: str, user_id: str, data: CardUpdate) -> Card:
        card = self.get(card_id, user_id)
        return self.repo.update(card, **data.model_dump(exclude_unset=True))

    def delete(self, card_id: str, user_id: str) -> None:
        # Cascade (definido no model): apaga o cartão apaga junto todas as
        # parcelas lançadas nele — deletar um cartão é um ato deliberado.
        card = self.get(card_id, user_id)
        self.repo.delete(card)
