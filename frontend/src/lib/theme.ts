/** Aplica a classe "dark" no <html> ANTES do primeiro render, lendo direto
 * do localStorage — evita o "flash" da tela no tema errado ao carregar. */
const STORAGE_KEY = 'fincontrol-theme'

export function initTheme(): void {
  let isDark: boolean

  try {
    const stored = localStorage.getItem(STORAGE_KEY)
    const parsed = stored ? JSON.parse(stored) : null
    isDark = parsed?.state?.theme
      ? parsed.state.theme === 'dark'
      : window.matchMedia('(prefers-color-scheme: dark)').matches
  } catch {
    isDark = false
  }

  document.documentElement.classList.toggle('dark', isDark)
}
