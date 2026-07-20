import { FadeIn } from '../ui/fade-in'
import { logoCompanies } from '../data/landing-content'

export function LogosSection() {
  return (
    <section className="py-12 md:py-16 border-y border-border/30" aria-label="Trusted by">
      <div className="mx-auto max-w-[1200px] px-4 sm:px-6">
        <FadeIn>
          <p className="text-center text-sm text-landing-muted mb-8">
            Used by freelancers and agencies worldwide
          </p>
        </FadeIn>
        <FadeIn delay={0.1}>
          <div className="flex flex-wrap items-center justify-center gap-x-10 gap-y-4">
            {logoCompanies.map((company) => (
              <span
                key={company}
                className="text-sm md:text-base font-medium text-landing-muted/60 hover:text-landing-muted transition-colors"
              >
                {company}
              </span>
            ))}
          </div>
        </FadeIn>
      </div>
    </section>
  )
}
