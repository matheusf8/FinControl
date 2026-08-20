import { create } from 'zustand'
import { persist } from 'zustand/middleware'
import type { User } from '../types/auth'

type AuthState = {
  user: User | null
  accessToken: string | null
  refreshToken: string | null
  setAuth: (params: { user: User; accessToken: string; refreshToken: string }) => void
  setTokens: (params: { accessToken: string; refreshToken: string }) => void
  updateUser: (user: User) => void
  logout: () => void
}

// Persistido no localStorage: ao fechar/reabrir o app, a sessão continua
// logada (até o refresh token expirar).
export const useAuthStore = create<AuthState>()(
  persist(
    (set) => ({
      user: null,
      accessToken: null,
      refreshToken: null,
      setAuth: ({ user, accessToken, refreshToken }) => set({ user, accessToken, refreshToken }),
      setTokens: ({ accessToken, refreshToken }) => set({ accessToken, refreshToken }),
      updateUser: (user) => set({ user }),
      logout: () => set({ user: null, accessToken: null, refreshToken: null }),
    }),
    { name: 'fincontrol-auth' },
  ),
)
