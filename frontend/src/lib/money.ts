/**
 * Entrada de valores em dinheiro: aceita tanto o formato brasileiro
 * ("1.356,92", ponto de milhar + vírgula decimal) quanto o formato simples
 * ("1356.92" ou "1356"). O backend (Decimal do Python) só entende o segundo
 * formato, então toda tela que manda um valor pra API precisa passar por
 * `toApiAmount` antes de enviar.
 */

/** Converte a string digitada pelo usuário num number utilizável em cálculos/validação. */
export function parseMoneyInput(raw: string): number {
  const trimmed = raw.trim()
  // Number('') é 0 em JS (não NaN) — trataria "vazio" como um valor válido.
  if (trimmed === '') return NaN
  // Tem vírgula -> é formato BR: ponto é milhar (remove) e vírgula é decimal (vira ponto).
  // Sem vírgula -> assume que já é formato simples (ex: "1356.92" ou "1356").
  const normalized = trimmed.includes(',') ? trimmed.replace(/\./g, '').replace(',', '.') : trimmed
  return Number(normalized)
}

/** Converte pro formato que a API espera ("1356.92"), ou null se não for um valor válido. */
export function toApiAmount(raw: string): string | null {
  const value = parseMoneyInput(raw)
  return Number.isFinite(value) ? value.toFixed(2) : null
}
