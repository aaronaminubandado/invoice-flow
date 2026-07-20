import { Link } from 'react-router-dom'
import { ArrowRight } from 'lucide-react'
import { Button } from '@/components/ui'
import { FadeIn } from '../ui/fade-in'
import { DashboardMockup } from '../mockups/dashboard-mockup'
import { heroContent } from '../data/landing-content'

function scrollToWalkthrough() {
  document.querySelector('#walkthrough')?.scrollIntoView({ behavior: 'smooth' })
}

export function HeroSection() {
  return (
    <section className="landing-gradient-hero pt-32 pb-20 md:pt-40 md:pb-28">
      <div className="mx-auto max-w-[1200px] px-4 sm:px-6">
        <div className="grid lg:grid-cols-2 gap-12 lg:gap-16 items-center">
          <div>
            <FadeIn>
              <p className="text-sm font-medium text-landing-accent mb-4 tracking-wide">
                {heroContent.eyebrow}
              </p>
            </FadeIn>

            <FadeIn delay={0.1}>
              <h1 className="font-display text-4xl sm:text-5xl lg:text-[3.5rem] font-semibold tracking-tight text-landing-foreground leading-[1.08]">
                {heroContent.headline}
              </h1>
            </FadeIn>

            <FadeIn delay={0.2}>
              <p className="mt-6 text-lg text-landing-muted leading-relaxed max-w-lg">
                {heroContent.subhead}
              </p>
            </FadeIn>

            <FadeIn delay={0.3}>
              <div className="mt-8 flex flex-col sm:flex-row gap-3">
                <Link to="/register">
                  <Button size="lg" className="w-full sm:w-auto gap-2 h-12 px-6 text-base">
                    {heroContent.primaryCta}
                    <ArrowRight className="h-4 w-4" />
                  </Button>
                </Link>
                <Button
                  size="lg"
                  variant="outline"
                  className="w-full sm:w-auto h-12 px-6 text-base"
                  onClick={scrollToWalkthrough}
                >
                  {heroContent.secondaryCta}
                </Button>
              </div>
            </FadeIn>

            <FadeIn delay={0.4}>
              <p className="mt-6 text-sm text-landing-muted">{heroContent.trustLine}</p>
              <div className="mt-6 flex flex-wrap gap-3">
                {heroContent.stats.map((stat) => (
                  <div
                    key={stat.label}
                    className="rounded-full border border-border/50 bg-landing-surface/60 px-4 py-1.5 text-xs"
                  >
                    <span className="font-semibold text-landing-foreground tabular-nums">
                      {stat.value}
                    </span>{' '}
                    <span className="text-landing-muted">{stat.label}</span>
                  </div>
                ))}
              </div>
            </FadeIn>
          </div>

          <FadeIn delay={0.3} direction="none" className="relative">
            <DashboardMockup />
          </FadeIn>
        </div>
      </div>
    </section>
  )
}
