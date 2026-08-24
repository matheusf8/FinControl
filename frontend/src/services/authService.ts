import { api } from './api'
import type {
  ForgotPasswordPayload,
  LoginPayload,
  RegisterPayload,
  ResetPasswordPayload,
  Token,
  User,
} from '../types/auth'

export const authService = {
  register: (payload: RegisterPayload) =>
    api.post<User>('/auth/register', payload).then((r) => r.data),
  login: (payload: LoginPayload) => api.post<Token>('/auth/login', payload).then((r) => r.data),
  me: () => api.get<User>('/auth/me').then((r) => r.data),
  updateSettings: (payload: { cycle_closing_day: number }) =>
    api.patch<User>('/auth/me', payload).then((r) => r.data),
  // reset_url_base vem de window.location.origin (ver ForgotPasswordPage) —
  // o backend não sabe se está sendo chamado do site hospedado ou do .exe
  // local, então quem informa a origem certa pro link do e-mail é o front.
  forgotPassword: (payload: ForgotPasswordPayload) =>
    api.post<void>('/auth/forgot-password', payload).then((r) => r.data),
  resetPassword: (payload: ResetPasswordPayload) =>
    api.post<void>('/auth/reset-password', payload).then((r) => r.data),
}
