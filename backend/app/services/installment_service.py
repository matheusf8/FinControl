"""Regras de negócio de compras parceladas no cartão: em que fatura cada
parcela cai (fechamento/vencimento) e como dividir o valor total."""
import uuid
from datetime import date, datetime, timezone
from decimal import ROUND_HALF_UP, Decimal

from sqlalchemy.orm import Session

from app.models.card import Card
from app.models.enums import FlowType
from app.models.transaction import Transaction
from app.repositories.card_repository import CardRepository
from app.repositories.category_repository import CategoryRepository
from app.repositories.installment_repository import InstallmentRepository
from app.schemas.installment import InstallmentPurchaseCreate, InvoiceResponse
from app.services.card_service import CardNotFoundError

__all__ = [
    "CardNotFoundError",
    "InstallmentService",
    "InvalidCategoryError",
    "PurchaseGroupNotFoundError",
]


class InvalidCategoryError(Exception):
    """category_id não existe, ou não pertence ao usuário autenticado."""


class PurchaseGroupNotFoundError(Exception):
    """Nenhuma parcela encontrada com esse purchase_group_id pra esse usuário."""


def _last_day_of_month(year: int, month: int) -> int:
    if month == 12:
        next_year, next_month = year + 1, 1
    else:
        next_year, next_month = year, month + 1
    return (date(next_year, next_month, 1) - date(year, month, 1)).days


def _add_months(year: int, month: int, n: int) -> tuple[int, int]:
    total = year * 12 + (month - 1) + n
    return total // 12, total % 12 + 1


def _split_amount(total: Decimal, installments: int) -> list[Decimal]:
    """Divide `total` em N parcelas de 2 casas. Ajusta a última parcela pra
    a soma bater exatamente com o total (ex: R$100,00 / 3 = 33,33+33,33+33,34,
    não 33,33x3=99,99)."""
    base = (total / installments).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
    amounts = [base] * installments
    amounts[-1] = total - base * (installments - 1)
    return amounts


class InstallmentService:
    def __init__(self, db: Session):
        self.cards = CardRepository(db)
        self.categories = CategoryRepository(db)
        self.repo = InstallmentRepository(db)

    def _first_invoice_month(self, card: Card, purchase_date: date) -> tuple[int, int]:
        # Compra até o dia de fechamento entra na fatura do próprio mês;
        # depois do fechamento, só entra na fatura do mês seguinte.
        year, month = purchase_date.year, purchase_date.month
        if purchase_date.day > card.closing_day:
            year, month = _add_months(year, month, 1)
        return year, month

    def create_purchase(
        self, user_id: str, card_id: str, data: InstallmentPurchaseCreate
    ) -> list[Transaction]:
        card = self.cards.get_by_id(card_id, user_id)
        if not card:
            raise CardNotFoundError(card_id)

        if data.category_id is not None and not self.categories.get_by_id(data.category_id, user_id):
            raise InvalidCategoryError(data.category_id)

        n = data.installments
        amounts = _split_amount(data.total_amount, n)
        purchase_group_id = str(uuid.uuid4())
        year, month = self._first_invoice_month(card, data.purchase_date)
        base_description = data.description or "Compra"

        transactions = []
        for i in range(n):
            inst_year, inst_month = _add_months(year, month, i)
            day = min(card.due_day, _last_day_of_month(inst_year, inst_month))
            due_date = datetime(inst_year, inst_month, day, tzinfo=timezone.utc)

            description = f"{base_description} ({i + 1}/{n})" if n > 1 else base_description

            transactions.append(
                Transaction(
                    user_id=user_id,
                    card_id=card.id,
                    category_id=data.category_id,
                    type=FlowType.EXPENSE,
                    amount=amounts[i],
                    description=description,
                    date=due_date,
                    installment_number=i + 1,
                    installment_total=n,
                    purchase_group_id=purchase_group_id,
                )
            )

        return self.repo.create_many(transactions)

    def get_invoice(self, user_id: str, card_id: str, year: int, month: int) -> InvoiceResponse:
        card = self.cards.get_by_id(card_id, user_id)
        if not card:
            raise CardNotFoundError(card_id)

        installments = self.repo.list_by_card_and_month(card_id, user_id, year, month)
        total = sum((t.amount for t in installments), Decimal("0"))
        return InvoiceResponse(month=f"{year:04d}-{month:02d}", total=total, installments=installments)

    def delete_purchase(self, user_id: str, purchase_group_id: str) -> None:
        transactions = self.repo.list_by_purchase_group(purchase_group_id, user_id)
        if not transactions:
            raise PurchaseGroupNotFoundError(purchase_group_id)
        self.repo.delete_many(transactions)
