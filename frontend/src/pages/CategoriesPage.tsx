import { zodResolver } from '@hookform/resolvers/zod'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { isAxiosError } from 'axios'
import { useState } from 'react'
import { useForm } from 'react-hook-form'
import { z } from 'zod'
import { categoryService } from '../services/financeService'

const categorySchema = z.object({
  name: z.string().min(1, 'Informe um nome').max(120),
  type: z.enum(['income', 'expense']),
  color: z
    .string()
    .regex(/^#[0-9a-fA-F]{6}$/, 'Cor inválida (ex: #22c55e)')
    .optional()
    .or(z.literal('')),
})

type CategoryForm = z.infer<typeof categorySchema>

export function CategoriesPage() {
  const queryClient = useQueryClient()
  const [error, setError] = useState<string | null>(null)

  const { data: categories, isLoading } = useQuery({
    queryKey: ['categories'],
    queryFn: categoryService.list,
  })

  const {
    register,
    handleSubmit,
    reset,
    formState: { errors, isSubmitting },
  } = useForm<CategoryForm>({
    resolver: zodResolver(categorySchema),
    defaultValues: { type: 'expense', name: '', color: '' },
  })

  const createMutation = useMutation({
    mutationFn: categoryService.create,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['categories'] })
      reset({ name: '', type: 'expense', color: '' })
    },
    onError: () => setError('Não foi possível criar a categoria'),
  })

  const deleteMutation = useMutation({
    mutationFn: categoryService.remove,
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['categories'] }),
    onError: (err) => {
      if (isAxiosError(err) && err.response?.status === 409) {
        setError('Essa categoria já tem transações e não pode ser removida')
      } else {
        setError('Não foi possível remover a categoria')
      }
    },
  })

  const onSubmit = (data: CategoryForm) => {
    setError(null)
    createMutation.mutate({
      name: data.name,
      type: data.type,
      color: data.color || undefined,
    })
  }

  return (
    <div className="space-y-6">
      <h1 className="text-2xl font-semibold text-gray-900 dark:text-gray-100">Categorias</h1>

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
            <option value="expense">Despesa</option>
            <option value="income">Receita</option>
          </select>
        </div>

        <div>
          <label className="block text-sm font-medium text-gray-700 dark:text-gray-300" htmlFor="color">
            Cor (opcional)
          </label>
          <input
            id="color"
            placeholder="#22c55e"
            className="mt-1 rounded border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-700 px-3 py-2 text-gray-900 dark:text-gray-100"
            {...register('color')}
          />
          {errors.color && <p className="text-sm text-red-600 mt-1">{errors.color.message}</p>}
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
        {categories?.length === 0 && (
          <p className="p-4 text-gray-500 dark:text-gray-400">Nenhuma categoria cadastrada ainda.</p>
        )}
        {categories?.map((category) => (
          <div key={category.id} className="p-4 flex items-center justify-between">
            <div className="flex items-center gap-2">
              {category.color && (
                <span
                  className="inline-block h-3 w-3 rounded-full"
                  style={{ backgroundColor: category.color }}
                />
              )}
              <div>
                <p className="font-medium text-gray-900 dark:text-gray-100">{category.name}</p>
                <p className="text-sm text-gray-500 dark:text-gray-400">
                  {category.type === 'income' ? 'Receita' : 'Despesa'}
                </p>
              </div>
            </div>
            <button
              type="button"
              onClick={() => {
                setError(null)
                deleteMutation.mutate(category.id)
              }}
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
