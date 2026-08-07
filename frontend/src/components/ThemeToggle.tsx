import { useEffect } from 'react'
import { useThemeStore } from '../store/themeStore'

export function ThemeToggle() {
  const theme = useThemeStore((s) => s.theme)
  const toggleTheme = useThemeStore((s) => s.toggleTheme)

  // Mantém o <html class="dark"> em sincronia sempre que o tema mudar
  // (a aplicação inicial, sem flash, é feita por src/lib/theme.ts).
  useEffect(() => {
    document.documentElement.classList.toggle('dark', theme === 'dark')
  }, [theme])

  return (
    <button
      type="button"
      onClick={toggleTheme}
      aria-label={theme === 'dark' ? 'Ativar modo claro' : 'Ativar modo escuro'}
      title={theme === 'dark' ? 'Modo claro' : 'Modo escuro'}
      className="rounded p-2 text-lg leading-none text-gray-600 dark:text-gray-300 hover:bg-gray-200 dark:hover:bg-gray-700"
    >
      {theme === 'dark' ? '☀️' : '🌙'}
    </button>
  )
}
