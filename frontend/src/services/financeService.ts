import { api } from './api'
import type {
  Account,
  AccountPayload,
  Category,
  CategoryPayload,
  InvoicePaymentPayload,
  Transaction,
  TransactionFilters,
  TransactionPayload,
  TransactionUpdatePayload,
} from '../types/finance'

export const accountService = {
  list: () => api.get<Account[]>('/accounts').then((r) => r.data),
  create: (payload: AccountPayload) => api.post<Account>('/accounts', payload).then((r) => r.data),
  update: (id: string, payload: Partial<AccountPayload> & { real_balance?: string }) =>
    api.put<Account>(`/accounts/${id}`, payload).then((r) => r.data),
  remove: (id: string) => api.delete(`/accounts/${id}`).then(() => undefined),
  // Abate `amount` da fatura fechada e desconta o mesmo valor do "saldo em
  // conta" dessa conta — ver backend/app/services/account_service.py.
  payInvoice: (accountId: string, payload: InvoicePaymentPayload) =>
    api.post<Account>(`/accounts/${accountId}/pay-invoice`, payload).then((r) => r.data),
}

export const categoryService = {
  list: () => api.get<Category[]>('/categories').then((r) => r.data),
  create: (payload: CategoryPayload) =>
    api.post<Category>('/categories', payload).then((r) => r.data),
  update: (id: string, payload: { name?: string; color?: string }) =>
    api.put<Category>(`/categories/${id}`, payload).then((r) => r.data),
  remove: (id: string) => api.delete(`/categories/${id}`).then(() => undefined),
}

export const transactionService = {
  list: (filters: TransactionFilters = {}) =>
    api.get<Transaction[]>('/transactions', { params: filters }).then((r) => r.data),
  create: (payload: TransactionPayload) =>
    api.post<Transaction>('/transactions', payload).then((r) => r.data),
  update: (id: string, payload: TransactionUpdatePayload) =>
    api.put<Transaction>(`/transactions/${id}`, payload).then((r) => r.data),
  remove: (id: string) => api.delete(`/transactions/${id}`).then(() => undefined),
}
