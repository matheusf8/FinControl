import { zodResolver } from '@hookform/resolvers/zod'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { useState } from 'react'
import { useForm } from 'react-hook-form'
import { z } from 'zod'
import { cardService } from '../services/cardService'
import { categoryService } from '../services/financeService'

function todayIsoDate(): string {
  return new Date().toISOString().slice(0, 10)
}

function currentMonth(): string {
  return new Date().toISOString().slice(0, 7)
}

function formatCurrency(value: string): string {
  return Number(value).toLocaleString('pt-BR', { style: 'currency', currency: 'BRL' })
}

// z.coerce.number() dá conflito de tipos com o resolver do RHF (o form
// trabalha com string até o parse) — validamos como string e convertemos
// só na hora de montar o payload, mesmo padrão usado no resto do projeto.
function isIntInRange(value: string, min: number, max: number): boolean {
  const n = Number(value)
  return Number.isInteger(n) && n >= min && n <= max
}

const cardSchema = z.object({
  name: z.string().min(1, 'Informe um nome').max(120),
  closingDay: z
    .string()
    .min(1, 'Informe o dia')
    .refine((v) => isIntInRange(v, 1, 31), 'Entre 1 e 31'),
  dueDay: z
    .string()
    .min(1, 'Informe o dia')
    .refine((v) => isIntInRange(v, 1, 31), 'Entre 1 e 31'),
  limit: z.string().optional(),
})
type CardForm = z.infer<typeof cardSchema>

const purchaseSchema = z.object({
  description: z.string().max(255).optional(),
  categoryId: z.string().optional(),
  totalAmount: z
    .string()
    .min(1, 'Informe o valor')
    .refine((v) => Number(v) > 0, 'O valor precisa ser maior que zero'),
  installments: z
    .string()
    .min(1, 'Informe as parcelas')
    .refine((v) => isIntInRange(v, 1, 48), 'Entre 1x e 48x'),
  purchaseDate: z.string().min(1, 'Informe a data'),
})
type PurchaseForm = z.infer<typeof purchaseSchema>

export function CardsPage() {
  const queryClient = useQueryClient()
  const [error, setError] = useState<string | null>(null)
  const [selectedCardId, setSelectedCardId] = useState<string | null>(null)
  const [invoiceMonth, setInvoiceMonth] = useState(currentMonth())

  const { data: cards, isLoading } = useQuery({ queryKey: ['cards'], queryFn: cardService.list })
  const { data: categories } = useQuery({
    queryKey: ['categories'],
    queryFn: categoryService.list,
  })

  const selectedCard = cards?.find((c) => c.id === selectedCardId) ?? null

  const { data: invoice } = useQuery({
    queryKey: ['cards', selectedCardId, 'invoice', invoiceMonth],
    queryFn: () => cardService.getInvoice(selectedCardId as string, invoiceMonth),
    enabled: Boolean(selectedCardId),
  })

  const categoriesById = new Map((categories ?? []).map((c) => [c.id, c]))

  const cardForm = useForm<CardForm>({
    resolver: zodResolver(cardSchema),
    defaultValues: { name: '', closingDay: '1', dueDay: '10', limit: '' },
  })

  const createCardMutation = useMutation({
    mutationFn: cardService.create,
    onSuccess: (card) => {
      queryClient.invalidateQueries({ queryKey: ['cards'] })
      cardForm.reset({ name: '', closingDay: '1', dueDay: '10', limit: '' })
      setSelectedCardId(card.id)
    },
    onError: () => setError('Não foi possível criar o cartão'),
  })

  const deleteCardMutation = useMutation({
    mutationFn: cardService.remove,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['cards'] })
      setSelectedCardId(null)
    },
  })

  const purchaseForm = useForm<PurchaseForm>({
    resolver: zodResolver(purchaseSchema),
    defaultValues: {
      description: '',
      categoryId: '',
      totalAmount: '',
      installments: '1',
      purchaseDate: todayIsoDate(),
    },
  })

  const createPurchaseMutation = useMutation({
    mutationFn: (data: PurchaseForm) => {
      if (!selectedCardId) throw new Error('Nenhum cartão selecionado')
      return cardService.createPurchase(selectedCardId, {
        description: data.description || undefined,
        category_id: data.categoryId || undefined,
        total_amount: data.totalAmount,
        installments: Number(data.installments),
        purchase_date: data.purchaseDate,
      })
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['cards', selectedCardId, 'invoice'] })
      purchaseForm.reset({
        description: '',
        categoryId: '',
        totalAmount: '',
        installments: '1',
        purchaseDate: todayIsoDate(),
      })
    },
    onError: () => setError('Não foi possível lançar a compra'),
  })

  const deletePurchaseMutation = useMutation({
    mutationFn: cardService.deletePurchase,
    onSuccess: () =>
      queryClient.invalidateQueries({ queryKey: ['cards', selectedCardId, 'invoice'] }),
  })

  return (
    <div className="space-y-6">
      <h1 className="text-2xl font-semibold text-gray-900 dark:text-gray-100">Cartões</h1>

      <form
        onSubmit={cardForm.handleSubmit((data) =>
          createCardMutation.mutate({
            name: data.name,
            closing_day: Number(data.closingDay),
            due_day: Number(data.dueDay),
            limit: data.limit || '0',
          }),
        )}
        noValidate
        className="flex flex-wrap items-end gap-3 bg-white dark:bg-gray-800 p-4 rounded-lg shadow"
      >
        <div>
          <label className="block text-sm font-medium text-gray-700 dark:text-gray-300" htmlFor="cardName">
            Nome
          </label>
          <input
            id="cardName"
            placeholder="Nubank"
            className="mt-1 rounded border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-700 px-3 py-2 text-gray-900 dark:text-gray-100"
            {...cardForm.register('name')}
          />
          {cardForm.formState.errors.name && (
            <p className="text-sm text-red-600 mt-1">{cardForm.formState.errors.name.message}</p>
          )}
        </div>

        <div>
          <label
            className="block text-sm font-medium text-gray-700 dark:text-gray-300"
            htmlFor="closingDay"
          >
            Dia de fechamento
          </label>
          <input
            id="closingDay"
            type="number"
            min={1}
            max={31}
            className="mt-1 w-20 rounded border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-700 px-3 py-2 text-gray-900 dark:text-gray-100"
            {...cardForm.register('closingDay')}
          />
        </div>

        <div>
          <label className="block text-sm font-medium text-gray-700 dark:text-gray-300" htmlFor="dueDay">
            Dia de vencimento
          </label>
          <input
            id="dueDay"
            type="number"
            min={1}
            max={31}
            className="mt-1 w-20 rounded border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-700 px-3 py-2 text-gray-900 dark:text-gray-100"
            {...cardForm.register('dueDay')}
          />
        </div>

        <div>
          <label className="block text-sm font-medium text-gray-700 dark:text-gray-300" htmlFor="limit">
            Limite
          </label>
          <input
            id="limit"
            placeholder="0.00"
            className="mt-1 rounded border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-700 px-3 py-2 text-gray-900 dark:text-gray-100"
            {...cardForm.register('limit')}
          />
        </div>

        <button
          type="submit"
          disabled={cardForm.formState.isSubmitting}
          className="rounded bg-indigo-600 px-4 py-2 text-white font-medium hover:bg-indigo-700 disabled:opacity-50"
        >
          Adicionar cartão
        </button>
      </form>
      {error && <p className="text-sm text-red-600">{error}</p>}

      {isLoading && <p className="text-gray-500 dark:text-gray-400">Carregando...</p>}
      {cards?.length === 0 && (
        <p className="text-gray-500 dark:text-gray-400">Nenhum cartão cadastrado ainda.</p>
      )}

      {cards && cards.length > 0 && (
        <div className="flex flex-wrap gap-2">
          {cards.map((card) => (
            <div key={card.id} className="flex items-center gap-1">
              <button
                type="button"
                onClick={() => setSelectedCardId(card.id)}
                className={`rounded px-3 py-2 text-sm font-medium ${
                  selectedCardId === card.id
                    ? 'bg-indigo-600 text-white'
                    : 'bg-white dark:bg-gray-800 text-gray-900 dark:text-gray-100 shadow'
                }`}
              >
                {card.name} · fecha dia {card.closing_day}, vence dia {card.due_day}
              </button>
              <button
                type="button"
                onClick={() => deleteCardMutation.mutate(card.id)}
                className="text-sm text-red-600 hover:underline"
              >
                Remover
              </button>
            </div>
          ))}
        </div>
      )}

      {selectedCard && (
        <div className="space-y-4">
          <h2 className="text-lg font-medium text-gray-900 dark:text-gray-100">
            Nova compra — {selectedCard.name}
          </h2>

          <form
            onSubmit={purchaseForm.handleSubmit((data) => createPurchaseMutation.mutate(data))}
            noValidate
            className="flex flex-wrap items-end gap-3 bg-white dark:bg-gray-800 p-4 rounded-lg shadow"
          >
            <div className="flex-1 min-w-[10rem]">
              <label
                className="block text-sm font-medium text-gray-700 dark:text-gray-300"
                htmlFor="purchaseDescription"
              >
                Descrição
              </label>
              <input
                id="purchaseDescription"
                className="mt-1 w-full rounded border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-700 px-3 py-2 text-gray-900 dark:text-gray-100"
                {...purchaseForm.register('description')}
              />
            </div>

            <div>
              <label
                className="block text-sm font-medium text-gray-700 dark:text-gray-300"
                htmlFor="purchaseCategory"
              >
                Categoria
              </label>
              <select
                id="purchaseCategory"
                className="mt-1 rounded border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-700 px-3 py-2 text-gray-900 dark:text-gray-100"
                {...purchaseForm.register('categoryId')}
              >
                <option value="">Sem categoria</option>
                {categories
                  ?.filter((c) => c.type === 'expense')
                  .map((c) => (
                    <option key={c.id} value={c.id}>
                      {c.name}
                    </option>
                  ))}
              </select>
            </div>

            <div>
              <label
                className="block text-sm font-medium text-gray-700 dark:text-gray-300"
                htmlFor="totalAmount"
              >
                Valor total
              </label>
              <input
                id="totalAmount"
                placeholder="0.00"
                className="mt-1 w-28 rounded border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-700 px-3 py-2 text-gray-900 dark:text-gray-100"
                {...purchaseForm.register('totalAmount')}
              />
              {purchaseForm.formState.errors.totalAmount && (
                <p className="text-sm text-red-600 mt-1">
                  {purchaseForm.formState.errors.totalAmount.message}
                </p>
              )}
            </div>

            <div>
              <label
                className="block text-sm font-medium text-gray-700 dark:text-gray-300"
                htmlFor="installments"
              >
                Parcelas
              </label>
              <input
                id="installments"
                type="number"
                min={1}
                max={48}
                className="mt-1 w-20 rounded border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-700 px-3 py-2 text-gray-900 dark:text-gray-100"
                {...purchaseForm.register('installments')}
              />
            </div>

            <div>
              <label
                className="block text-sm font-medium text-gray-700 dark:text-gray-300"
                htmlFor="purchaseDate"
              >
                Data da compra
              </label>
              <input
                id="purchaseDate"
                type="date"
                className="mt-1 rounded border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-700 px-3 py-2 text-gray-900 dark:text-gray-100"
                {...purchaseForm.register('purchaseDate')}
              />
            </div>

            <button
              type="submit"
              disabled={purchaseForm.formState.isSubmitting}
              className="rounded bg-indigo-600 px-4 py-2 text-white font-medium hover:bg-indigo-700 disabled:opacity-50"
            >
              Lançar compra
            </button>
          </form>

          <div className="bg-white dark:bg-gray-800 rounded-lg shadow">
            <div className="p-4 flex items-center justify-between border-b border-gray-200 dark:border-gray-700">
              <h2 className="text-lg font-medium text-gray-900 dark:text-gray-100">
                Fatura de {invoiceMonth}
              </h2>
              <div className="flex items-center gap-2">
                <input
                  type="month"
                  value={invoiceMonth}
                  onChange={(e) => setInvoiceMonth(e.target.value)}
                  className="rounded border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-700 px-3 py-1.5 text-gray-900 dark:text-gray-100"
                />
                <span className="font-semibold text-gray-900 dark:text-gray-100">
                  Total: {invoice ? formatCurrency(invoice.total) : '—'}
                </span>
              </div>
            </div>
            <div className="divide-y divide-gray-200 dark:divide-gray-700">
              {invoice?.installments.length === 0 && (
                <p className="p-4 text-gray-500 dark:text-gray-400">Nenhuma parcela nesse mês.</p>
              )}
              {invoice?.installments.map((item) => (
                <div key={item.id} className="p-4 flex items-center justify-between">
                  <div>
                    <p className="font-medium text-gray-900 dark:text-gray-100">
                      {item.description || 'Sem descrição'}
                    </p>
                    <p className="text-sm text-gray-500 dark:text-gray-400">
                      {item.installment_number}/{item.installment_total}
                      {item.category_id && ` · ${categoriesById.get(item.category_id)?.name ?? ''}`}
                      {' · vence '}
                      {new Date(item.date).toLocaleDateString('pt-BR')}
                    </p>
                  </div>
                  <div className="flex items-center gap-3">
                    <span className="font-medium text-red-600">{formatCurrency(item.amount)}</span>
                    <button
                      type="button"
                      onClick={() => deletePurchaseMutation.mutate(item.purchase_group_id)}
                      className="text-sm text-red-600 hover:underline"
                    >
                      Remover compra
                    </button>
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
