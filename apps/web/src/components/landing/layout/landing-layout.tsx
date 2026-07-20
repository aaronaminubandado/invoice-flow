import { LandingNav } from './landing-nav'
import { LandingFooter } from './landing-footer'

interface LandingLayoutProps {
  children: React.ReactNode
}

export function LandingLayout({ children }: LandingLayoutProps) {
  return (
    <div className="landing-page min-h-screen">
      <LandingNav />
      <main>{children}</main>
      <LandingFooter />
    </div>
  )
}
