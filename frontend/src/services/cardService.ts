import { api } from './api'
import type { Card, CardPayload, Installment, InstallmentPurchasePayload, Invoice } from '../types/card'

export const cardService = {
  list: () => api.get<Card[]>('/cards').then((r) => r.data),
  create: (payload: CardPayload) => api.post<Card>('/cards', payload).then((r) => r.data),
  remove: (id: string) => api.delete(`/cards/${id}`).then(() => undefined),
  createPurchase: (cardId: string, payload: InstallmentPurchasePayload) =>
    api.post<Installment[]>(`/cards/${cardId}/purchases`, payload).then((r) => r.data),
  getInvoice: (cardId: string, month: string) =>
    api.get<Invoice>(`/cards/${cardId}/invoice`, { params: { month } }).then((r) => r.data),
  deletePurchase: (purchaseGroupId: string) =>
    api.delete(`/cards/purchases/${purchaseGroupId}`).then(() => undefined),
}
