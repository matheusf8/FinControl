import { api } from './api'
import type { LoginPayload, RegisterPayload, Token, User } from '../types/auth'

export const authService = {
  register: (payload: RegisterPayload) =>
    api.post<User>('/auth/register', payload).then((r) => r.data),
  login: (payload: LoginPayload) => api.post<Token>('/auth/login', payload).then((r) => r.data),
  me: () => api.get<User>('/auth/me').then((r) => r.data),
}
