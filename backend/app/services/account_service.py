"""Regras de negócio de contas financeiras."""
from decimal import Decimal

from sqlalchemy.orm import Session

from app.models.account import Account
from app.models.enums import FlowType
from app.repositories.account_repository import AccountRepository
from app.repositories.transaction_repository import TransactionRepository
from app.schemas.account import AccountCreate, AccountUpdate
from app.services.dashboard_service import DashboardService


class AccountNotFoundError(Exception):
    """Conta não existe, ou não pertence ao usuário autenticado."""


class NoClosedInvoiceError(Exception):
    """Ciclo atual ainda não fechou — não tem fatura fechada pra pagar/abater."""


class AccountService:
    def __init__(self, db: Session):
        self.db = db
        self.repo = AccountRepository(db)
        self.transactions = TransactionRepository(db)

    def list(self, user_id: str) -> list[Account]:
        return self.repo.list_by_user(user_id)

    def get(self, account_id: str, user_id: str) -> Account:
        account = self.repo.get_by_id(account_id, user_id)
        if not account:
            raise AccountNotFoundError(account_id)
        return account

    def create(self, user_id: str, data: AccountCreate) -> Account:
        return self.repo.create(user_id=user_id, **data.model_dump())

    def update(self, account_id: str, user_id: str, data: AccountUpdate) -> Account:
        account = self.get(account_id, user_id)
        return self.repo.update(account, **data.model_dump(exclude_unset=True))

    def delete(self, account_id: str, user_id: str) -> None:
        account = self.get(account_id, user_id)
        self.repo.delete(account)

    def pay_invoice(
        self,
        account_id: str,
        user_id: str,
        closing_day: int,
        amount: Decimal,
        description: str | None,
    ) -> Account:
        """Abate `amount` da fatura fechada (a que já fechou nesse ciclo, ainda
        não da que está em aberto) e desconta o mesmo valor do "saldo em
        conta" — imita o dinheiro saindo da conta de verdade pra pagar a
        fatura. Cria um lançamento de despesa negativo (mesmo padrão que o
        próprio Nubank usa pra créditos/abatimentos na fatura dele), sem
        categoria, datado no fim do ciclo fechado."""
        account = self.get(account_id, user_id)
        cycle = DashboardService(self.db).cycle_view(closing_day)
        if cycle.closed is None:
            raise NoClosedInvoiceError()

        self.transactions.create(
            user_id=user_id,
            account_id=account.id,
            type=FlowType.EXPENSE,
            amount=-amount,
            description=description or "Abatimento da fatura (saldo em conta)",
            date=cycle.closed.date_to,
        )
        new_balance = (account.real_balance or Decimal("0")) - amount
        return self.repo.update(account, real_balance=new_balance)
