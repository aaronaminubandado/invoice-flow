import { describe, expect, it } from 'vitest'
import { formatCurrency } from '@/lib/utils'

describe('formatCurrency', () => {
  it('formats USD amounts', () => {
    expect(formatCurrency(1234.5, 'USD')).toBe('$1,234.50')
  })

  it('handles string input', () => {
    expect(formatCurrency('99.9', 'USD')).toBe('$99.90')
  })

  it('returns zero for invalid values', () => {
    expect(formatCurrency('not-a-number', 'USD')).toBe('$0.00')
  })
})
