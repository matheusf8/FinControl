// Espelha os schemas Pydantic de backend/app/schemas/auth.py
export type User = {
  id: string
  email: string
  full_name: string | null
  created_at: string
}

export type Token = {
  access_token: string
  refresh_token: string
  token_type: string
}

export type LoginPayload = {
  email: string
  password: string
}

export type RegisterPayload = {
  email: string
  password: string
  full_name?: string
}
