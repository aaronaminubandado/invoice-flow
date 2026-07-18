import { describe, expect, it } from 'vitest'
import { buildOnboardingSteps, shouldShowOnboarding } from '@/lib/onboarding'

describe('onboarding', () => {
  it('marks steps done based on account state', () => {
    const steps = buildOnboardingSteps(true, 1, 0)
    expect(steps[0].done).toBe(true)
    expect(steps[1].done).toBe(true)
    expect(steps[2].done).toBe(false)
  })

  it('hides checklist when every step is complete', () => {
    const incomplete = buildOnboardingSteps(false, 0, 0)
    const complete = buildOnboardingSteps(true, 2, 3)

    expect(shouldShowOnboarding(incomplete)).toBe(true)
    expect(shouldShowOnboarding(complete)).toBe(false)
  })
})
