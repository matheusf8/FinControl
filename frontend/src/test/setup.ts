import '@testing-library/jest-dom/vitest'
import { afterEach } from 'vitest'
import { useAuthStore } from '../store/authStore'

// jsdom não implementa matchMedia — themeStore usa pra detectar o tema do SO.
if (!window.matchMedia) {
  window.matchMedia = (query: string) =>
    ({
      matches: false,
      media: query,
      onchange: null,
      addListener: () => {},
      removeListener: () => {},
      addEventListener: () => {},
      removeEventListener: () => {},
      dispatchEvent: () => false,
    }) as MediaQueryList
}

// Cada teste começa deslogado — o store é persistido no localStorage,
// então sem isso um teste vazaria estado de autenticação pro próximo.
afterEach(() => {
  useAuthStore.setState({ user: null, accessToken: null, refreshToken: null })
  localStorage.clear()
})
