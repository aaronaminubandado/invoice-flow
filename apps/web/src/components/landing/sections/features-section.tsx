import { cn } from '@/lib/utils'
import { SectionHeader } from '../ui/section-header'
import { StaggerContainer, StaggerItem } from '../ui/fade-in'
import { features } from '../data/landing-content'

function PaymentTrackingPreview() {
  const rows = [
    { label: 'INV-1042', status: 'Paid', color: 'text-emerald-500' },
    { label: 'INV-1041', status: 'Pending', color: 'text-amber-500' },
    { label: 'INV-1039', status: 'Overdue', color: 'text-red-500' },
  ]

  return (
    <div className="mt-4 rounded-lg border border-border/40 bg-background/50 p-3 space-y-2">
      {rows.map((row) => (
        <div key={row.label} className="flex items-center justify-between text-xs">
          <span className="font-mono text-muted-foreground">{row.label}</span>
          <span className={cn('font-medium', row.color)}>{row.status}</span>
        </div>
      ))}
    </div>
  )
}

function CurrencyPreview() {
  const currencies = ['USD', 'EUR', 'GBP', 'JPY']
  return (
    <div className="mt-4 flex gap-2">
      {currencies.map((c, i) => (
        <span
          key={c}
          className={cn(
            'px-2.5 py-1 rounded-md text-xs font-mono',
            i === 0
              ? 'bg-primary/10 text-primary font-medium'
              : 'bg-muted/50 text-muted-foreground'
          )}
        >
          {c}
        </span>
      ))}
    </div>
  )
}

export function FeaturesSection() {
  return (
    <section id="features" className="py-24 md:py-32" aria-labelledby="features-heading">
      <div className="mx-auto max-w-[1200px] px-4 sm:px-6">
        <SectionHeader
          eyebrow="Features"
          title="Everything you need to invoice and get paid"
          description="From your first client to your hundredth invoice, one workspace handles it all."
          className="mb-16"
        />

        <StaggerContainer className="grid md:grid-cols-2 lg:grid-cols-3 gap-5">
          {features.map((feature) => {
            const Icon = feature.icon
            return (
              <StaggerItem key={feature.title}>
                <div
                  className={cn(
                    'landing-surface rounded-2xl p-6 h-full landing-card-hover',
                    feature.large && 'md:row-span-1'
                  )}
                >
                  <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-landing-accent/10 mb-4">
                    <Icon className="h-5 w-5 text-landing-accent" aria-hidden="true" />
                  </div>
                  <h3
                    id={feature.title === features[0].title ? 'features-heading' : undefined}
                    className="font-display text-lg font-semibold text-landing-foreground mb-2"
                  >
                    {feature.title}
                  </h3>
                  <p className="text-sm text-landing-muted leading-relaxed">
                    {feature.description}
                  </p>
                  {feature.title === 'Payment tracking' && <PaymentTrackingPreview />}
                  {feature.title === 'Multi-currency' && <CurrencyPreview />}
                </div>
              </StaggerItem>
            )
          })}
        </StaggerContainer>
      </div>
    </section>
  )
}
