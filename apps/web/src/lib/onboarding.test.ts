import { describe, expect, it } from 'vitest'
import { buildOnboardingSteps, shouldShowOnboarding } from '@/lib/onboarding'

describe('onboarding', () => {
  it('marks steps done based on account state', () => {
    const steps = buildOnboardingSteps(true, 1, 0)
    expect(steps[0].done).toBe(true)
    expect(steps[1].done).toBe(true)
    expect(steps[2].done).toBe(false)
  })

  it('hides checklist when invoices exist', () => {
    expect(shouldShowOnboarding(0)).toBe(true)
    expect(shouldShowOnboarding(3)).toBe(false)
  })
})
