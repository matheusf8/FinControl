// Espelha backend/app/schemas/{card,installment}.py

export type Card = {
  id: string
  name: string
  closing_day: number
  due_day: number
  limit: string
  created_at: string
}

export type CardPayload = {
  name: string
  closing_day: number
  due_day: number
  limit?: string
}

export type InstallmentPurchasePayload = {
  category_id?: string
  description?: string
  total_amount: string
  installments: number
  purchase_date: string // YYYY-MM-DD
}

export type Installment = {
  id: string
  card_id: string
  category_id: string | null
  type: 'expense'
  amount: string
  description: string | null
  date: string
  installment_number: number
  installment_total: number
  purchase_group_id: string
}

export type Invoice = {
  month: string // "2026-09"
  total: string
  installments: Installment[]
}
