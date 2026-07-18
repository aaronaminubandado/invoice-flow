const SQL_ERROR_PATTERNS = [
  /sqlalchemy/i,
  /integrityerror/i,
  /uniqueviolation/i,
  /asyncpg/i,
  /duplicate key/i,
  /violates unique constraint/i,
]

const TRANSITION_ERROR_MAP: Record<string, string> = {
  'draft invoices must be sent before they can be paid.':
    'Draft invoices must be sent before they can be paid.',
  'this invoice cannot be marked as paid in its current status.':
    'This invoice cannot be marked as paid in its current status.',
  'this invoice cannot be cancelled in its current status.':
    'This invoice cannot be cancelled in its current status.',
  'this action is not allowed for the current invoice status.':
    'This action is not allowed for the current invoice status.',
}

function looksLikeSqlError(message: string): boolean {
  return SQL_ERROR_PATTERNS.some((pattern) => pattern.test(message))
}

export function mapApiErrorDetail(
  detail: unknown,
  status?: number
): string | null {
  if (typeof detail !== 'string' || !detail.trim()) {
    return null
  }

  const normalized = detail.trim()
  const lower = normalized.toLowerCase()

  if (looksLikeSqlError(normalized)) {
    if (lower.includes('invoice_number')) {
      return 'An invoice with this number already exists. Please try again.'
    }
    if (status === 409) {
      return 'This action conflicts with existing data. Please refresh and try again.'
    }
    return 'Something went wrong while saving. Please try again.'
  }

  if (lower.startsWith('invalid transition from')) {
    return 'This action is not allowed for the current invoice status.'
  }

  if (lower.startsWith('failed to create invoice:')) {
    return 'Could not create the invoice. Please try again.'
  }

  return TRANSITION_ERROR_MAP[lower] ?? normalized
}
