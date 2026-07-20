import { SectionHeader } from '../ui/section-header'
import { StaggerContainer, StaggerItem } from '../ui/fade-in'
import { testimonials } from '../data/landing-content'

export function TestimonialsSection() {
  return (
    <section className="py-24 md:py-32" aria-labelledby="testimonials-heading">
      <div className="mx-auto max-w-[1200px] px-4 sm:px-6">
        <SectionHeader
          eyebrow="Testimonials"
          title="Trusted by people who invoice for a living"
          className="mb-16"
        />

        <StaggerContainer className="grid md:grid-cols-3 gap-6">
          {testimonials.map((t) => (
            <StaggerItem key={t.name}>
              <blockquote className="landing-surface rounded-2xl p-6 h-full flex flex-col landing-card-hover">
                <p className="text-landing-foreground leading-relaxed flex-1">
                  &ldquo;{t.quote}&rdquo;
                </p>
                <footer className="mt-6 flex items-center gap-3 pt-6 border-t border-border/40">
                  <div
                    className="h-10 w-10 rounded-full bg-landing-accent/10 flex items-center justify-center text-sm font-semibold text-landing-accent"
                    aria-hidden="true"
                  >
                    {t.initials}
                  </div>
                  <div>
                    <p
                      id={t.name === testimonials[0].name ? 'testimonials-heading' : undefined}
                      className="text-sm font-medium text-landing-foreground"
                    >
                      {t.name}
                    </p>
                    <p className="text-xs text-landing-muted">
                      {t.role}, {t.company}
                    </p>
                  </div>
                </footer>
              </blockquote>
            </StaggerItem>
          ))}
        </StaggerContainer>
      </div>
    </section>
  )
}
