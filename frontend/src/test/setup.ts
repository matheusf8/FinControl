import '@testing-library/jest-dom/vitest'
import { afterEach } from 'vitest'
import { useAuthStore } from '../store/authStore'

// Cada teste começa deslogado — o store é persistido no localStorage,
// então sem isso um teste vazaria estado de autenticação pro próximo.
afterEach(() => {
  useAuthStore.setState({ user: null, accessToken: null, refreshToken: null })
  localStorage.clear()
})
