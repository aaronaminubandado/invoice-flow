import { useState, useRef, useEffect } from 'react'
import { Download, FileSpreadsheet, FileText, ChevronDown } from 'lucide-react'
import { Button } from './button'
import type { ExportFormat } from '@/services/invoices'

interface ExportDropdownProps {
  onExport: (format: ExportFormat) => void
  loading?: boolean
}

const formatOptions: { value: ExportFormat; label: string; icon: typeof Download; ext: string }[] = [
  { value: 'csv', label: 'CSV', icon: FileText, ext: '.csv' },
  { value: 'xlsx', label: 'Excel', icon: FileSpreadsheet, ext: '.xlsx' },
  { value: 'pdf', label: 'PDF', icon: Download, ext: '.pdf' },
]

export function ExportDropdown({ onExport, loading }: ExportDropdownProps) {
  const [open, setOpen] = useState(false)
  const ref = useRef<HTMLDivElement>(null)

  useEffect(() => {
    const handleClick = (e: MouseEvent) => {
      if (ref.current && !ref.current.contains(e.target as Node)) {
        setOpen(false)
      }
    }
    document.addEventListener('mousedown', handleClick)
    return () => document.removeEventListener('mousedown', handleClick)
  }, [])

  return (
    <div ref={ref} className="relative">
      <Button
        variant="outline"
        onClick={() => setOpen(!open)}
        disabled={loading}
        className="gap-2"
      >
        <Download className="h-4 w-4" />
        Export
        <ChevronDown className="h-3.5 w-3.5 text-muted-foreground" />
      </Button>

      {open && (
        <div className="absolute right-0 top-full mt-1.5 z-50 w-40 rounded-lg border border-border bg-card shadow-xl animate-scale-in overflow-hidden">
          {formatOptions.map((opt) => (
            <button
              key={opt.value}
              onClick={() => {
                onExport(opt.value)
                setOpen(false)
              }}
              className="flex w-full items-center gap-2.5 px-3 py-2.5 text-[13px] font-medium text-muted-foreground transition-colors hover:bg-accent hover:text-foreground"
            >
              <opt.icon className="h-4 w-4" />
              {opt.label}
              <span className="ml-auto text-[11px] text-muted-foreground/60 font-mono">
                {opt.ext}
              </span>
            </button>
          ))}
        </div>
      )}
    </div>
  )
}
