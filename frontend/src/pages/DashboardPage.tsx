import { useAuthStore } from '../store/authStore'

// Placeholder da Sprint 4, só pra provar que a rota protegida funciona.
// O dashboard de verdade (gráficos, saldo, evolução) entra na Sprint 5.
export function DashboardPage() {
  const user = useAuthStore((s) => s.user)

  return (
    <div className="space-y-2">
      <h1 className="text-2xl font-semibold text-gray-900 dark:text-gray-100">
        Bem-vindo{user?.full_name ? `, ${user.full_name}` : ''}!
      </h1>
      <p className="text-gray-500 dark:text-gray-400">
        O dashboard de verdade (gráficos, saldo, evolução) entra na Sprint 5. Use o menu acima pra
        cadastrar contas, categorias e lançar transações.
      </p>
    </div>
  )
}
