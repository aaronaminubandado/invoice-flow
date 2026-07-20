import * as React from 'react'
import { ChevronDown } from 'lucide-react'
import { cn } from '@/lib/utils'

interface AccordionItem {
  question: string
  answer: string
}

interface AccordionProps {
  items: AccordionItem[]
  className?: string
}

export function Accordion({ items, className }: AccordionProps) {
  const [openIndex, setOpenIndex] = React.useState<number | null>(null)

  const toggle = (index: number) => {
    setOpenIndex((prev) => (prev === index ? null : index))
  }

  return (
    <div className={cn('divide-y divide-border/60', className)}>
      {items.map((item, index) => {
        const isOpen = openIndex === index
        const panelId = `accordion-panel-${index}`
        const triggerId = `accordion-trigger-${index}`

        return (
          <div key={item.question}>
            <button
              id={triggerId}
              type="button"
              aria-expanded={isOpen}
              aria-controls={panelId}
              onClick={() => toggle(index)}
              className="flex w-full items-center justify-between gap-4 py-5 text-left transition-colors hover:text-landing-accent focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring rounded-sm"
            >
              <span className="font-medium text-landing-foreground">{item.question}</span>
              <ChevronDown
                className={cn(
                  'h-5 w-5 shrink-0 text-landing-muted transition-transform duration-200',
                  isOpen && 'rotate-180'
                )}
                aria-hidden="true"
              />
            </button>
            <div
              id={panelId}
              role="region"
              aria-labelledby={triggerId}
              className={cn(
                'grid transition-all duration-200 ease-out',
                isOpen ? 'grid-rows-[1fr] opacity-100 pb-5' : 'grid-rows-[0fr] opacity-0'
              )}
            >
              <div className="overflow-hidden">
                <p className="text-landing-muted leading-relaxed pr-8">{item.answer}</p>
              </div>
            </div>
          </div>
        )
      })}
    </div>
  )
}
