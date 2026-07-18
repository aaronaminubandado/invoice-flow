import type { ReactElement, ReactNode } from 'react'
import { cn } from '@/lib/utils'

interface TooltipProps {
  label: string
  children: ReactElement
  side?: 'top' | 'bottom'
}

export function Tooltip({ label, children, side = 'top' }: TooltipProps) {
  return (
    <span className="group/tooltip relative inline-flex">
      <span aria-label={label} title={label} className="inline-flex">
        {children as ReactNode}
      </span>
      <span
        role="tooltip"
        className={cn(
          'pointer-events-none absolute z-50 whitespace-nowrap rounded-md bg-foreground px-2 py-1 text-xs text-background opacity-0 shadow-md transition-opacity group-hover/tooltip:opacity-100 group-focus-within/tooltip:opacity-100',
          side === 'top'
            ? 'bottom-full left-1/2 mb-2 -translate-x-1/2'
            : 'top-full left-1/2 mt-2 -translate-x-1/2'
        )}
      >
        {label}
      </span>
    </span>
  )
}
