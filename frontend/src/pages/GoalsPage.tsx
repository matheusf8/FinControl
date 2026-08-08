import { zodResolver } from '@hookform/resolvers/zod'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { useState } from 'react'
import { useForm } from 'react-hook-form'
import { z } from 'zod'
import { parseMoneyInput, toApiAmount } from '../lib/money'
import { goalService } from '../services/goalService'
import type { Goal } from '../types/goal'

function formatCurrency(value: string): string {
  return Number(value).toLocaleString('pt-BR', { style: 'currency', currency: 'BRL' })
}

const goalSchema = z.object({
  name: z.string().min(1, 'Informe um nome').max(120),
  targetAmount: z
    .string()
    .min(1, 'Informe o valor')
    .refine((v) => parseMoneyInput(v) > 0, 'O valor precisa ser maior que zero'),
  targetDate: z.string().optional(),
})
type GoalForm = z.infer<typeof goalSchema>

function GoalCard({ goal }: { goal: Goal }) {
  const queryClient = useQueryClient()
  const [contributeValue, setContributeValue] = useState('')
  const [error, setError] = useState<string | null>(null)

  const contributeMutation = useMutation({
    mutationFn: (amount: string) => goalService.contribute(goal.id, { amount }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['goals'] })
      setContributeValue('')
      setError(null)
    },
    onError: () => setError('Não foi possível registrar (o valor não pode deixar a meta negativa)'),
  })

  const handleContribute = () => {
    const parsed = parseMoneyInput(contributeValue)
    if (!Number.isFinite(parsed) || parsed === 0) {
      setError('Informe um valor válido (ex: 100,00 ou -50,00)')
      return
    }
    setError(null)
    contributeMutation.mutate(parsed.toFixed(2))
  }

  const deleteMutation = useMutation({
    mutationFn: () => goalService.remove(goal.id),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['goals'] }),
  })

  const percent = Math.min(Number(goal.progress_percent), 100)
  const isComplete = Number(goal.progress_percent) >= 100

  return (
    <div className="bg-white dark:bg-gray-800 rounded-lg shadow p-4 space-y-3">
      <div className="flex items-center justify-between">
        <div>
          <p className="font-medium text-gray-900 dark:text-gray-100">{goal.name}</p>
          {goal.target_date && (
            <p className="text-sm text-gray-500 dark:text-gray-400">
              até {new Date(`${goal.target_date}T00:00:00`).toLocaleDateString('pt-BR')}
            </p>
          )}
        </div>
        <button
          type="button"
          onClick={() => deleteMutation.mutate()}
          className="text-sm text-red-600 hover:underline"
        >
          Remover
        </button>
      </div>

      <div>
        <div className="h-3 w-full rounded-full bg-gray-200 dark:bg-gray-700 overflow-hidden">
          <div
            className={`h-full rounded-full ${isComplete ? 'bg-green-500' : 'bg-indigo-600'}`}
            style={{ width: `${percent}%` }}
          />
        </div>
        <p className="mt-1 text-sm text-gray-600 dark:text-gray-300">
          {formatCurrency(goal.current_amount)} de {formatCurrency(goal.target_amount)} ·{' '}
          {Number(goal.progress_percent).toLocaleString('pt-BR', { maximumFractionDigits: 0 })}%
          {isComplete && ' 🎉'}
        </p>
      </div>

      <div className="flex items-center gap-2">
        <input
          value={contributeValue}
          onChange={(e) => setContributeValue(e.target.value)}
          placeholder="valor (ex: 100,00 ou -50,00)"
          className="flex-1 rounded border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-700 px-3 py-1.5 text-sm text-gray-900 dark:text-gray-100"
        />
        <button
          type="button"
          disabled={!contributeValue || contributeMutation.isPending}
          onClick={handleContribute}
          className="rounded bg-indigo-600 px-3 py-1.5 text-sm text-white font-medium hover:bg-indigo-700 disabled:opacity-50"
        >
          Registrar
        </button>
      </div>
      {error && <p className="text-sm text-red-600">{error}</p>}
    </div>
  )
}

export function GoalsPage() {
  const queryClient = useQueryClient()
  const [error, setError] = useState<string | null>(null)

  const { data: goals, isLoading } = useQuery({ queryKey: ['goals'], queryFn: goalService.list })

  const {
    register,
    handleSubmit,
    reset,
    formState: { errors, isSubmitting },
  } = useForm<GoalForm>({
    resolver: zodResolver(goalSchema),
    defaultValues: { name: '', targetAmount: '', targetDate: '' },
  })

  const createMutation = useMutation({
    mutationFn: goalService.create,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['goals'] })
      reset({ name: '', targetAmount: '', targetDate: '' })
    },
    onError: () => setError('Não foi possível criar a meta'),
  })

  const onSubmit = (data: GoalForm) => {
    setError(null)
    createMutation.mutate({
      name: data.name,
      target_amount: toApiAmount(data.targetAmount) ?? data.targetAmount,
      target_date: data.targetDate || undefined,
    })
  }

  return (
    <div className="space-y-6">
      <h1 className="text-2xl font-semibold text-gray-900 dark:text-gray-100">Metas</h1>

      <form
        onSubmit={handleSubmit(onSubmit)}
        noValidate
        className="flex flex-wrap items-end gap-3 bg-white dark:bg-gray-800 p-4 rounded-lg shadow"
      >
        <div>
          <label className="block text-sm font-medium text-gray-700 dark:text-gray-300" htmlFor="goalName">
            Nome
          </label>
          <input
            id="goalName"
            placeholder="Viagem, reserva de emergência..."
            className="mt-1 rounded border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-700 px-3 py-2 text-gray-900 dark:text-gray-100"
            {...register('name')}
          />
          {errors.name && <p className="text-sm text-red-600 mt-1">{errors.name.message}</p>}
        </div>

        <div>
          <label
            className="block text-sm font-medium text-gray-700 dark:text-gray-300"
            htmlFor="targetAmount"
          >
            Valor alvo
          </label>
          <input
            id="targetAmount"
            placeholder="5000,00"
            className="mt-1 rounded border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-700 px-3 py-2 text-gray-900 dark:text-gray-100"
            {...register('targetAmount')}
          />
          {errors.targetAmount && (
            <p className="text-sm text-red-600 mt-1">{errors.targetAmount.message}</p>
          )}
        </div>

        <div>
          <label
            className="block text-sm font-medium text-gray-700 dark:text-gray-300"
            htmlFor="targetDate"
          >
            Data alvo (opcional)
          </label>
          <input
            id="targetDate"
            type="date"
            className="mt-1 rounded border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-700 px-3 py-2 text-gray-900 dark:text-gray-100"
            {...register('targetDate')}
          />
        </div>

        <button
          type="submit"
          disabled={isSubmitting}
          className="rounded bg-indigo-600 px-4 py-2 text-white font-medium hover:bg-indigo-700 disabled:opacity-50"
        >
          Criar meta
        </button>
      </form>
      {error && <p className="text-sm text-red-600">{error}</p>}

      {isLoading && <p className="text-gray-500 dark:text-gray-400">Carregando...</p>}
      {goals?.length === 0 && (
        <p className="text-gray-500 dark:text-gray-400">Nenhuma meta cadastrada ainda.</p>
      )}

      <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
        {goals?.map((goal) => (
          <GoalCard key={goal.id} goal={goal} />
        ))}
      </div>
    </div>
  )
}
