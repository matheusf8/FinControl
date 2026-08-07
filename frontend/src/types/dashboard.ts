// Espelha backend/app/schemas/dashboard.py — valores monetários vêm como
// string (Decimal serializado), converter pra number só na hora de plotar.

export type AccountBalance = {
  account_id: string
  account_name: string
  balance: string
}

export type BalancesResponse = {
  total_balance: string
  accounts: AccountBalance[]
}

export type SummaryResponse = {
  date_from: string
  date_to: string
  total_income: string
  total_expense: string
  net: string
}

export type CategoryBreakdownItem = {
  category_id: string | null
  category_name: string
  color: string | null
  total: string
}

export type MonthlyEvolutionItem = {
  month: string // "2026-08"
  income: string
  expense: string
}
