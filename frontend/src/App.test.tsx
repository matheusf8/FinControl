import { render, screen } from '@testing-library/react'
import { describe, expect, it } from 'vitest'
import App from './App'

describe('App', () => {
  it('renderiza o título FinControl', () => {
    render(<App />)
    expect(screen.getByText('FinControl')).toBeInTheDocument()
  })
})
