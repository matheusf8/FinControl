import { useQuery, useQueryClient } from '@tanstack/react-query'
import { useMemo, useState } from 'react'
import { TransactionRow } from '../components/TransactionRow'
import { categoryService, transactionService } from '../services/financeService'
import { dashboardService } from '../services/dashboardService'

const DAY_LABELS = ['Segunda', 'Terça', 'Quarta', 'Quinta', 'Sexta', 'Sábado', 'Domingo']

function formatCurrency(value: string): string {
  return Number(value).toLocaleString('pt-BR', { style: 'currency', currency: 'BRL' })
}

// Formata em componentes locais (ano/mês/dia), nunca via toISOString(): essa
// converte pra UTC, e em fuso negativo (ex: Brasil) pode empurrar a data pro
// dia seguinte perto da meia-noite, bagunçando a semana mostrada.
function toIsoDate(date: Date): string {
  const year = date.getFullYear()
  const month = String(date.getMonth() + 1).padStart(2, '0')
  const day = String(date.getDate()).padStart(2, '0')
  return `${year}-${month}-${day}`
}

function mondayOf(date: Date): Date {
  const weekday = date.getDay() // 0=domingo...6=sábado
  const diffToMonday = weekday === 0 ? -6 : 1 - weekday
  const result = new Date(date)
  result.setDate(result.getDate() + diffToMonday)
  return result
}

function formatDayShort(isoDate: string): string {
  const [, month, day] = isoDate.split('-')
  return `${day}/${month}`
}

function formatWeekRange(weekStart: string, weekEnd: string): string {
  return `${formatDayShort(weekStart)} a ${formatDayShort(weekEnd)}`
}

export function WeeklyPage() {
  const queryClient = useQueryClient()
  const [weekStart, setWeekStart] = useState(() => toIsoDate(mondayOf(new Date())))
  const currentWeekStart = toIsoDate(mondayOf(new Date()))
  // Qual dia está expandido mostrando os lançamentos (só um por vez, pra não
  // virar uma lista gigante) — fecha ao trocar de semana.
  const [expandedDay, setExpandedDay] = useState<string | null>(null)

  const { data, isLoading } = useQuery({
    queryKey: ['dashboard', 'weekly', weekStart],
    queryFn: () => dashboardService.weeklySummary(weekStart),
  })
  // "Saldo total" calculado foi descartado (pedido do Matheus, 2026-08-24) —
  // essa tela mostra "saldo em conta" (editado à mão no Dashboard) no lugar.
  const { data: balances } = useQuery({
    queryKey: ['dashboard', 'balances'],
    queryFn: dashboardService.balances,
  })
  const { data: categories } = useQuery({ queryKey: ['categories'], queryFn: categoryService.list })
  const categoriesById = useMemo(
    () => new Map((categories ?? []).map((c) => [c.id, c])),
    [categories],
  )

  // Busca a semana inteira de uma vez (em vez de 7 requests, um por dia) e
  // agrupa por data no cliente — "Editar"/"Remover" de um lançamento aqui
  // usa o mesmo componente da aba Transações.
  //
  // Só gastos avulsos (counts_in_cycle=false): a aba Semana é o controle do
  // dinheiro/débito do dia a dia, separado da fatura do Dashboard. Assim
  // apagar/editar algo aqui não mexe nos totais do Dashboard, e vice-versa.
  const { data: weekTransactions } = useQuery({
    queryKey: ['transactions', 'week', weekStart],
    queryFn: () =>
      transactionService.list({
        date_from: weekStart,
        date_to: data?.week_end ?? weekStart,
        counts_in_cycle: false,
      }),
    enabled: !!data?.week_end,
  })
  const transactionsByDay = useMemo(() => {
    const map = new Map<string, typeof weekTransactions>()
    for (const t of weekTransactions ?? []) {
      const day = t.date.slice(0, 10)
      map.set(day, [...(map.get(day) ?? []), t])
    }
    return map
  }, [weekTransactions])

  const invalidateWeek = () => {
    queryClient.invalidateQueries({ queryKey: ['transactions', 'week', weekStart] })
    queryClient.invalidateQueries({ queryKey: ['dashboard', 'weekly', weekStart] })
  }

  const goToWeek = (deltaDays: number) => {
    const current = new Date(`${weekStart}T00:00:00`)
    current.setDate(current.getDate() + deltaDays)
    setWeekStart(toIsoDate(current))
    setExpandedDay(null)
  }

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-semibold text-gray-900 dark:text-gray-100">Controle semanal</h1>
        <p className="text-gray-500 dark:text-gray-400">
          Só gastos avulsos (dinheiro, débito) de segunda a domingo — marcados como "gasto avulso" na
          aba Transações. Não entram na fatura do Dashboard.
        </p>
      </div>

      <div className="flex items-center justify-between bg-white dark:bg-gray-800 rounded-lg shadow p-4">
        <button
          type="button"
          onClick={() => goToWeek(-7)}
          className="rounded bg-gray-200 dark:bg-gray-700 px-3 py-1.5 text-sm font-medium text-gray-900 dark:text-gray-100 hover:bg-gray-300 dark:hover:bg-gray-600"
        >
          ← Semana anterior
        </button>
        <div className="text-center">
          <p className="font-medium text-gray-900 dark:text-gray-100">
            {data ? formatWeekRange(data.week_start, data.week_end) : '—'}
          </p>
          {weekStart === currentWeekStart && (
            <p className="text-xs text-indigo-600 dark:text-indigo-400">Semana atual</p>
          )}
        </div>
        <button
          type="button"
          onClick={() => goToWeek(7)}
          className="rounded bg-gray-200 dark:bg-gray-700 px-3 py-1.5 text-sm font-medium text-gray-900 dark:text-gray-100 hover:bg-gray-300 dark:hover:bg-gray-600"
        >
          Próxima semana →
        </button>
      </div>

      {isLoading || !data ? (
        <p className="text-gray-500 dark:text-gray-400">Carregando...</p>
      ) : (
        <>
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
            <div className="bg-white dark:bg-gray-800 rounded-lg shadow p-4">
              <p className="text-sm text-gray-500 dark:text-gray-400">Saldo em conta</p>
              <p className="text-2xl font-semibold text-gray-900 dark:text-gray-100">
                {balances?.total_real_balance != null ? formatCurrency(balances.total_real_balance) : '—'}
              </p>
            </div>
            <div className="bg-white dark:bg-gray-800 rounded-lg shadow p-4">
              <p className="text-sm text-gray-500 dark:text-gray-400">Recebido na semana</p>
              <p className="text-2xl font-semibold text-green-600">{formatCurrency(data.total_income)}</p>
            </div>
            <div className="bg-white dark:bg-gray-800 rounded-lg shadow p-4">
              <p className="text-sm text-gray-500 dark:text-gray-400">Gasto na semana</p>
              <p className="text-2xl font-semibold text-red-600">{formatCurrency(data.total_expense)}</p>
            </div>
            <div className="bg-white dark:bg-gray-800 rounded-lg shadow p-4">
              <p className="text-sm text-gray-500 dark:text-gray-400">Saldo da semana</p>
              <p
                className={`text-2xl font-semibold ${
                  Number(data.net) >= 0 ? 'text-green-600' : 'text-red-600'
                }`}
              >
                {formatCurrency(data.net)}
              </p>
            </div>
          </div>

          <div className="bg-white dark:bg-gray-800 rounded-lg shadow divide-y divide-gray-200 dark:divide-gray-700">
            <h2 className="text-lg font-medium text-gray-900 dark:text-gray-100 p-4 pb-2">Dia a dia</h2>
            {data.days.map((day, index) => {
              const net = Number(day.income) - Number(day.expense)
              const isToday = day.date === toIsoDate(new Date())
              const isExpanded = expandedDay === day.date
              const dayTransactions = transactionsByDay.get(day.date) ?? []
              const hasNothing = Number(day.income) === 0 && Number(day.expense) === 0
              return (
                <div key={day.date}>
                  <button
                    type="button"
                    onClick={() => setExpandedDay(isExpanded ? null : day.date)}
                    disabled={hasNothing}
                    className={`w-full p-4 flex flex-wrap items-center justify-between gap-3 text-left ${
                      isToday ? 'bg-indigo-50 dark:bg-indigo-950/30' : ''
                    } ${hasNothing ? 'cursor-default' : 'hover:bg-gray-50 dark:hover:bg-gray-700/50'}`}
                  >
                    <div>
                      <p className="font-medium text-gray-900 dark:text-gray-100">
                        {DAY_LABELS[index]}
                        {isToday && (
                          <span className="ml-2 text-xs text-indigo-600 dark:text-indigo-400">hoje</span>
                        )}
                      </p>
                      <p className="text-sm text-gray-500 dark:text-gray-400">{formatDayShort(day.date)}</p>
                    </div>
                    <div className="flex items-center gap-4 text-sm">
                      <span className="text-green-600">+{formatCurrency(day.income)}</span>
                      <span className="text-red-600">-{formatCurrency(day.expense)}</span>
                      <span
                        className={`font-medium w-28 text-right ${
                          net >= 0 ? 'text-gray-900 dark:text-gray-100' : 'text-red-600'
                        }`}
                      >
                        {formatCurrency(String(net))}
                      </span>
                      {!hasNothing && (
                        <span className="text-gray-400 dark:text-gray-500">{isExpanded ? '▲' : '▼'}</span>
                      )}
                    </div>
                  </button>
                  {isExpanded && (
                    <div className="divide-y divide-gray-200 dark:divide-gray-700 border-t border-gray-200 dark:border-gray-700">
                      {dayTransactions.length === 0 ? (
                        <p className="p-4 text-sm text-gray-500 dark:text-gray-400">Carregando...</p>
                      ) : (
                        dayTransactions.map((t) => (
                          <TransactionRow
                            key={t.id}
                            transaction={t}
                            categories={categories ?? []}
                            categoryName={
                              t.category_id ? categoriesById.get(t.category_id)?.name : undefined
                            }
                            onChanged={invalidateWeek}
                          />
                        ))
                      )}
                    </div>
                  )}
                </div>
              )
            })}
          </div>
        </>
      )}
    </div>
  )
}
