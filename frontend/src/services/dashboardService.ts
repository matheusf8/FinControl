import { api } from './api'
import type {
  BalancesResponse,
  CategoryBreakdownItem,
  MonthlyEvolutionItem,
  SummaryResponse,
} from '../types/dashboard'
import type { FlowType } from '../types/finance'

export const dashboardService = {
  balances: () => api.get<BalancesResponse>('/dashboard/balances').then((r) => r.data),
  summary: () => api.get<SummaryResponse>('/dashboard/summary').then((r) => r.data),
  byCategory: (type: FlowType = 'expense') =>
    api
      .get<CategoryBreakdownItem[]>('/dashboard/by-category', { params: { type } })
      .then((r) => r.data),
  monthlyEvolution: (months = 6) =>
    api
      .get<MonthlyEvolutionItem[]>('/dashboard/monthly-evolution', { params: { months } })
      .then((r) => r.data),
}
