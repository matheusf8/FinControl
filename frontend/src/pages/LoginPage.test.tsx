import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { MemoryRouter } from 'react-router-dom'
import { describe, expect, it, vi } from 'vitest'
import { authService } from '../services/authService'
import { LoginPage } from './LoginPage'

vi.mock('../services/authService', () => ({
  authService: {
    login: vi.fn(),
    me: vi.fn(),
    register: vi.fn(),
  },
}))

function renderLoginPage() {
  const queryClient = new QueryClient()
  return render(
    <QueryClientProvider client={queryClient}>
      <MemoryRouter>
        <LoginPage />
      </MemoryRouter>
    </QueryClientProvider>,
  )
}

describe('LoginPage', () => {
  it('mostra erro de validação pra e-mail inválido e não chama a API', async () => {
    const user = userEvent.setup()
    renderLoginPage()

    await user.type(screen.getByLabelText('E-mail'), 'nao-e-email')
    await user.type(screen.getByLabelText('Senha'), '123')
    await user.click(screen.getByRole('button', { name: 'Entrar' }))

    expect(await screen.findByText('E-mail inválido')).toBeInTheDocument()
    expect(authService.login).not.toHaveBeenCalled()
  })

  it('mostra erro do servidor quando o login falha', async () => {
    vi.mocked(authService.login).mockRejectedValueOnce(new Error('unauthorized'))
    const user = userEvent.setup()
    renderLoginPage()

    await user.type(screen.getByLabelText('E-mail'), 'ana@example.com')
    await user.type(screen.getByLabelText('Senha'), 'senha1234')
    await user.click(screen.getByRole('button', { name: 'Entrar' }))

    expect(await screen.findByText('E-mail ou senha incorretos')).toBeInTheDocument()
  })
})
