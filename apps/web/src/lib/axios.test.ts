import { describe, expect, it } from 'vitest'
import { AxiosError } from 'axios'
import { getErrorMessage } from '@/lib/axios'

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
