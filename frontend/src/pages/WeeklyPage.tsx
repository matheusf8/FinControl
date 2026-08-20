import { useQuery } from '@tanstack/react-query'
import { useState } from 'react'
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
  const [weekStart, setWeekStart] = useState(() => toIsoDate(mondayOf(new Date())))
  const currentWeekStart = toIsoDate(mondayOf(new Date()))

  const { data, isLoading } = useQuery({
    queryKey: ['dashboard', 'weekly', weekStart],
    queryFn: () => dashboardService.weeklySummary(weekStart),
  })

  const goToWeek = (deltaDays: number) => {
    const current = new Date(`${weekStart}T00:00:00`)
    current.setDate(current.getDate() + deltaDays)
    setWeekStart(toIsoDate(current))
  }

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-semibold text-gray-900 dark:text-gray-100">Controle semanal</h1>
        <p className="text-gray-500 dark:text-gray-400">Receitas e despesas de segunda a domingo.</p>
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
              <p className="text-sm text-gray-500 dark:text-gray-400">Saldo total (atual)</p>
              <p className="text-2xl font-semibold text-gray-900 dark:text-gray-100">
                {formatCurrency(data.total_balance)}
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
              return (
                <div
                  key={day.date}
                  className={`p-4 flex flex-wrap items-center justify-between gap-3 ${
                    isToday ? 'bg-indigo-50 dark:bg-indigo-950/30' : ''
                  }`}
                >
                  <div>
                    <p className="font-medium text-gray-900 dark:text-gray-100">
                      {DAY_LABELS[index]}
                      {isToday && <span className="ml-2 text-xs text-indigo-600 dark:text-indigo-400">hoje</span>}
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
                  </div>
                </div>
              )
            })}
          </div>
        </>
      )}
    </div>
  )
}
