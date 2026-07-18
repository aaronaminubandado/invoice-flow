import type { BadgeProps } from './badge'

export function getStatusBadgeVariant(
  status: string
): NonNullable<BadgeProps['variant']> {
  switch (status) {
    case 'paid':
      return 'success'
    case 'sent':
      return 'info'
    case 'overdue':
      return 'destructive'
    case 'partial':
      return 'warning'
    case 'cancelled':
    case 'void':
    case 'draft':
      return 'secondary'
    default:
      return 'default'
  }
}
