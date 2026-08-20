import { api } from './api'
import type {
  BalancesResponse,
  CategoryBreakdownItem,
  CyclePeriod,
  CycleViewResponse,
  MonthlyEvolutionItem,
  SummaryResponse,
  WeeklySummaryResponse,
} from '../types/dashboard'
import type { FlowType } from '../types/finance'

export const dashboardService = {
  balances: () => api.get<BalancesResponse>('/dashboard/balances').then((r) => r.data),
  // Sem `period`, usa o ciclo corrente do usuário (comportamento padrão do
  // backend). Com `period`, força um intervalo específico — usado pra pegar
  // a fatura fechada e a em aberto separadamente (ver cycleView()).
  summary: (period?: CyclePeriod) =>
    api.get<SummaryResponse>('/dashboard/summary', { params: period }).then((r) => r.data),
  byCategory: (type: FlowType = 'expense', period?: CyclePeriod) =>
    api
      .get<CategoryBreakdownItem[]>('/dashboard/by-category', { params: { type, ...period } })
      .then((r) => r.data),
  cycleView: () => api.get<CycleViewResponse>('/dashboard/cycle-view').then((r) => r.data),
  monthlyEvolution: (months = 6) =>
    api
      .get<MonthlyEvolutionItem[]>('/dashboard/monthly-evolution', { params: { months } })
      .then((r) => r.data),
  // weekStart: qualquer data "AAAA-MM-DD" dentro da semana desejada (o
  // backend normaliza pra segunda-feira). Sem isso, usa a semana atual.
  weeklySummary: (weekStart?: string) =>
    api
      .get<WeeklySummaryResponse>('/dashboard/weekly', {
        params: weekStart ? { week_start: weekStart } : undefined,
      })
      .then((r) => r.data),
}
