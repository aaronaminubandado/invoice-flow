import { describe, expect, it } from 'vitest'
import { AxiosError } from 'axios'
import { getErrorMessage } from '@/lib/axios'
import { mapApiErrorDetail } from '@/lib/api-errors'

describe('mapApiErrorDetail', () => {
  it('maps SQL errors to friendly messages', () => {
    expect(
      mapApiErrorDetail(
        'IntegrityError: duplicate key value violates unique constraint "invoices_invoice_number_key"',
        500
      )
    ).toBe('An invoice with this number already exists. Please try again.')
  })

  it('maps legacy transition errors', () => {
    expect(
      mapApiErrorDetail(
        "Invalid transition from 'draft' to 'paid'. Allowed: ['sent', 'cancelled']"
      )
    ).toBe('This action is not allowed for the current invoice status.')
  })
})

describe('getErrorMessage', () => {
  it('returns API detail message', () => {
    const error = new AxiosError(
      'Request failed',
      undefined,
      undefined,
      undefined,
      {
        status: 400,
        data: { detail: 'Client not found' },
        statusText: 'Bad Request',
        headers: {},
        config: {} as never,
      }
    )
    expect(getErrorMessage(error)).toBe('Client not found')
  })

  it('returns message for generic errors', () => {
    expect(getErrorMessage(new Error('boom'))).toBe('boom')
  })

  it('returns fallback for unknown errors', () => {
    expect(getErrorMessage(null)).toBe('An unknown error occurred')
  })
})
