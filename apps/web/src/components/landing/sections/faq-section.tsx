import { SectionHeader } from '../ui/section-header'
import { FadeIn } from '../ui/fade-in'
import { Accordion } from '@/components/ui/accordion'
import { faqItems } from '../data/landing-content'

export function FaqSection() {
  return (
    <section id="faq" className="py-24 md:py-32" aria-labelledby="faq-heading">
      <div className="mx-auto max-w-[1200px] px-4 sm:px-6">
        <div className="grid lg:grid-cols-5 gap-12 lg:gap-16">
          <div className="lg:col-span-2">
            <SectionHeader
              eyebrow="FAQ"
              title="Common questions"
              description="Everything you need to know before getting started."
              align="left"
            />
          </div>

          <FadeIn className="lg:col-span-3">
            <div id="faq-heading" className="landing-surface rounded-2xl px-6">
              <Accordion items={faqItems} />
            </div>
          </FadeIn>
        </div>
      </div>
    </section>
  )
}
