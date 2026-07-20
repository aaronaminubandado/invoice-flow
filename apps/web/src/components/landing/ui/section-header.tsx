import { cn } from '@/lib/utils'
import { FadeIn } from './fade-in'

interface SectionHeaderProps {
  eyebrow?: string
  title: string
  description?: string
  align?: 'left' | 'center'
  className?: string
}

export function SectionHeader({
  eyebrow,
  title,
  description,
  align = 'center',
  className,
}: SectionHeaderProps) {
  return (
    <FadeIn className={cn('max-w-2xl', align === 'center' && 'mx-auto text-center', className)}>
      {eyebrow && (
        <p className="text-sm font-medium text-landing-accent mb-3 tracking-wide uppercase">
          {eyebrow}
        </p>
      )}
      <h2 className="font-display text-3xl md:text-4xl lg:text-[2.75rem] font-semibold tracking-tight text-landing-foreground leading-[1.1]">
        {title}
      </h2>
      {description && (
        <p className="mt-4 text-lg text-landing-muted leading-relaxed">{description}</p>
      )}
    </FadeIn>
  )
}
