import { zodResolver } from '@hookform/resolvers/zod'
import { isAxiosError } from 'axios'
import { useState } from 'react'
import { useForm } from 'react-hook-form'
import { Link, useNavigate } from 'react-router-dom'
import { z } from 'zod'
import { ThemeToggle } from '../components/ThemeToggle'
import { authService } from '../services/authService'

const registerSchema = z
  .object({
    fullName: z.string().max(255).optional().or(z.literal('')),
    email: z.string().email('E-mail inválido'),
    // Limites espelham backend/app/schemas/auth.py (bcrypt trunca em 72 bytes)
    password: z.string().min(8, 'Mínimo de 8 caracteres').max(72, 'Máximo de 72 caracteres'),
    confirmPassword: z.string(),
    // Validado de verdade só no backend (settings.invite_code) — aqui é só
    // obrigatório não ficar em branco quando preenchido pelo usuário.
    inviteCode: z.string().min(1, 'Código de convite obrigatório'),
  })
  .refine((data) => data.password === data.confirmPassword, {
    message: 'As senhas não coincidem',
    path: ['confirmPassword'],
  })

type RegisterForm = z.infer<typeof registerSchema>

export function RegisterPage() {
  const navigate = useNavigate()
  const [serverError, setServerError] = useState<string | null>(null)

  const {
    register,
    handleSubmit,
    formState: { errors, isSubmitting },
  } = useForm<RegisterForm>({ resolver: zodResolver(registerSchema) })

  const onSubmit = async (data: RegisterForm) => {
    setServerError(null)
    try {
      await authService.register({
        email: data.email,
        password: data.password,
        full_name: data.fullName || undefined,
        invite_code: data.inviteCode,
      })
      navigate('/login', { replace: true })
    } catch (err) {
      if (isAxiosError(err) && err.response?.status === 409) {
        setServerError('Já existe uma conta com esse e-mail')
      } else if (isAxiosError(err) && err.response?.status === 403) {
        setServerError('Código de convite inválido')
      } else {
        setServerError('Não foi possível criar a conta, tente novamente')
      }
    }
  }

  return (
    <div className="min-h-screen flex items-center justify-center bg-gray-50 dark:bg-gray-900 px-4">
      <div className="absolute top-4 right-4">
        <ThemeToggle />
      </div>
      <form
        onSubmit={handleSubmit(onSubmit)}
        noValidate
        className="w-full max-w-sm space-y-4 bg-white dark:bg-gray-800 p-8 rounded-lg shadow"
      >
        <h1 className="text-2xl font-semibold text-gray-900 dark:text-gray-100">Criar conta</h1>

        <div>
          <label
            htmlFor="fullName"
            className="block text-sm font-medium text-gray-700 dark:text-gray-300"
          >
            Nome (opcional)
          </label>
          <input
            id="fullName"
            type="text"
            className="mt-1 w-full rounded border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-700 px-3 py-2 text-gray-900 dark:text-gray-100"
            {...register('fullName')}
          />
        </div>

        <div>
          <label
            htmlFor="email"
            className="block text-sm font-medium text-gray-700 dark:text-gray-300"
          >
            E-mail
          </label>
          <input
            id="email"
            type="email"
            className="mt-1 w-full rounded border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-700 px-3 py-2 text-gray-900 dark:text-gray-100"
            {...register('email')}
          />
          {errors.email && <p className="text-sm text-red-600 mt-1">{errors.email.message}</p>}
        </div>

        <div>
          <label
            htmlFor="password"
            className="block text-sm font-medium text-gray-700 dark:text-gray-300"
          >
            Senha
          </label>
          <input
            id="password"
            type="password"
            className="mt-1 w-full rounded border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-700 px-3 py-2 text-gray-900 dark:text-gray-100"
            {...register('password')}
          />
          {errors.password && (
            <p className="text-sm text-red-600 mt-1">{errors.password.message}</p>
          )}
        </div>

        <div>
          <label
            htmlFor="confirmPassword"
            className="block text-sm font-medium text-gray-700 dark:text-gray-300"
          >
            Confirmar senha
          </label>
          <input
            id="confirmPassword"
            type="password"
            className="mt-1 w-full rounded border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-700 px-3 py-2 text-gray-900 dark:text-gray-100"
            {...register('confirmPassword')}
          />
          {errors.confirmPassword && (
            <p className="text-sm text-red-600 mt-1">{errors.confirmPassword.message}</p>
          )}
        </div>

        <div>
          <label
            htmlFor="inviteCode"
            className="block text-sm font-medium text-gray-700 dark:text-gray-300"
          >
            Código de convite
          </label>
          <input
            id="inviteCode"
            type="text"
            className="mt-1 w-full rounded border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-700 px-3 py-2 text-gray-900 dark:text-gray-100"
            {...register('inviteCode')}
          />
          {errors.inviteCode && (
            <p className="text-sm text-red-600 mt-1">{errors.inviteCode.message}</p>
          )}
        </div>

        {serverError && <p className="text-sm text-red-600">{serverError}</p>}

        <button
          type="submit"
          disabled={isSubmitting}
          className="w-full rounded bg-indigo-600 py-2 text-white font-medium hover:bg-indigo-700 disabled:opacity-50"
        >
          {isSubmitting ? 'Criando...' : 'Criar conta'}
        </button>

        <p className="text-sm text-center text-gray-500 dark:text-gray-400">
          Já tem conta?{' '}
          <Link to="/login" className="text-indigo-600 hover:underline">
            Entrar
          </Link>
        </p>
      </form>
    </div>
  )
}
