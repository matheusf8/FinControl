import { useQuery } from '@tanstack/react-query'
import {
  CartesianGrid,
  Cell,
  Legend,
  Line,
  LineChart,
  Pie,
  PieChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from 'recharts'
import { dashboardService } from '../services/dashboardService'
import { useAuthStore } from '../store/authStore'

const FALLBACK_COLORS = ['#6366f1', '#22c55e', '#f97316', '#ef4444', '#0ea5e9', '#a855f7', '#eab308']

function formatCurrency(value: string): string {
  return Number(value).toLocaleString('pt-BR', { style: 'currency', currency: 'BRL' })
}

function formatMonth(month: string): string {
  const [year, m] = month.split('-')
  const date = new Date(Number(year), Number(m) - 1, 1)
  return date.toLocaleDateString('pt-BR', { month: 'short', year: '2-digit' })
}

export function DashboardPage() {
  const user = useAuthStore((s) => s.user)

  const { data: balances } = useQuery({
    queryKey: ['dashboard', 'balances'],
    queryFn: dashboardService.balances,
  })
  const { data: summary } = useQuery({
    queryKey: ['dashboard', 'summary'],
    queryFn: dashboardService.summary,
  })
  const { data: byCategory } = useQuery({
    queryKey: ['dashboard', 'by-category', 'expense'],
    queryFn: () => dashboardService.byCategory('expense'),
  })
  const { data: evolution } = useQuery({
    queryKey: ['dashboard', 'monthly-evolution'],
    queryFn: () => dashboardService.monthlyEvolution(6),
  })

  const pieData = (byCategory ?? []).map((item) => ({
    name: item.category_name,
    value: Number(item.total),
    color: item.color,
  }))

  const evolutionData = (evolution ?? []).map((item) => ({
    month: formatMonth(item.month),
    Receitas: Number(item.income),
    Despesas: Number(item.expense),
  }))

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-semibold text-gray-900 dark:text-gray-100">
          Bem-vindo{user?.full_name ? `, ${user.full_name}` : ''}!
        </h1>
        <p className="text-gray-500 dark:text-gray-400">Resumo do mês atual.</p>
      </div>

      <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
        <div className="bg-white dark:bg-gray-800 rounded-lg shadow p-4">
          <p className="text-sm text-gray-500 dark:text-gray-400">Saldo total</p>
          <p className="text-2xl font-semibold text-gray-900 dark:text-gray-100">
            {balances ? formatCurrency(balances.total_balance) : '—'}
          </p>
        </div>
        <div className="bg-white dark:bg-gray-800 rounded-lg shadow p-4">
          <p className="text-sm text-gray-500 dark:text-gray-400">Receitas no mês</p>
          <p className="text-2xl font-semibold text-green-600">
            {summary ? formatCurrency(summary.total_income) : '—'}
          </p>
        </div>
        <div className="bg-white dark:bg-gray-800 rounded-lg shadow p-4">
          <p className="text-sm text-gray-500 dark:text-gray-400">Despesas no mês</p>
          <p className="text-2xl font-semibold text-red-600">
            {summary ? formatCurrency(summary.total_expense) : '—'}
          </p>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
        <div className="bg-white dark:bg-gray-800 rounded-lg shadow p-4">
          <h2 className="text-lg font-medium text-gray-900 dark:text-gray-100 mb-2">
            Gastos por categoria (mês atual)
          </h2>
          {pieData.length === 0 ? (
            <p className="text-gray-500 dark:text-gray-400 text-sm">
              Nenhuma despesa lançada esse mês ainda.
            </p>
          ) : (
            <ResponsiveContainer width="100%" height={260}>
              <PieChart>
                <Pie
                data={pieData}
                dataKey="value"
                nameKey="name"
                outerRadius={90}
                label
                // A animação de entrada (crescer do 0°) trava numa fatia
                // minúscula em alguns navegadores/ambientes — recharts nunca
                // termina o tween e a pizza fica "achatada". Sem impacto
                // visual perceptível desligar, e evita esse travamento.
                isAnimationActive={false}
              >
                  {pieData.map((entry, index) => (
                    <Cell
                      key={entry.name}
                      fill={entry.color ?? FALLBACK_COLORS[index % FALLBACK_COLORS.length]}
                    />
                  ))}
                </Pie>
                <Tooltip
                  formatter={(value) =>
                    Number(value).toLocaleString('pt-BR', { style: 'currency', currency: 'BRL' })
                  }
                />
                <Legend />
              </PieChart>
            </ResponsiveContainer>
          )}
        </div>

        <div className="bg-white dark:bg-gray-800 rounded-lg shadow p-4">
          <h2 className="text-lg font-medium text-gray-900 dark:text-gray-100 mb-2">
            Evolução mensal (últimos 6 meses)
          </h2>
          <ResponsiveContainer width="100%" height={260}>
            <LineChart data={evolutionData}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="month" />
              <YAxis />
              <Tooltip
                formatter={(value) =>
                  Number(value).toLocaleString('pt-BR', { style: 'currency', currency: 'BRL' })
                }
              />
              <Legend />
              <Line type="monotone" dataKey="Receitas" stroke="#22c55e" />
              <Line type="monotone" dataKey="Despesas" stroke="#ef4444" />
            </LineChart>
          </ResponsiveContainer>
        </div>
      </div>

      {balances && balances.accounts.length > 0 && (
        <div className="bg-white dark:bg-gray-800 rounded-lg shadow divide-y divide-gray-200 dark:divide-gray-700">
          <h2 className="text-lg font-medium text-gray-900 dark:text-gray-100 p-4 pb-2">
            Saldo por conta
          </h2>
          {balances.accounts.map((account) => (
            <div key={account.account_id} className="p-4 flex items-center justify-between">
              <span className="text-gray-900 dark:text-gray-100">{account.account_name}</span>
              <span className="font-medium text-gray-900 dark:text-gray-100">
                {formatCurrency(account.balance)}
              </span>
            </div>
          ))}
        </div>
      )}
    </div>
  )
}
