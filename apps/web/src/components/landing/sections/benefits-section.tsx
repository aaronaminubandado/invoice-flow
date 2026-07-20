import { FadeIn } from '../ui/fade-in'
import { benefits, mockChartData } from '../data/landing-content'
import { MiniChart } from '../mockups/mini-chart'

function AnalyticsMockup() {
  const statuses = [
    { label: 'Paid', value: 68, color: 'bg-emerald-500' },
    { label: 'Pending', value: 22, color: 'bg-amber-500' },
    { label: 'Overdue', value: 10, color: 'bg-red-500' },
  ]

  return (
    <div className="landing-surface rounded-2xl p-6 space-y-6" aria-hidden="true">
      <div>
        <p className="text-sm font-medium text-landing-foreground mb-1">Monthly revenue</p>
        <p className="text-2xl font-semibold tabular-nums">$48,250</p>
        <p className="text-xs text-emerald-500 mt-1">+12.4% from last month</p>
      </div>

      <MiniChart data={mockChartData} height={100} width={320} />

      <div>
        <p className="text-sm font-medium text-landing-foreground mb-3">Payment status</p>
        <div className="flex h-2.5 rounded-full overflow-hidden mb-3">
          {statuses.map((s) => (
            <div
              key={s.label}
              className={s.color}
              style={{ width: `${s.value}%` }}
            />
          ))}
        </div>
        <div className="flex gap-4">
          {statuses.map((s) => (
            <div key={s.label} className="flex items-center gap-1.5 text-xs text-landing-muted">
              <div className={`h-2 w-2 rounded-full ${s.color}`} />
              {s.label} {s.value}%
            </div>
          ))}
        </div>
      </div>
    </div>
  )
}

export function BenefitsSection() {
  return (
    <section className="py-24 md:py-32 bg-landing-surface/50" aria-labelledby="benefits-heading">
      <div className="mx-auto max-w-[1200px] px-4 sm:px-6">
        <div className="grid lg:grid-cols-2 gap-12 lg:gap-20 items-center">
          <FadeIn>
            <p className="text-sm font-medium text-landing-accent mb-3 tracking-wide uppercase">
              Why Invoice Flow
            </p>
            <h2
              id="benefits-heading"
              className="font-display text-3xl md:text-4xl font-semibold tracking-tight text-landing-foreground leading-[1.1] mb-8"
            >
              Spend less time on invoicing, more on your work
            </h2>
            <div className="space-y-6">
              {benefits.map((benefit) => {
                const Icon = benefit.icon
                return (
                  <div key={benefit.title} className="flex gap-4">
                    <div className="flex h-10 w-10 shrink-0 items-center justify-center rounded-xl bg-landing-accent/10">
                      <Icon className="h-5 w-5 text-landing-accent" aria-hidden="true" />
                    </div>
                    <div>
                      <h3 className="font-medium text-landing-foreground mb-1">
                        {benefit.title}
                      </h3>
                      <p className="text-sm text-landing-muted leading-relaxed">
                        {benefit.description}
                      </p>
                    </div>
                  </div>
                )
              })}
            </div>
          </FadeIn>

          <FadeIn delay={0.2}>
            <AnalyticsMockup />
          </FadeIn>
        </div>
      </div>
    </section>
  )
}
