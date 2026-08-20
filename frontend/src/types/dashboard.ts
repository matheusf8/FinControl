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

export type DayTotal = {
  date: string // "2026-08-17"
  income: string
  expense: string
}

export type WeeklySummaryResponse = {
  week_start: string // segunda-feira, "2026-08-17"
  week_end: string // domingo, "2026-08-23"
  total_balance: string
  total_income: string
  total_expense: string
  net: string
  days: DayTotal[] // sempre 7 itens, segunda a domingo
}
