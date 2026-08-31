import { useQuery } from '@tanstack/react-query'
import { useMemo, useState } from 'react'
import { dashboardService } from '../services/dashboardService'
import { categoryService, transactionService } from '../services/financeService'

function formatCurrency(value: string): string {
  return Number(value).toLocaleString('pt-BR', { style: 'currency', currency: 'BRL' })
}

// Data vem como ISO ("2026-07-15T00:00:00+00:00"). Formata pelo pedaço de
// data da string, sem `new Date()` — em fuso negativo isso empurraria a
// meia-noite UTC pro dia anterior (mesmo cuidado do resto do app).
function formatDate(iso: string): string {
  const [datePart] = iso.split('T')
  const [year, month, day] = datePart.split('-')
  return `${day}/${month}/${year}`
}

// Aba Faturas: registro só-leitura das faturas (ciclos) do Dashboard. Não
// cadastra cartão nem lança nada — pra isso é a aba Transações. Serve só pra
// consultar faturas passadas: total e o que entrou em cada uma.
export function InvoicesPage() {
  const [idx, setIdx] = useState(0) // 0 = ciclo atual, cresce pro passado

  const { data: cycles, isLoading } = useQuery({
    queryKey: ['dashboard', 'cycles'],
    queryFn: () => dashboardService.cycles(12),
  })
  const { data: categories } = useQuery({ queryKey: ['categories'], queryFn: categoryService.list })
  const categoriesById = useMemo(
    () => new Map((categories ?? []).map((c) => [c.id, c])),
    [categories],
  )

  const cycle = cycles?.[idx]

  const { data: summary } = useQuery({
    queryKey: ['dashboard', 'summary', 'cycle', cycle?.date_from],
    queryFn: () => dashboardService.summary(cycle),
    enabled: !!cycle,
  })
  const { data: transactions } = useQuery({
    queryKey: ['transactions', 'cycle', cycle?.date_from],
    queryFn: () =>
      transactionService.list({
        date_from: cycle!.date_from,
        date_to: cycle!.date_to,
        counts_in_cycle: true,
      }),
    enabled: !!cycle,
  })

  const isCurrent = idx === 0
  const hasOlder = !!cycles && idx < cycles.length - 1

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-semibold text-gray-900 dark:text-gray-100">Faturas</h1>
        <p className="text-gray-500 dark:text-gray-400">
          Registro das faturas (ciclos) do Dashboard, só para consulta. Para lançar ou editar, use a
          aba Transações.
        </p>
      </div>

      {isLoading || !cycle ? (
        <p className="text-gray-500 dark:text-gray-400">Carregando...</p>
      ) : (
        <>
          <div className="flex items-center justify-between bg-white dark:bg-gray-800 rounded-lg shadow p-4">
            <button
              type="button"
              onClick={() => setIdx((i) => i + 1)}
              disabled={!hasOlder}
              className="rounded bg-gray-200 dark:bg-gray-700 px-3 py-1.5 text-sm font-medium text-gray-900 dark:text-gray-100 hover:bg-gray-300 dark:hover:bg-gray-600 disabled:opacity-40"
            >
              ← Fatura anterior
            </button>
            <div className="text-center">
              <p className="font-medium text-gray-900 dark:text-gray-100">
                {formatDate(cycle.date_from)} a {formatDate(cycle.date_to)}
              </p>
              {isCurrent && (
                <p className="text-xs text-indigo-600 dark:text-indigo-400">Fatura atual</p>
              )}
            </div>
            <button
              type="button"
              onClick={() => setIdx((i) => Math.max(0, i - 1))}
              disabled={isCurrent}
              className="rounded bg-gray-200 dark:bg-gray-700 px-3 py-1.5 text-sm font-medium text-gray-900 dark:text-gray-100 hover:bg-gray-300 dark:hover:bg-gray-600 disabled:opacity-40"
            >
              Próxima fatura →
            </button>
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
            <div className="bg-white dark:bg-gray-800 rounded-lg shadow p-4">
              <p className="text-sm text-gray-500 dark:text-gray-400">Recebido</p>
              <p className="text-2xl font-semibold text-green-600">
                {summary ? formatCurrency(summary.total_income) : '—'}
              </p>
            </div>
            <div className="bg-white dark:bg-gray-800 rounded-lg shadow p-4">
              <p className="text-sm text-gray-500 dark:text-gray-400">Gasto na fatura</p>
              <p className="text-2xl font-semibold text-red-600">
                {summary ? formatCurrency(summary.total_expense) : '—'}
              </p>
            </div>
            <div className="bg-white dark:bg-gray-800 rounded-lg shadow p-4">
              <p className="text-sm text-gray-500 dark:text-gray-400">Saldo</p>
              <p
                className={`text-2xl font-semibold ${
                  summary && Number(summary.net) < 0
                    ? 'text-red-600'
                    : 'text-gray-900 dark:text-gray-100'
                }`}
              >
                {summary ? formatCurrency(summary.net) : '—'}
              </p>
            </div>
          </div>

          <div className="bg-white dark:bg-gray-800 rounded-lg shadow divide-y divide-gray-200 dark:divide-gray-700">
            <h2 className="text-lg font-medium text-gray-900 dark:text-gray-100 p-4 pb-2">
              Lançamentos da fatura
            </h2>
            {transactions?.length === 0 && (
              <p className="p-4 text-sm text-gray-500 dark:text-gray-400">
                Nenhum lançamento nessa fatura.
              </p>
            )}
            {transactions?.map((t) => (
              <div key={t.id} className="p-4 flex items-center justify-between gap-3">
                <div>
                  <p className="font-medium text-gray-900 dark:text-gray-100">
                    {t.description ||
                      (t.category_id ? categoriesById.get(t.category_id)?.name : undefined) ||
                      'Sem descrição'}
                  </p>
                  <p className="text-sm text-gray-500 dark:text-gray-400">
                    {formatDate(t.date)}
                    {t.category_id && ` · ${categoriesById.get(t.category_id)?.name ?? ''}`}
                  </p>
                </div>
                <span
                  className={`font-medium ${t.type === 'income' ? 'text-green-600' : 'text-red-600'}`}
                >
                  {t.type === 'income' ? '+' : '-'} {formatCurrency(t.amount)}
                </span>
              </div>
            ))}
          </div>
        </>
      )}
    </div>
  )
}
