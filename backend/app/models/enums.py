"""Enums compartilhados entre os models financeiros."""
from enum import StrEnum


class FlowType(StrEnum):
    """Receita ou despesa — usado tanto em Category quanto em Transaction."""

    INCOME = "income"
    EXPENSE = "expense"


class AccountType(StrEnum):
    CHECKING = "checking"
    SAVINGS = "savings"
    WALLET = "wallet"
    INVESTMENT = "investment"
    OTHER = "other"
