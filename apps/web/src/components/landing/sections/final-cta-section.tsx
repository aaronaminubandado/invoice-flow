import { Link } from 'react-router-dom'
import { ArrowRight } from 'lucide-react'
import { Button } from '@/components/ui'
import { FadeIn } from '../ui/fade-in'

export function FinalCtaSection() {
  return (
    <section className="py-24 md:py-32" aria-labelledby="final-cta-heading">
      <div className="mx-auto max-w-[1200px] px-4 sm:px-6">
        <FadeIn>
          <div className="relative rounded-3xl overflow-hidden px-8 py-16 md:px-16 md:py-20 text-center">
            <div
              className="absolute inset-0 landing-gradient-hero"
              aria-hidden="true"
            />
            <div
              className="absolute inset-0 bg-gradient-to-br from-landing-accent/5 via-transparent to-landing-accent-glow/10"
              aria-hidden="true"
            />

            <div className="relative">
              <h2
                id="final-cta-heading"
                className="font-display text-3xl md:text-4xl lg:text-5xl font-semibold tracking-tight text-landing-foreground leading-[1.1] max-w-2xl mx-auto"
              >
                Start sending invoices in minutes
              </h2>
              <p className="mt-4 text-lg text-landing-muted max-w-lg mx-auto">
                Join freelancers and agencies who stopped wrestling with spreadsheets and started getting paid on time.
              </p>
              <div className="mt-8 flex flex-col sm:flex-row items-center justify-center gap-3">
                <Link to="/register">
                  <Button size="lg" className="h-12 px-8 text-base gap-2">
                    Start free
                    <ArrowRight className="h-4 w-4" />
                  </Button>
                </Link>
                <Link
                  to="/login"
                  className="text-sm text-landing-muted hover:text-landing-foreground transition-colors px-4 py-2"
                >
                  Already have an account? Sign in
                </Link>
              </div>
            </div>
          </div>
        </FadeIn>
      </div>
    </section>
  )
}
