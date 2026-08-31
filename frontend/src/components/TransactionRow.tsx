import { useMutation } from '@tanstack/react-query'
import { useState } from 'react'
import { toApiAmount } from '../lib/money'
import { transactionService } from '../services/financeService'
import type { Category, Transaction } from '../types/finance'

function formatCurrency(value: string): string {
  return Number(value).toLocaleString('pt-BR', { style: 'currency', currency: 'BRL' })
}

// Formata a data (string "YYYY-MM-DDTHH:mm:ss", sem timezone — ver nota em
// TransactionsPage/CardsPage) direto, sem passar por `new Date()`, só pra
// preencher o <input type="date"> na edição.
function toDateInputValue(iso: string): string {
  return iso.slice(0, 10)
}

// Uma transação, usada tanto na aba Transações quanto na lista "Dia a dia" da
// tela Semana — mostra os dados e, ao clicar "Editar", vira um formulariozinho
// inline (mesmo padrão do "Abater fatura"/"Editar saldo em conta" no
// Dashboard: useState local, sem react-hook-form, é só um form pequeno).
export function TransactionRow({
  transaction,
  categories,
  categoryName,
  accountName,
  onChanged,
  showScope = false,
}: {
  transaction: Transaction
  categories: Category[]
  categoryName?: string
  accountName?: string
  onChanged: () => void
  // Mostra um selo "avulso" quando a transação está fora da fatura
  // (counts_in_cycle=false). Usado na aba Transações, onde os dois tipos
  // convivem na mesma lista; na aba Semana é sempre avulso, então fica off.
  showScope?: boolean
}) {
  const [editing, setEditing] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const [type, setType] = useState(transaction.type)
  const [amount, setAmount] = useState(transaction.amount)
  const [categoryId, setCategoryId] = useState(transaction.category_id ?? '')
  const [description, setDescription] = useState(transaction.description ?? '')
  const [date, setDate] = useState(toDateInputValue(transaction.date))
  const [countsInCycle, setCountsInCycle] = useState(transaction.counts_in_cycle)

  const startEditing = () => {
    setType(transaction.type)
    setAmount(transaction.amount)
    setCategoryId(transaction.category_id ?? '')
    setDescription(transaction.description ?? '')
    setDate(toDateInputValue(transaction.date))
    setCountsInCycle(transaction.counts_in_cycle)
    setError(null)
    setEditing(true)
  }

  const updateMutation = useMutation({
    mutationFn: () => {
      const apiAmount = toApiAmount(amount)
      if (!apiAmount || Number(apiAmount) <= 0) throw new Error('valor inválido')
      return transactionService.update(transaction.id, {
        type,
        amount: apiAmount,
        category_id: categoryId || undefined,
        description: description || undefined,
        date: new Date(`${date}T00:00:00`).toISOString(),
        counts_in_cycle: countsInCycle,
      })
    },
    onSuccess: () => {
      setEditing(false)
      onChanged()
    },
    onError: () => setError('Não foi possível salvar — confira o valor e a data'),
  })

  const deleteMutation = useMutation({
    mutationFn: () => transactionService.remove(transaction.id),
    onSuccess: onChanged,
  })

  // Categorias do mesmo tipo que a transação sendo editada (troca de tipo no
  // form já reseta a categoria, ver onChange do select de tipo abaixo).
  const relevantCategories = categories.filter((c) => c.type === type)

  if (editing) {
    return (
      <div className="p-4 flex flex-wrap items-end gap-2 bg-indigo-50 dark:bg-indigo-950/30">
        <select
          value={type}
          onChange={(e) => {
            setType(e.target.value as 'income' | 'expense')
            setCategoryId('')
          }}
          className="rounded border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-700 px-2 py-1.5 text-sm text-gray-900 dark:text-gray-100"
        >
          <option value="expense">Despesa</option>
          <option value="income">Receita</option>
        </select>
        <input
          value={amount}
          onChange={(e) => setAmount(e.target.value)}
          placeholder="0,00"
          className="w-24 rounded border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-700 px-2 py-1.5 text-sm text-gray-900 dark:text-gray-100"
        />
        <select
          value={categoryId}
          onChange={(e) => setCategoryId(e.target.value)}
          className="rounded border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-700 px-2 py-1.5 text-sm text-gray-900 dark:text-gray-100"
        >
          <option value="">Sem categoria</option>
          {relevantCategories.map((c) => (
            <option key={c.id} value={c.id}>
              {c.name}
            </option>
          ))}
        </select>
        <input
          value={description}
          onChange={(e) => setDescription(e.target.value)}
          placeholder="Descrição"
          className="flex-1 min-w-[8rem] rounded border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-700 px-2 py-1.5 text-sm text-gray-900 dark:text-gray-100"
        />
        <input
          type="date"
          value={date}
          onChange={(e) => setDate(e.target.value)}
          className="rounded border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-700 px-2 py-1.5 text-sm text-gray-900 dark:text-gray-100"
        />
        {showScope && (
          <label
            className="flex items-center gap-1.5 text-sm text-gray-700 dark:text-gray-300"
            title="Desmarcado = gasto avulso (fora da fatura, aba Semana)."
          >
            <input
              type="checkbox"
              checked={countsInCycle}
              onChange={(e) => setCountsInCycle(e.target.checked)}
              className="rounded"
            />
            Na fatura
          </label>
        )}
        <button
          type="button"
          onClick={() => updateMutation.mutate()}
          disabled={updateMutation.isPending}
          className="rounded bg-indigo-600 px-3 py-1.5 text-sm font-medium text-white hover:bg-indigo-700 disabled:opacity-50"
        >
          Salvar
        </button>
        <button
          type="button"
          onClick={() => setEditing(false)}
          className="rounded bg-gray-200 dark:bg-gray-700 px-3 py-1.5 text-sm font-medium text-gray-900 dark:text-gray-100 hover:bg-gray-300 dark:hover:bg-gray-600"
        >
          Cancelar
        </button>
        {error && <p className="w-full text-sm text-red-600">{error}</p>}
      </div>
    )
  }

  return (
    <div className="p-4 flex items-center justify-between gap-3">
      <div>
        <p className="font-medium text-gray-900 dark:text-gray-100">
          {transaction.description || categoryName || 'Sem descrição'}
          {showScope && !transaction.counts_in_cycle && (
            <span className="ml-2 rounded bg-amber-100 dark:bg-amber-900/40 px-1.5 py-0.5 text-xs font-medium text-amber-700 dark:text-amber-400">
              avulso
            </span>
          )}
        </p>
        <p className="text-sm text-gray-500 dark:text-gray-400">
          {toDateInputValue(transaction.date).split('-').reverse().join('/')}
          {accountName && ` · ${accountName}`}
          {categoryName && ` · ${categoryName}`}
        </p>
      </div>
      <div className="flex items-center gap-3">
        <span
          className={`font-medium ${transaction.type === 'income' ? 'text-green-600' : 'text-red-600'}`}
        >
          {transaction.type === 'income' ? '+' : '-'} {formatCurrency(transaction.amount)}
        </span>
        <button
          type="button"
          onClick={startEditing}
          className="text-sm text-indigo-600 hover:underline"
        >
          Editar
        </button>
        <button
          type="button"
          onClick={() => deleteMutation.mutate()}
          disabled={deleteMutation.isPending}
          className="text-sm text-red-600 hover:underline disabled:opacity-50"
        >
          Remover
        </button>
      </div>
    </div>
  )
}
