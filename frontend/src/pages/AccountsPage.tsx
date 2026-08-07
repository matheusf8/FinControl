import { zodResolver } from '@hookform/resolvers/zod'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { useState } from 'react'
import { useForm } from 'react-hook-form'
import { z } from 'zod'
import { accountService } from '../services/financeService'
import type { AccountType } from '../types/finance'

const ACCOUNT_TYPE_LABELS: Record<AccountType, string> = {
  checking: 'Conta corrente',
  savings: 'Poupança',
  wallet: 'Carteira',
  investment: 'Investimento',
  other: 'Outro',
}

const accountSchema = z.object({
  name: z.string().min(1, 'Informe um nome').max(120),
  type: z.enum(['checking', 'savings', 'wallet', 'investment', 'other']),
  initialBalance: z.string().optional(),
})

type AccountForm = z.infer<typeof accountSchema>

export function AccountsPage() {
  const queryClient = useQueryClient()
  const [error, setError] = useState<string | null>(null)

  const { data: accounts, isLoading } = useQuery({
    queryKey: ['accounts'],
    queryFn: accountService.list,
  })

  const {
    register,
    handleSubmit,
    reset,
    formState: { errors, isSubmitting },
  } = useForm<AccountForm>({
    resolver: zodResolver(accountSchema),
    defaultValues: { type: 'checking', name: '', initialBalance: '' },
  })

  const createMutation = useMutation({
    mutationFn: accountService.create,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['accounts'] })
      reset({ name: '', type: 'checking', initialBalance: '' })
    },
    onError: () => setError('Não foi possível criar a conta'),
  })

  const deleteMutation = useMutation({
    mutationFn: accountService.remove,
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['accounts'] }),
  })

  const onSubmit = (data: AccountForm) => {
    setError(null)
    createMutation.mutate({
      name: data.name,
      type: data.type,
      initial_balance: data.initialBalance || '0',
    })
  }

  return (
    <div className="space-y-6">
      <h1 className="text-2xl font-semibold text-gray-900 dark:text-gray-100">Contas</h1>

      <form
        onSubmit={handleSubmit(onSubmit)}
        noValidate
        className="flex flex-wrap items-end gap-3 bg-white dark:bg-gray-800 p-4 rounded-lg shadow"
      >
        <div>
          <label className="block text-sm font-medium text-gray-700 dark:text-gray-300" htmlFor="name">
            Nome
          </label>
          <input
            id="name"
            className="mt-1 rounded border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-700 px-3 py-2 text-gray-900 dark:text-gray-100"
            {...register('name')}
          />
          {errors.name && <p className="text-sm text-red-600 mt-1">{errors.name.message}</p>}
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
            {Object.entries(ACCOUNT_TYPE_LABELS).map(([value, label]) => (
              <option key={value} value={value}>
                {label}
              </option>
            ))}
          </select>
        </div>

        <div>
          <label
            className="block text-sm font-medium text-gray-700 dark:text-gray-300"
            htmlFor="initialBalance"
          >
            Saldo inicial
          </label>
          <input
            id="initialBalance"
            placeholder="0.00"
            className="mt-1 rounded border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-700 px-3 py-2 text-gray-900 dark:text-gray-100"
            {...register('initialBalance')}
          />
        </div>

        <button
          type="submit"
          disabled={isSubmitting}
          className="rounded bg-indigo-600 px-4 py-2 text-white font-medium hover:bg-indigo-700 disabled:opacity-50"
        >
          Adicionar
        </button>
      </form>
      {error && <p className="text-sm text-red-600">{error}</p>}

      <div className="bg-white dark:bg-gray-800 rounded-lg shadow divide-y divide-gray-200 dark:divide-gray-700">
        {isLoading && <p className="p-4 text-gray-500 dark:text-gray-400">Carregando...</p>}
        {accounts?.length === 0 && (
          <p className="p-4 text-gray-500 dark:text-gray-400">Nenhuma conta cadastrada ainda.</p>
        )}
        {accounts?.map((account) => (
          <div key={account.id} className="p-4 flex items-center justify-between">
            <div>
              <p className="font-medium text-gray-900 dark:text-gray-100">{account.name}</p>
              <p className="text-sm text-gray-500 dark:text-gray-400">
                {ACCOUNT_TYPE_LABELS[account.type]} · saldo inicial R$ {account.initial_balance}
              </p>
            </div>
            <button
              type="button"
              onClick={() => deleteMutation.mutate(account.id)}
              className="text-sm text-red-600 hover:underline"
            >
              Remover
            </button>
          </div>
        ))}
      </div>
    </div>
  )
}
