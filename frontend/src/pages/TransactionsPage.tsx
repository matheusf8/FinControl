import { zodResolver } from '@hookform/resolvers/zod'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { useMemo, useState } from 'react'
import { useForm } from 'react-hook-form'
import { z } from 'zod'
import { TransactionRow } from '../components/TransactionRow'
import { parseMoneyInput, toApiAmount } from '../lib/money'
import { accountService, categoryService, transactionService } from '../services/financeService'
import type { FlowType, TransactionFilters } from '../types/finance'

const transactionSchema = z.object({
  accountId: z.string().min(1, 'Selecione uma conta'),
  categoryId: z.string().optional(),
  type: z.enum(['income', 'expense']),
  amount: z
    .string()
    .min(1, 'Informe o valor')
    .refine((v) => parseMoneyInput(v) > 0, 'O valor precisa ser maior que zero'),
  description: z.string().max(255).optional(),
  date: z.string().min(1, 'Informe a data'),
})

type TransactionForm = z.infer<typeof transactionSchema>

function todayIsoDate() {
  return new Date().toISOString().slice(0, 10)
}

export function TransactionsPage() {
  const queryClient = useQueryClient()
  const [error, setError] = useState<string | null>(null)
  const [filters, setFilters] = useState<TransactionFilters>({})

  const { data: accounts } = useQuery({ queryKey: ['accounts'], queryFn: accountService.list })
  const { data: categories } = useQuery({ queryKey: ['categories'], queryFn: categoryService.list })
  const { data: transactions, isLoading } = useQuery({
    queryKey: ['transactions', filters],
    queryFn: () => transactionService.list(filters),
  })

  const accountsById = useMemo(() => new Map((accounts ?? []).map((a) => [a.id, a])), [accounts])
  const categoriesById = useMemo(
    () => new Map((categories ?? []).map((c) => [c.id, c])),
    [categories],
  )

  const {
    register,
    handleSubmit,
    reset,
    formState: { errors, isSubmitting },
  } = useForm<TransactionForm>({
    resolver: zodResolver(transactionSchema),
    defaultValues: {
      type: 'expense',
      date: todayIsoDate(),
      accountId: '',
      categoryId: '',
      amount: '',
      description: '',
    },
  })

  const createMutation = useMutation({
    mutationFn: transactionService.create,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['transactions'] })
      reset({
        type: 'expense',
        date: todayIsoDate(),
        accountId: '',
        categoryId: '',
        amount: '',
        description: '',
      })
    },
    onError: () => setError('Não foi possível lançar a transação'),
  })

  const onSubmit = (data: TransactionForm) => {
    setError(null)
    createMutation.mutate({
      account_id: data.accountId,
      category_id: data.categoryId || undefined,
      type: data.type,
      amount: toApiAmount(data.amount) ?? data.amount,
      description: data.description || undefined,
      date: new Date(data.date).toISOString(),
    })
  }

  const hasAccounts = (accounts?.length ?? 0) > 0

  return (
    <div className="space-y-6">
      <h1 className="text-2xl font-semibold text-gray-900 dark:text-gray-100">Transações</h1>

      {!hasAccounts && (
        <p className="text-sm text-amber-600 dark:text-amber-400">
          Cadastre uma conta na aba "Contas" antes de lançar uma transação.
        </p>
      )}

      {hasAccounts && (
        <form
          onSubmit={handleSubmit(onSubmit)}
          noValidate
          className="flex flex-wrap items-end gap-3 bg-white dark:bg-gray-800 p-4 rounded-lg shadow"
        >
          <div>
            <label
              className="block text-sm font-medium text-gray-700 dark:text-gray-300"
              htmlFor="accountId"
            >
              Conta
            </label>
            <select
              id="accountId"
              className="mt-1 rounded border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-700 px-3 py-2 text-gray-900 dark:text-gray-100"
              {...register('accountId')}
            >
              <option value="">Selecione</option>
              {accounts?.map((a) => (
                <option key={a.id} value={a.id}>
                  {a.name}
                </option>
              ))}
            </select>
            {errors.accountId && (
              <p className="text-sm text-red-600 mt-1">{errors.accountId.message}</p>
            )}
          </div>

          <div>
            <label
              className="block text-sm font-medium text-gray-700 dark:text-gray-300"
              htmlFor="categoryId"
            >
              Categoria
            </label>
            <select
              id="categoryId"
              className="mt-1 rounded border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-700 px-3 py-2 text-gray-900 dark:text-gray-100"
              {...register('categoryId')}
            >
              <option value="">Sem categoria</option>
              {categories?.map((c) => (
                <option key={c.id} value={c.id}>
                  {c.name}
                </option>
              ))}
            </select>
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 dark:text-gray-300" htmlFor="type">
              Tipo
            </label>
            <select
              id="type"
              className="mt-1 rounded border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-700 px-3 py-2 text-gray-900 dark:text-gray-100"
              {...register('type')}
            >
              <option value="expense">Despesa</option>
              <option value="income">Receita</option>
            </select>
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 dark:text-gray-300" htmlFor="amount">
              Valor
            </label>
            <input
              id="amount"
              placeholder="0,00"
              className="mt-1 w-28 rounded border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-700 px-3 py-2 text-gray-900 dark:text-gray-100"
              {...register('amount')}
            />
            {errors.amount && <p className="text-sm text-red-600 mt-1">{errors.amount.message}</p>}
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 dark:text-gray-300" htmlFor="date">
              Data
            </label>
            <input
              id="date"
              type="date"
              className="mt-1 rounded border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-700 px-3 py-2 text-gray-900 dark:text-gray-100"
              {...register('date')}
            />
            {errors.date && <p className="text-sm text-red-600 mt-1">{errors.date.message}</p>}
          </div>

          <div className="flex-1 min-w-[10rem]">
            <label
              className="block text-sm font-medium text-gray-700 dark:text-gray-300"
              htmlFor="description"
            >
              Descrição (opcional)
            </label>
            <input
              id="description"
              className="mt-1 w-full rounded border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-700 px-3 py-2 text-gray-900 dark:text-gray-100"
              {...register('description')}
            />
          </div>

          <button
            type="submit"
            disabled={isSubmitting}
            className="rounded bg-indigo-600 px-4 py-2 text-white font-medium hover:bg-indigo-700 disabled:opacity-50"
          >
            Lançar
          </button>
        </form>
      )}
      {error && <p className="text-sm text-red-600">{error}</p>}

      <div className="flex flex-wrap items-end gap-3 bg-white dark:bg-gray-800 p-4 rounded-lg shadow">
        <div>
          <label
            className="block text-sm font-medium text-gray-700 dark:text-gray-300"
            htmlFor="filterType"
          >
            Filtrar por tipo
          </label>
          <select
            id="filterType"
            className="mt-1 rounded border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-700 px-3 py-2 text-gray-900 dark:text-gray-100"
            value={filters.type ?? ''}
            onChange={(e) =>
              setFilters((f) => ({
                ...f,
                type: (e.target.value || undefined) as FlowType | undefined,
              }))
            }
          >
            <option value="">Todos</option>
            <option value="expense">Despesa</option>
            <option value="income">Receita</option>
          </select>
        </div>

        <div>
          <label
            className="block text-sm font-medium text-gray-700 dark:text-gray-300"
            htmlFor="filterCategory"
          >
            Filtrar por categoria
          </label>
          <select
            id="filterCategory"
            className="mt-1 rounded border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-700 px-3 py-2 text-gray-900 dark:text-gray-100"
            value={filters.category_id ?? ''}
            onChange={(e) => setFilters((f) => ({ ...f, category_id: e.target.value || undefined }))}
          >
            <option value="">Todas</option>
            {categories?.map((c) => (
              <option key={c.id} value={c.id}>
                {c.name}
              </option>
            ))}
          </select>
        </div>

        <div>
          <label className="block text-sm font-medium text-gray-700 dark:text-gray-300" htmlFor="dateFrom">
            De
          </label>
          <input
            id="dateFrom"
            type="date"
            className="mt-1 rounded border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-700 px-3 py-2 text-gray-900 dark:text-gray-100"
            value={filters.date_from?.slice(0, 10) ?? ''}
            onChange={(e) =>
              setFilters((f) => ({
                ...f,
                date_from: e.target.value ? new Date(e.target.value).toISOString() : undefined,
              }))
            }
          />
        </div>

        <div>
          <label className="block text-sm font-medium text-gray-700 dark:text-gray-300" htmlFor="dateTo">
            Até
          </label>
          <input
            id="dateTo"
            type="date"
            className="mt-1 rounded border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-700 px-3 py-2 text-gray-900 dark:text-gray-100"
            value={filters.date_to?.slice(0, 10) ?? ''}
            onChange={(e) =>
              setFilters((f) => ({
                ...f,
                date_to: e.target.value ? new Date(e.target.value).toISOString() : undefined,
              }))
            }
          />
        </div>
      </div>

      <div className="bg-white dark:bg-gray-800 rounded-lg shadow divide-y divide-gray-200 dark:divide-gray-700">
        {isLoading && <p className="p-4 text-gray-500 dark:text-gray-400">Carregando...</p>}
        {transactions?.length === 0 && (
          <p className="p-4 text-gray-500 dark:text-gray-400">Nenhuma transação encontrada.</p>
        )}
        {transactions?.map((t) => (
          <TransactionRow
            key={t.id}
            transaction={t}
            categories={categories ?? []}
            categoryName={t.category_id ? categoriesById.get(t.category_id)?.name : undefined}
            accountName={t.account_id ? accountsById.get(t.account_id)?.name : undefined}
            onChanged={() => queryClient.invalidateQueries({ queryKey: ['transactions'] })}
          />
        ))}
      </div>
    </div>
  )
}
