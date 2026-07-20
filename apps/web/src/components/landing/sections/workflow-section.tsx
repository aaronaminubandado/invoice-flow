import { SectionHeader } from '../ui/section-header'
import { StaggerContainer, StaggerItem } from '../ui/fade-in'
import { workflowSteps } from '../data/landing-content'

export function WorkflowSection() {
  return (
    <section className="py-24 md:py-32" aria-labelledby="workflow-heading">
      <div className="mx-auto max-w-[1200px] px-4 sm:px-6">
        <SectionHeader
          eyebrow="How it works"
          title="Four steps to effortless invoicing"
          description="No complicated setup. Add a client, send an invoice, and track payments from day one."
          className="mb-16"
        />

        <StaggerContainer className="relative">
          <div
            className="hidden lg:block absolute top-12 left-[12.5%] right-[12.5%] h-px bg-gradient-to-r from-transparent via-landing-accent/30 to-transparent"
            aria-hidden="true"
          />

          <div className="grid sm:grid-cols-2 lg:grid-cols-4 gap-8 lg:gap-6">
            {workflowSteps.map((item) => {
              const Icon = item.icon
              return (
                <StaggerItem key={item.step}>
                  <div className="relative text-center lg:text-left">
                    <div className="inline-flex items-center justify-center h-12 w-12 rounded-2xl bg-landing-accent/10 mb-5 relative z-10">
                      <Icon className="h-5 w-5 text-landing-accent" aria-hidden="true" />
                      <span className="absolute -top-2 -right-2 h-6 w-6 rounded-full bg-landing-accent text-white text-xs font-semibold flex items-center justify-center">
                        {item.step}
                      </span>
                    </div>
                    <h3
                      id={item.step === 1 ? 'workflow-heading' : undefined}
                      className="font-display text-lg font-semibold text-landing-foreground mb-2"
                    >
                      {item.title}
                    </h3>
                    <p className="text-sm text-landing-muted leading-relaxed">
                      {item.description}
                    </p>
                  </div>
                </StaggerItem>
              )
            })}
          </div>
        </StaggerContainer>
      </div>
    </section>
  )
}
