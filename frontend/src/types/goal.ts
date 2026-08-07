// Espelha backend/app/schemas/goal.py

export type Goal = {
  id: string
  name: string
  target_amount: string
  current_amount: string
  target_date: string | null
  created_at: string
  progress_percent: string
}

export type GoalPayload = {
  name: string
  target_amount: string
  target_date?: string
}

export type GoalUpdatePayload = {
  name?: string
  target_amount?: string
  target_date?: string
}

export type GoalContributePayload = {
  amount: string
}
