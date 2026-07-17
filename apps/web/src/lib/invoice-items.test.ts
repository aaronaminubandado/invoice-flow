import { describe, expect, it } from 'vitest'
import { invoiceItemsTotal, lineItemTotal } from '@/lib/invoice-items'

describe('invoice line item totals', () => {
  it('computes a single line total', () => {
    expect(lineItemTotal({ quantity: 2, unit_price: 10 })).toBe(20)
  })

  it('sums multiple line items', () => {
    expect(
      invoiceItemsTotal([
        { quantity: 2, unit_price: 10 },
        { quantity: 1, unit_price: 5.5 },
      ])
    ).toBe(25.5)
  })
})
