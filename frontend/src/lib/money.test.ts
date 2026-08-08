import { describe, expect, it } from 'vitest'
import { parseMoneyInput, toApiAmount } from './money'

describe('parseMoneyInput', () => {
  it('entende formato brasileiro com milhar e decimal (o bug reportado)', () => {
    expect(parseMoneyInput('1.356,92')).toBe(1356.92)
  })

  it('entende formato brasileiro sem milhar', () => {
    expect(parseMoneyInput('50,00')).toBe(50)
    expect(parseMoneyInput('50,5')).toBe(50.5)
  })

  it('continua entendendo formato simples (ponto decimal)', () => {
    expect(parseMoneyInput('1356.92')).toBe(1356.92)
    expect(parseMoneyInput('100')).toBe(100)
  })

  it('entende negativo (retirada de meta)', () => {
    expect(parseMoneyInput('-1.356,92')).toBe(-1356.92)
  })
})

describe('toApiAmount', () => {
  it('converte formato brasileiro pro formato da API', () => {
    expect(toApiAmount('1.356,92')).toBe('1356.92')
  })

  it('sempre fecha com 2 casas decimais', () => {
    expect(toApiAmount('50')).toBe('50.00')
    expect(toApiAmount('50,5')).toBe('50.50')
  })

  it('retorna null pra entrada inválida', () => {
    expect(toApiAmount('abc')).toBeNull()
    expect(toApiAmount('')).toBeNull()
  })
})
