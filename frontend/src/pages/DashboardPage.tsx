import { useAuthStore } from '../store/authStore'

// Placeholder da Sprint 3, só pra provar que a rota protegida funciona.
// O dashboard de verdade (gráficos, saldo, etc.) entra na Sprint 5.
export function DashboardPage() {
  const user = useAuthStore((s) => s.user)
  const logout = useAuthStore((s) => s.logout)

  return (
    <div className="min-h-screen bg-gray-50 dark:bg-gray-900 p-8">
      <div className="max-w-2xl mx-auto space-y-4">
        <h1 className="text-2xl font-semibold text-gray-900 dark:text-gray-100">
          Bem-vindo{user?.full_name ? `, ${user.full_name}` : ''}!
        </h1>
        <p className="text-gray-500 dark:text-gray-400">
          Logado como {user?.email}. O dashboard de verdade entra na Sprint 5.
        </p>
        <button
          type="button"
          onClick={logout}
          className="rounded bg-gray-200 dark:bg-gray-700 px-4 py-2 text-gray-900 dark:text-gray-100 hover:bg-gray-300 dark:hover:bg-gray-600"
        >
          Sair
        </button>
      </div>
    </div>
  )
}
