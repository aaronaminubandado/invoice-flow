export interface OnboardingStep {
  id: string
  label: string
  href: string
  done: boolean
}

export function buildOnboardingSteps(
  hasSettings: boolean,
  clientCount: number,
  invoiceCount: number
): OnboardingStep[] {
  return [
    {
      id: 'settings',
      label: 'Add your business details',
      href: '/settings',
      done: hasSettings,
    },
    {
      id: 'clients',
      label: 'Add your first client',
      href: '/clients',
      done: clientCount > 0,
    },
    {
      id: 'invoices',
      label: 'Send your first invoice',
      href: '/invoices',
      done: invoiceCount > 0,
    },
  ]
}

export function shouldShowOnboarding(steps: OnboardingStep[]): boolean {
  return steps.some((step) => !step.done)
}
