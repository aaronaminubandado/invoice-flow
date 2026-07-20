import { ImageIcon } from 'lucide-react'
import { cn } from '@/lib/utils'

interface FeatureScreenshotProps {
  label: string
  className?: string
}

export function FeatureScreenshot({ label, className }: FeatureScreenshotProps) {
  return (
    <div
      data-screenshot={label.toLowerCase().replace(/\s+/g, '-')}
      className={cn(
        'relative rounded-2xl landing-surface overflow-hidden aspect-[4/3]',
        className
      )}
    >
      <div className="absolute inset-0 landing-grid-bg opacity-40" />
      <div className="absolute inset-0 flex flex-col items-center justify-center gap-3 p-8">
        <div className="flex h-14 w-14 items-center justify-center rounded-xl bg-landing-accent/10">
          <ImageIcon className="h-6 w-6 text-landing-accent" aria-hidden="true" />
        </div>
        <p className="text-sm font-medium text-landing-muted text-center">
          Replace with screenshot
        </p>
        <p className="text-xs text-landing-muted/70">{label}</p>
      </div>
      <div className="absolute top-0 left-0 right-0 h-8 bg-landing-surface border-b border-border/40 flex items-center px-3 gap-1.5">
        <div className="h-2.5 w-2.5 rounded-full bg-red-400/60" />
        <div className="h-2.5 w-2.5 rounded-full bg-amber-400/60" />
        <div className="h-2.5 w-2.5 rounded-full bg-emerald-400/60" />
      </div>
    </div>
  )
}
