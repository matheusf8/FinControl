// Espelha os schemas Pydantic de backend/app/schemas/{account,category,transaction}.py.
// Valores monetários (Decimal no backend) chegam como string no JSON (ex: "150.00"),
// pra não perder precisão — nunca converter pra number pra fazer conta no frontend.

export type AccountType = 'checking' | 'savings' | 'wallet' | 'investment' | 'other'
export type FlowType = 'income' | 'expense'

export type Account = {
  id: string
  name: string
  type: AccountType
  initial_balance: string
  // "Saldo em conta": editado à mão pelo usuário (quanto ele tem no banco de
  // verdade agora), independente do "Saldo total" calculado — null se nunca
  // configurado.
  real_balance: string | null
  created_at: string
}

export type AccountPayload = {
  name: string
  type: AccountType
  initial_balance?: string
}

export type InvoicePaymentPayload = {
  amount: string
  description?: string
}

export type Category = {
  id: string
  name: string
  type: FlowType
  color: string | null
  created_at: string
}

export type CategoryPayload = {
  name: string
  type: FlowType
  color?: string
}

export type Transaction = {
  id: string
  account_id: string
  category_id: string | null
  type: FlowType
  amount: string
  description: string | null
  date: string
  created_at: string
}

export type TransactionPayload = {
  account_id: string
  category_id?: string
  type: FlowType
  amount: string
  description?: string
  date: string
}

export type TransactionFilters = {
  account_id?: string
  category_id?: string
  type?: FlowType
  date_from?: string
  date_to?: string
}
