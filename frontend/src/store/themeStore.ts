import { create } from 'zustand'
import { persist } from 'zustand/middleware'

type Theme = 'light' | 'dark'

type ThemeState = {
  theme: Theme
  toggleTheme: () => void
}

function prefersDark(): boolean {
  return (
    typeof window !== 'undefined' &&
    window.matchMedia('(prefers-color-scheme: dark)').matches
  )
}

// Persistido no localStorage — mesma chave que src/lib/theme.ts lê antes do
// primeiro render, pra aplicar a classe "dark" sem piscar a tela errada.
export const useThemeStore = create<ThemeState>()(
  persist(
    (set, get) => ({
      theme: prefersDark() ? 'dark' : 'light',
      toggleTheme: () => set({ theme: get().theme === 'dark' ? 'light' : 'dark' }),
    }),
    { name: 'fincontrol-theme' },
  ),
)
