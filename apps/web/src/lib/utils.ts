import { clsx, type ClassValue } from 'clsx'
import { twMerge } from 'tailwind-merge'

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs))
}

const CURRENCY_SYMBOLS: Record<string, string> = {
  USD: '$',
  EUR: '€',
  GBP: '£',
  JPY: '¥',
}

export function formatCurrency(
  value: string | number,
  currency = 'USD'
): string {
  const num = typeof value === 'string' ? parseFloat(value) : value
  if (Number.isNaN(num)) return `${CURRENCY_SYMBOLS[currency] ?? '$'}0.00`
  return new Intl.NumberFormat('en-US', {
    style: 'currency',
    currency,
  }).format(num)
}

export function currencySymbol(currency = 'USD'): string {
  return CURRENCY_SYMBOLS[currency] ?? `${currency} `
}
