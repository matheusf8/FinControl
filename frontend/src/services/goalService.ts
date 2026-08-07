import { api } from './api'
import type { Goal, GoalContributePayload, GoalPayload, GoalUpdatePayload } from '../types/goal'

export const goalService = {
  list: () => api.get<Goal[]>('/goals').then((r) => r.data),
  create: (payload: GoalPayload) => api.post<Goal>('/goals', payload).then((r) => r.data),
  update: (id: string, payload: GoalUpdatePayload) =>
    api.put<Goal>(`/goals/${id}`, payload).then((r) => r.data),
  remove: (id: string) => api.delete(`/goals/${id}`).then(() => undefined),
  contribute: (id: string, payload: GoalContributePayload) =>
    api.post<Goal>(`/goals/${id}/contribute`, payload).then((r) => r.data),
}
