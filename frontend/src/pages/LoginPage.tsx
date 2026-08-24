import { zodResolver } from '@hookform/resolvers/zod'
import { useState } from 'react'
import { useForm } from 'react-hook-form'
import { Link, useNavigate } from 'react-router-dom'
import { z } from 'zod'
import { ThemeToggle } from '../components/ThemeToggle'
import { authService } from '../services/authService'
import { useAuthStore } from '../store/authStore'

const loginSchema = z.object({
  email: z.string().email('E-mail inválido'),
  password: z.string().min(1, 'Informe a senha'),
})

type LoginForm = z.infer<typeof loginSchema>

export function LoginPage() {
  const navigate = useNavigate()
  const [serverError, setServerError] = useState<string | null>(null)

  const {
    register,
    handleSubmit,
    formState: { errors, isSubmitting },
  } = useForm<LoginForm>({ resolver: zodResolver(loginSchema) })

  const onSubmit = async (data: LoginForm) => {
    setServerError(null)
    try {
      const token = await authService.login(data)
      // guarda os tokens já pra próxima chamada (me()) sair autenticada
      useAuthStore.getState().setTokens({
        accessToken: token.access_token,
        refreshToken: token.refresh_token,
      })
      const user = await authService.me()
      useAuthStore.getState().setAuth({
        user,
        accessToken: token.access_token,
        refreshToken: token.refresh_token,
      })
      navigate('/dashboard', { replace: true })
    } catch {
      setServerError('E-mail ou senha incorretos')
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
        <h1 className="text-2xl font-semibold text-gray-900 dark:text-gray-100">Entrar</h1>

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
          <Link
            to="/forgot-password"
            className="mt-1 inline-block text-xs text-indigo-600 dark:text-indigo-400 hover:underline"
          >
            Esqueci minha senha
          </Link>
        </div>

        {serverError && <p className="text-sm text-red-600">{serverError}</p>}

        <button
          type="submit"
          disabled={isSubmitting}
          className="w-full rounded bg-indigo-600 py-2 text-white font-medium hover:bg-indigo-700 disabled:opacity-50"
        >
          {isSubmitting ? 'Entrando...' : 'Entrar'}
        </button>

        <p className="text-sm text-center text-gray-500 dark:text-gray-400">
          Não tem conta?{' '}
          <Link to="/register" className="text-indigo-600 hover:underline">
            Cadastre-se
          </Link>
        </p>
      </form>
    </div>
  )
}
