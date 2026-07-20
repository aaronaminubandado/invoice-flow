import { Link } from 'react-router-dom'
import { Check } from 'lucide-react'
import { cn } from '@/lib/utils'
import { Button } from '@/components/ui'
import { SectionHeader } from '../ui/section-header'
import { StaggerContainer, StaggerItem } from '../ui/fade-in'
import { pricingTiers } from '../data/landing-content'

export function PricingSection() {
  return (
    <section id="pricing" className="py-24 md:py-32 bg-landing-surface/50" aria-labelledby="pricing-heading">
      <div className="mx-auto max-w-[1200px] px-4 sm:px-6">
        <SectionHeader
          eyebrow="Pricing"
          title="Simple plans that grow with you"
          description="Start free. Upgrade when you need recurring invoices, multi-currency, or team access."
          className="mb-16"
        />

        <StaggerContainer className="grid md:grid-cols-3 gap-6 max-w-5xl mx-auto">
          {pricingTiers.map((tier) => (
            <StaggerItem key={tier.name}>
              <div
                className={cn(
                  'rounded-2xl p-6 h-full flex flex-col landing-card-hover',
                  tier.highlighted
                    ? 'landing-surface ring-2 ring-landing-accent shadow-lg shadow-landing-accent/10'
                    : 'landing-surface'
                )}
              >
                {tier.highlighted && (
                  <span className="inline-block self-start text-xs font-medium text-landing-accent bg-landing-accent/10 px-2.5 py-1 rounded-full mb-4">
                    Most popular
                  </span>
                )}
                <h3
                  id={tier.name === 'Starter' ? 'pricing-heading' : undefined}
                  className="font-display text-lg font-semibold text-landing-foreground"
                >
                  {tier.name}
                </h3>
                <div className="mt-3 mb-2">
                  <span className="text-3xl font-semibold tabular-nums">{tier.price}</span>
                  {tier.period && (
                    <span className="text-sm text-landing-muted ml-1">{tier.period}</span>
                  )}
                </div>
                <p className="text-sm text-landing-muted mb-6">{tier.description}</p>

                <ul className="space-y-3 mb-8 flex-1">
                  {tier.features.map((feature) => (
                    <li key={feature} className="flex items-start gap-2.5 text-sm text-landing-muted">
                      <Check className="h-4 w-4 text-landing-accent shrink-0 mt-0.5" aria-hidden="true" />
                      {feature}
                    </li>
                  ))}
                </ul>

                <Link to="/register">
                  <Button
                    variant={tier.highlighted ? 'default' : 'outline'}
                    className="w-full"
                  >
                    {tier.cta}
                  </Button>
                </Link>
              </div>
            </StaggerItem>
          ))}
        </StaggerContainer>

        <p className="text-center text-xs text-landing-muted/70 mt-8">
          Pricing preview — adjust before launch
        </p>
      </div>
    </section>
  )
}
