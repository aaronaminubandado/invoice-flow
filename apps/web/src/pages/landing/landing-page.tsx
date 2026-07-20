import { LandingLayout } from '@/components/landing/layout/landing-layout'
import { HeroSection } from '@/components/landing/sections/hero-section'
import { LogosSection } from '@/components/landing/sections/logos-section'
import { FeaturesSection } from '@/components/landing/sections/features-section'
import { WalkthroughSection } from '@/components/landing/sections/walkthrough-section'
import { WorkflowSection } from '@/components/landing/sections/workflow-section'
import { BenefitsSection } from '@/components/landing/sections/benefits-section'
import { TestimonialsSection } from '@/components/landing/sections/testimonials-section'
import { PricingSection } from '@/components/landing/sections/pricing-section'
import { FaqSection } from '@/components/landing/sections/faq-section'
import { FinalCtaSection } from '@/components/landing/sections/final-cta-section'

export function LandingPage() {
  return (
    <LandingLayout>
      <HeroSection />
      <LogosSection />
      <FeaturesSection />
      <WalkthroughSection />
      <WorkflowSection />
      <BenefitsSection />
      <TestimonialsSection />
      <PricingSection />
      <FaqSection />
      <FinalCtaSection />
    </LandingLayout>
  )
}
