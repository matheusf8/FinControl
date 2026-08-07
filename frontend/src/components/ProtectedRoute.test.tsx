import { render, screen } from '@testing-library/react'
import { MemoryRouter, Route, Routes } from 'react-router-dom'
import { describe, expect, it } from 'vitest'
import { useAuthStore } from '../store/authStore'
import { ProtectedRoute } from './ProtectedRoute'

function renderProtected(initialPath = '/private') {
  return render(
    <MemoryRouter initialEntries={[initialPath]}>
      <Routes>
        <Route path="/login" element={<div>Página de login</div>} />
        <Route
          path="/private"
          element={
            <ProtectedRoute>
              <div>Conteúdo protegido</div>
            </ProtectedRoute>
          }
        />
      </Routes>
    </MemoryRouter>,
  )
}

describe('ProtectedRoute', () => {
  it('redireciona pra /login sem token', () => {
    renderProtected()
    expect(screen.getByText('Página de login')).toBeInTheDocument()
  })

  it('renderiza os filhos quando autenticado', () => {
    useAuthStore.setState({ accessToken: 'fake-token', refreshToken: 'fake-refresh', user: null })
    renderProtected()
    expect(screen.getByText('Conteúdo protegido')).toBeInTheDocument()
  })
})
