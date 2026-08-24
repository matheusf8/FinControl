import { zodResolver } from '@hookform/resolvers/zod'
import { useState } from 'react'
import { useForm } from 'react-hook-form'
import { Link } from 'react-router-dom'
import { z } from 'zod'
import { ThemeToggle } from '../components/ThemeToggle'
import { authService } from '../services/authService'

const forgotPasswordSchema = z.object({
  email: z.string().email('E-mail inválido'),
})

type ForgotPasswordForm = z.infer<typeof forgotPasswordSchema>

export function ForgotPasswordPage() {
  const [sent, setSent] = useState(false)

  const {
    register,
    handleSubmit,
    formState: { errors, isSubmitting },
  } = useForm<ForgotPasswordForm>({ resolver: zodResolver(forgotPasswordSchema) })

  const onSubmit = async (data: ForgotPasswordForm) => {
    // window.location.origin: pra sempre montar o link do e-mail com a
    // origem certa, seja o site hospedado ou o .exe local (porta variável).
    await authService.forgotPassword({ email: data.email, reset_url_base: window.location.origin })
    // Sempre mostra a mesma mensagem de sucesso, exista ou não esse e-mail —
    // o backend também nunca revela isso (ver auth_service.forgot_password).
    setSent(true)
  }

  return (
    <div className="min-h-screen flex items-center justify-center bg-gray-50 dark:bg-gray-900 px-4">
      <div className="absolute top-4 right-4">
        <ThemeToggle />
      </div>
      <div className="w-full max-w-sm space-y-4 bg-white dark:bg-gray-800 p-8 rounded-lg shadow">
        <h1 className="text-2xl font-semibold text-gray-900 dark:text-gray-100">
          Esqueci minha senha
        </h1>

        {sent ? (
          <p className="text-sm text-gray-600 dark:text-gray-300">
            Se esse e-mail tiver uma conta, mandamos um link pra redefinir a senha — confira sua
            caixa de entrada (e o spam). O link vale por 1 hora.
          </p>
        ) : (
          <form onSubmit={handleSubmit(onSubmit)} noValidate className="space-y-4">
            <p className="text-sm text-gray-500 dark:text-gray-400">
              Informe o e-mail da sua conta e mandamos um link pra você escolher uma senha nova.
            </p>
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
                autoFocus
                className="mt-1 w-full rounded border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-700 px-3 py-2 text-gray-900 dark:text-gray-100"
                {...register('email')}
              />
              {errors.email && <p className="text-sm text-red-600 mt-1">{errors.email.message}</p>}
            </div>
            <button
              type="submit"
              disabled={isSubmitting}
              className="w-full rounded bg-indigo-600 py-2 text-white font-medium hover:bg-indigo-700 disabled:opacity-50"
            >
              {isSubmitting ? 'Enviando...' : 'Mandar link'}
            </button>
          </form>
        )}

        <p className="text-sm text-center text-gray-500 dark:text-gray-400">
          <Link to="/login" className="text-indigo-600 hover:underline">
            Voltar pro login
          </Link>
        </p>
      </div>
    </div>
  )
}
