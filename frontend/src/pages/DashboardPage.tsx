import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { isAxiosError } from 'axios'
import { useState } from 'react'
import type { ReactNode } from 'react'
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
import { toApiAmount } from '../lib/money'
import { authService } from '../services/authService'
import { dashboardService } from '../services/dashboardService'
import { accountService } from '../services/financeService'
import { useAuthStore } from '../store/authStore'
import type { CategoryBreakdownItem, CyclePeriod, SummaryResponse } from '../types/dashboard'

const FALLBACK_COLORS = ['#6366f1', '#22c55e', '#f97316', '#ef4444', '#0ea5e9', '#a855f7', '#eab308']

const RADIAN = Math.PI / 180

// Rótulo dentro da fatia (porcentagem), em vez do padrão do recharts que
// escreve nome+valor fora da pizza com uma linha guia: em fatias vizinhas
// pequenas essas linhas/textos se atropelam e, na fatia que cai perto do
// topo, o texto é cortado pela borda do card (era o caso do "Fatura" roxo).
// Fatias muito finas (<6%) não recebem rótulo — não cabe texto legível ali,
// e a legenda + tooltip já mostram nome e valor exato ao passar o mouse.
type PieLabelProps = {
  cx?: number
  cy?: number
  midAngle?: number
  innerRadius?: number
  outerRadius?: number
  percent?: number
}

function renderPercentLabel({ cx, cy, midAngle, innerRadius, outerRadius, percent }: PieLabelProps) {
  if (
    cx === undefined ||
    cy === undefined ||
    midAngle === undefined ||
    innerRadius === undefined ||
    outerRadius === undefined ||
    percent === undefined ||
    percent < 0.06
  ) {
    return null
  }
  const radius = innerRadius + (outerRadius - innerRadius) * 0.6
  const x = cx + radius * Math.cos(-midAngle * RADIAN)
  const y = cy + radius * Math.sin(-midAngle * RADIAN)
  return (
    <text
      x={x}
      y={y}
      fill="#fff"
      textAnchor="middle"
      dominantBaseline="central"
      fontSize={12}
      fontWeight={600}
    >
      {`${Math.round(percent * 100)}%`}
    </text>
  )
}

function formatCurrency(value: string): string {
  return Number(value).toLocaleString('pt-BR', { style: 'currency', currency: 'BRL' })
}

function formatMonth(month: string): string {
  const [year, m] = month.split('-')
  const date = new Date(Number(year), Number(m) - 1, 1)
  return date.toLocaleDateString('pt-BR', { month: 'short', year: '2-digit' })
}

// date_from/date_to vêm como datetime completo em UTC (ex: "2026-07-25T00:00:00Z").
// Extrai o dia/mês direto da string, sem passar por `new Date(iso).toLocaleDateString()`
// — isso converteria pro fuso local do navegador, e em fuso negativo (ex: Brasil) a
// meia-noite UTC do início do ciclo vira "dia anterior" na tela (mostrava 24/07 em vez
// de 25/07). O back já pensa em dias corridos (UTC), então exibe o mesmo dia.
function formatCycleDate(iso: string): string {
  const [datePart] = iso.split('T')
  const [, month, day] = datePart.split('-')
  return `${day}/${month}`
}

// Um painel de fatura (fechada ou em aberto): resumo receita/despesa/saldo
// daquele período + gastos por categoria em pizza.
function CyclePanel({
  title,
  hint,
  period,
  summary,
  byCategory,
  footer,
}: {
  title: string
  hint?: string
  period: CyclePeriod
  summary: SummaryResponse | undefined
  byCategory: CategoryBreakdownItem[] | undefined
  footer?: ReactNode
}) {
  const pieData = (byCategory ?? []).map((item) => ({
    name: item.category_name,
    value: Number(item.total),
    color: item.color,
  }))
  const netIsNegative = summary ? Number(summary.net) < 0 : false

  return (
    <div className="bg-white dark:bg-gray-800 rounded-lg shadow p-4">
      <div className="mb-3">
        <h2 className="text-lg font-medium text-gray-900 dark:text-gray-100">{title}</h2>
        <p className="text-sm text-gray-500 dark:text-gray-400">
          {formatCycleDate(period.date_from)} a {formatCycleDate(period.date_to)}
          {hint ? ` · ${hint}` : ''}
        </p>
      </div>

      <div className="grid grid-cols-3 gap-2 mb-3 text-center">
        <div>
          <p className="text-xs text-gray-500 dark:text-gray-400">Receita</p>
          <p className="font-semibold text-green-600">
            {summary ? formatCurrency(summary.total_income) : '—'}
          </p>
        </div>
        <div>
          <p className="text-xs text-gray-500 dark:text-gray-400">Despesa</p>
          <p className="font-semibold text-red-600">
            {summary ? formatCurrency(summary.total_expense) : '—'}
          </p>
        </div>
        <div>
          <p className="text-xs text-gray-500 dark:text-gray-400">Saldo</p>
          <p
            className={`font-semibold ${netIsNegative ? 'text-red-600' : 'text-gray-900 dark:text-gray-100'}`}
          >
            {summary ? formatCurrency(summary.net) : '—'}
          </p>
        </div>
      </div>

      {pieData.length === 0 ? (
        <p className="text-gray-500 dark:text-gray-400 text-sm">
          Nenhuma despesa lançada nesse período ainda.
        </p>
      ) : (
        <>
          <ResponsiveContainer width="100%" height={200}>
            <PieChart>
              <Pie
                data={pieData}
                dataKey="value"
                nameKey="name"
                outerRadius={75}
                label={renderPercentLabel}
                labelLine={false}
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
            </PieChart>
          </ResponsiveContainer>
          {/* Legenda própria em HTML (não a <Legend> do recharts): essa vive
              dentro da altura fixa do gráfico e, com muitas categorias (ex:
              9), o texto não cabia e sobrepunha ("Compras" em cima de
              "Farmácia"). Em HTML puro a lista só cresce pra baixo com
              flex-wrap — nunca mais corta, não importa quantas categorias. */}
          <div className="mt-3 flex flex-wrap gap-x-4 gap-y-1.5">
            {pieData.map((entry, index) => (
              <div key={entry.name} className="flex items-center gap-1.5 text-sm">
                <span
                  className="inline-block h-2.5 w-2.5 shrink-0 rounded-full"
                  style={{ backgroundColor: entry.color ?? FALLBACK_COLORS[index % FALLBACK_COLORS.length] }}
                />
                <span className="text-gray-700 dark:text-gray-300">
                  {entry.name} — {formatCurrency(String(entry.value))}
                </span>
              </div>
            ))}
          </div>
        </>
      )}
      {footer}
    </div>
  )
}

// Formulário pra abater um valor da fatura fechada usando o "saldo em
// conta" — some do saldo e reduz o total da fatura, igual pagar de verdade.
function PayInvoiceForm({
  onPay,
  isPending,
  error,
}: {
  onPay: (amount: string) => void
  isPending: boolean
  error: string | null
}) {
  const [amount, setAmount] = useState('')
  const [localError, setLocalError] = useState<string | null>(null)

  const handleSubmit = () => {
    setLocalError(null)
    const apiAmount = toApiAmount(amount)
    if (!apiAmount || Number(apiAmount) <= 0) {
      setLocalError('Informe um valor válido')
      return
    }
    onPay(apiAmount)
    setAmount('')
  }

  return (
    <div className="mt-4 pt-3 border-t border-gray-200 dark:border-gray-700">
      <label className="block text-xs text-gray-500 dark:text-gray-400 mb-1">
        Abater da fatura com o saldo em conta
      </label>
      <div className="flex items-center gap-2">
        <input
          type="text"
          inputMode="decimal"
          placeholder="0,00"
          value={amount}
          onChange={(e) => setAmount(e.target.value)}
          className="w-28 rounded border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-700 px-2 py-1.5 text-sm text-gray-900 dark:text-gray-100"
        />
        <button
          type="button"
          onClick={handleSubmit}
          disabled={isPending}
          className="rounded bg-indigo-600 px-3 py-1.5 text-sm font-medium text-white hover:bg-indigo-700 disabled:opacity-50"
        >
          Abater
        </button>
      </div>
      {(localError || error) && <p className="text-sm text-red-600 mt-1">{localError || error}</p>}
    </div>
  )
}

export function DashboardPage() {
  const user = useAuthStore((s) => s.user)
  const updateUser = useAuthStore((s) => s.updateUser)
  const queryClient = useQueryClient()

  const { data: balances } = useQuery({
    queryKey: ['dashboard', 'balances'],
    queryFn: dashboardService.balances,
  })
  // Decide se é pra mostrar só a fatura em aberto (ainda não fechou esse
  // mês) ou a fatura fechada + a nova já em aberto (já fechou) — ver
  // backend/app/services/dashboard_service.py (cycle_view).
  const { data: cycleView } = useQuery({
    queryKey: ['dashboard', 'cycle-view'],
    queryFn: dashboardService.cycleView,
  })
  const { data: evolution } = useQuery({
    queryKey: ['dashboard', 'monthly-evolution'],
    queryFn: () => dashboardService.monthlyEvolution(6),
  })

  const openPeriod = cycleView?.open
  const closedPeriod = cycleView?.closed ?? undefined

  const { data: openSummary } = useQuery({
    queryKey: ['dashboard', 'summary', 'open', openPeriod?.date_from],
    queryFn: () => dashboardService.summary(openPeriod),
    enabled: !!openPeriod,
  })
  const { data: openByCategory } = useQuery({
    queryKey: ['dashboard', 'by-category', 'open', openPeriod?.date_from],
    queryFn: () => dashboardService.byCategory('expense', openPeriod),
    enabled: !!openPeriod,
  })
  const { data: closedSummary } = useQuery({
    queryKey: ['dashboard', 'summary', 'closed', closedPeriod?.date_from],
    queryFn: () => dashboardService.summary(closedPeriod),
    enabled: !!closedPeriod,
  })
  const { data: closedByCategory } = useQuery({
    queryKey: ['dashboard', 'by-category', 'closed', closedPeriod?.date_from],
    queryFn: () => dashboardService.byCategory('expense', closedPeriod),
    enabled: !!closedPeriod,
  })

  // Dia que fecha o ciclo financeiro (igual fatura de cartão) — cada pessoa
  // configura o seu. Editável aqui porque é o valor que muda os períodos
  // mostrados logo abaixo.
  const [closingDayInput, setClosingDayInput] = useState(String(user?.cycle_closing_day ?? 24))
  const [closingDayError, setClosingDayError] = useState<string | null>(null)

  const updateClosingDayMutation = useMutation({
    mutationFn: (day: number) => authService.updateSettings({ cycle_closing_day: day }),
    onSuccess: (updatedUser) => {
      updateUser(updatedUser)
      // Muda os períodos (open/closed) — os resumos/pizzas parametrizados
      // por período buscam sozinhos de novo, já que a chave da query muda
      // junto (date_from novo). Só precisa invalidar o cycle-view mesmo.
      queryClient.invalidateQueries({ queryKey: ['dashboard', 'cycle-view'] })
    },
    onError: (err) => {
      setClosingDayError(
        isAxiosError(err) && err.response?.status === 422
          ? 'Dia inválido — use um valor entre 1 e 31'
          : 'Não foi possível salvar o dia de fechamento',
      )
    },
  })

  const handleSaveClosingDay = () => {
    setClosingDayError(null)
    const day = Number(closingDayInput)
    if (!Number.isInteger(day) || day < 1 || day > 31) {
      setClosingDayError('Informe um dia entre 1 e 31')
      return
    }
    updateClosingDayMutation.mutate(day)
  }

  // "Saldo em conta" — o único saldo mostrado no topo do dashboard. É editado
  // à mão (quanto tem no banco de verdade); o "saldo total" calculado
  // (receitas - despesas de todo o histórico) foi descartado por pedido do
  // Matheus em 2026-08-24: ele prefere manter o controle manual desse valor,
  // sem um número calculado concorrendo com ele na tela.
  const [editingRealBalance, setEditingRealBalance] = useState(false)
  const [realBalanceInput, setRealBalanceInput] = useState('')
  const [realBalanceError, setRealBalanceError] = useState<string | null>(null)

  // Único usada pra editar/abater: a primeira conta do usuário. O app hoje
  // só lida com uma conta na prática — se um dia tiver várias, isso precisa
  // virar um seletor.
  const primaryAccountId = balances?.accounts[0]?.account_id

  const updateRealBalanceMutation = useMutation({
    mutationFn: (value: string) => accountService.update(primaryAccountId!, { real_balance: value }),
    onSuccess: () => {
      setEditingRealBalance(false)
      queryClient.invalidateQueries({ queryKey: ['dashboard', 'balances'] })
    },
    onError: () => setRealBalanceError('Não foi possível salvar o saldo em conta'),
  })

  const handleSaveRealBalance = () => {
    setRealBalanceError(null)
    const apiAmount = toApiAmount(realBalanceInput)
    if (apiAmount === null) {
      setRealBalanceError('Informe um valor válido')
      return
    }
    if (!primaryAccountId) {
      setRealBalanceError('Nenhuma conta cadastrada ainda')
      return
    }
    updateRealBalanceMutation.mutate(apiAmount)
  }

  const [payInvoiceError, setPayInvoiceError] = useState<string | null>(null)
  const payInvoiceMutation = useMutation({
    mutationFn: (amount: string) => accountService.payInvoice(primaryAccountId!, { amount }),
    onSuccess: () => {
      setPayInvoiceError(null)
      queryClient.invalidateQueries({ queryKey: ['dashboard', 'balances'] })
      // O valor abatido muda o total da fatura fechada — mesma lógica do
      // "Fecha todo dia": a chave da query (date_from do período) não muda,
      // então precisa invalidar explicitamente pra buscar de novo.
      queryClient.invalidateQueries({ queryKey: ['dashboard', 'summary', 'closed'] })
      queryClient.invalidateQueries({ queryKey: ['dashboard', 'by-category', 'closed'] })
    },
    onError: (err) => {
      setPayInvoiceError(
        isAxiosError(err) && err.response?.status === 409
          ? 'Ainda não tem fatura fechada nesse ciclo'
          : 'Não foi possível abater da fatura',
      )
    },
  })

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
        <p className="text-gray-500 dark:text-gray-400">Resumo do ciclo atual.</p>
      </div>

      <div className="bg-white dark:bg-gray-800 rounded-lg shadow p-4 flex flex-wrap items-end justify-between gap-3">
        <div>
          <p className="text-sm text-gray-500 dark:text-gray-400">Saldo em conta</p>
          {editingRealBalance ? (
            <div className="flex items-center gap-2 mt-1">
              <input
                type="text"
                inputMode="decimal"
                autoFocus
                placeholder="0,00"
                value={realBalanceInput}
                onChange={(e) => setRealBalanceInput(e.target.value)}
                className="w-28 rounded border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-700 px-2 py-1 text-gray-900 dark:text-gray-100"
              />
              <button
                type="button"
                onClick={handleSaveRealBalance}
                disabled={updateRealBalanceMutation.isPending}
                className="rounded bg-indigo-600 px-2 py-1 text-xs font-medium text-white hover:bg-indigo-700 disabled:opacity-50"
              >
                Salvar
              </button>
            </div>
          ) : (
            <button
              type="button"
              onClick={() => {
                setRealBalanceInput(balances?.total_real_balance ?? '')
                setEditingRealBalance(true)
              }}
              className="block text-2xl font-semibold text-gray-900 dark:text-gray-100 hover:underline text-left"
              title="Clique pra editar"
            >
              {balances?.total_real_balance != null ? formatCurrency(balances.total_real_balance) : 'Definir valor'}
            </button>
          )}
          {realBalanceError && <p className="text-sm text-red-600 mt-1">{realBalanceError}</p>}
        </div>
        <div className="flex items-end gap-2">
          <div>
            <label
              htmlFor="cycle-closing-day"
              className="block text-xs text-gray-500 dark:text-gray-400"
            >
              Fecha todo dia
            </label>
            {/* Igual fatura de cartão: a partir do dia seguinte a esse já
                conta pro próximo ciclo (ver backend/app/services/dashboard_service.py). */}
            <input
              id="cycle-closing-day"
              type="number"
              min={1}
              max={31}
              value={closingDayInput}
              onChange={(e) => setClosingDayInput(e.target.value)}
              className="mt-1 w-20 rounded border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-700 px-2 py-1.5 text-gray-900 dark:text-gray-100"
            />
          </div>
          <button
            type="button"
            onClick={handleSaveClosingDay}
            disabled={updateClosingDayMutation.isPending}
            className="rounded bg-indigo-600 px-3 py-1.5 text-sm font-medium text-white hover:bg-indigo-700 disabled:opacity-50"
          >
            Salvar
          </button>
        </div>
        {closingDayError && <p className="text-sm text-red-600 w-full">{closingDayError}</p>}
      </div>

      {!cycleView ? (
        <p className="text-gray-500 dark:text-gray-400">Carregando...</p>
      ) : (
        <div className={`grid grid-cols-1 gap-4 ${closedPeriod ? 'lg:grid-cols-2' : ''}`}>
          {closedPeriod && (
            <CyclePanel
              title="Fatura fechada (a pagar)"
              period={closedPeriod}
              summary={closedSummary}
              byCategory={closedByCategory}
              footer={
                primaryAccountId ? (
                  <PayInvoiceForm
                    onPay={(amount) => payInvoiceMutation.mutate(amount)}
                    isPending={payInvoiceMutation.isPending}
                    error={payInvoiceError}
                  />
                ) : undefined
              }
            />
          )}
          {openPeriod && (
            <CyclePanel
              title={closedPeriod ? 'Fatura em aberto (próxima)' : 'Fatura atual'}
              hint={closedPeriod ? undefined : 'ainda não fechou'}
              period={openPeriod}
              summary={openSummary}
              byCategory={openByCategory}
            />
          )}
        </div>
      )}

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
