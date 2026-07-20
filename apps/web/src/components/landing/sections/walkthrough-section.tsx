import { useState } from 'react'
import { cn } from '@/lib/utils'
import { SectionHeader } from '../ui/section-header'
import { FadeIn } from '../ui/fade-in'
import { FeatureScreenshot } from '../mockups/feature-screenshot'
import { walkthroughSteps } from '../data/landing-content'

export function WalkthroughSection() {
  const [active, setActive] = useState(0)
  const step = walkthroughSteps[active]

  return (
    <section
      id="walkthrough"
      className="py-24 md:py-32 bg-landing-surface/50"
      aria-labelledby="walkthrough-heading"
    >
      <div className="mx-auto max-w-[1200px] px-4 sm:px-6">
        <SectionHeader
          eyebrow="Product walkthrough"
          title="From draft to paid in three steps"
          description="Invoice Flow keeps the workflow simple so you spend less time on paperwork."
          className="mb-12"
        />

        <div className="flex justify-center gap-2 mb-12">
          {walkthroughSteps.map((s, i) => (
            <button
              key={s.id}
              type="button"
              onClick={() => setActive(i)}
              className={cn(
                'px-5 py-2 rounded-full text-sm font-medium transition-all duration-200',
                active === i
                  ? 'bg-landing-accent text-white shadow-sm'
                  : 'text-landing-muted hover:text-landing-foreground hover:bg-accent/30'
              )}
              aria-pressed={active === i}
            >
              {s.label}
            </button>
          ))}
        </div>

        <FadeIn key={step.id}>
          <div className="grid lg:grid-cols-2 gap-10 lg:gap-16 items-center">
            <div>
              <h3
                id="walkthrough-heading"
                className="font-display text-2xl md:text-3xl font-semibold tracking-tight text-landing-foreground mb-4"
              >
                {step.title}
              </h3>
              <p className="text-landing-muted leading-relaxed text-lg">{step.description}</p>
            </div>
            <FeatureScreenshot
              label={step.screenshotLabel}
              src={step.screenshotSrc}
              alt={step.title}
            />
          </div>
        </FadeIn>
      </div>
    </section>
  )
}
