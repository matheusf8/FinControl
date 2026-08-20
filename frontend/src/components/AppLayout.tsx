import { NavLink, Outlet } from 'react-router-dom'
import { useAuthStore } from '../store/authStore'
import { ThemeToggle } from './ThemeToggle'

const navLinkClass = ({ isActive }: { isActive: boolean }) =>
  `px-3 py-2 rounded text-sm font-medium ${
    isActive
      ? 'bg-indigo-600 text-white'
      : 'text-gray-700 dark:text-gray-300 hover:bg-gray-200 dark:hover:bg-gray-700'
  }`

// Layout das telas logadas: barra de navegação + conteúdo da rota (<Outlet/>).
export function AppLayout() {
  const logout = useAuthStore((s) => s.logout)
  const user = useAuthStore((s) => s.user)

  return (
    <div className="min-h-screen bg-gray-50 dark:bg-gray-900">
      <nav className="bg-white dark:bg-gray-800 border-b border-gray-200 dark:border-gray-700 px-4 py-3 flex flex-wrap items-center justify-between gap-2">
        <div className="flex flex-wrap items-center gap-2">
          <span className="font-semibold text-gray-900 dark:text-gray-100 mr-4">FinControl</span>
          <NavLink to="/dashboard" className={navLinkClass}>
            Dashboard
          </NavLink>
          <NavLink to="/weekly" className={navLinkClass}>
            Semana
          </NavLink>
          <NavLink to="/accounts" className={navLinkClass}>
            Contas
          </NavLink>
          <NavLink to="/categories" className={navLinkClass}>
            Categorias
          </NavLink>
          <NavLink to="/transactions" className={navLinkClass}>
            Transações
          </NavLink>
          <NavLink to="/cards" className={navLinkClass}>
            Cartões
          </NavLink>
          <NavLink to="/goals" className={navLinkClass}>
            Metas
          </NavLink>
        </div>
        <div className="flex items-center gap-3">
          <ThemeToggle />
          <span className="hidden sm:inline text-sm text-gray-500 dark:text-gray-400">
            {user?.email}
          </span>
          <button
            type="button"
            onClick={logout}
            className="text-sm rounded bg-gray-200 dark:bg-gray-700 px-3 py-1.5 text-gray-900 dark:text-gray-100 hover:bg-gray-300 dark:hover:bg-gray-600"
          >
            Sair
          </button>
        </div>
      </nav>
      <main className="p-6 max-w-5xl mx-auto">
        <Outlet />
      </main>
    </div>
  )
}
