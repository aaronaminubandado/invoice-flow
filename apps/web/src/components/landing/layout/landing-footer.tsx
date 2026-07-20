import { Link } from 'react-router-dom'
import { LogoMark } from '@/components/brand/logo-mark'
import { footerLinks } from '../data/landing-content'

export function LandingFooter() {
  const scrollTo = (href: string) => {
    if (href.startsWith('#')) {
      document.querySelector(href)?.scrollIntoView({ behavior: 'smooth' })
    }
  }

  return (
    <footer className="border-t border-border/40 bg-landing-surface">
      <div className="mx-auto max-w-[1200px] px-4 sm:px-6 py-16">
        <div className="grid grid-cols-2 md:grid-cols-4 gap-8 md:gap-12">
          <div className="col-span-2 md:col-span-1">
            <Link to="/" className="flex items-center gap-2.5 mb-4">
              <LogoMark className="h-8 w-8" />
              <span className="font-display text-lg font-semibold tracking-tight">
                Invoice Flow
              </span>
            </Link>
            <p className="text-sm text-landing-muted leading-relaxed max-w-xs">
              Invoicing software that helps freelancers and agencies get paid without the admin overhead.
            </p>
          </div>

          <div>
            <h3 className="text-sm font-semibold text-landing-foreground mb-4">Product</h3>
            <ul className="space-y-2.5">
              {footerLinks.product.map((link) => (
                <li key={link.label}>
                  <button
                    type="button"
                    onClick={() => scrollTo(link.href)}
                    className="text-sm text-landing-muted hover:text-landing-foreground transition-colors"
                  >
                    {link.label}
                  </button>
                </li>
              ))}
            </ul>
          </div>

          <div>
            <h3 className="text-sm font-semibold text-landing-foreground mb-4">Company</h3>
            <ul className="space-y-2.5">
              {footerLinks.company.map((link) => (
                <li key={link.label}>
                  <a
                    href={link.href}
                    className="text-sm text-landing-muted hover:text-landing-foreground transition-colors"
                  >
                    {link.label}
                  </a>
                </li>
              ))}
            </ul>
          </div>

          <div>
            <h3 className="text-sm font-semibold text-landing-foreground mb-4">Legal</h3>
            <ul className="space-y-2.5">
              {footerLinks.legal.map((link) => (
                <li key={link.label}>
                  <a
                    href={link.href}
                    className="text-sm text-landing-muted hover:text-landing-foreground transition-colors"
                  >
                    {link.label}
                  </a>
                </li>
              ))}
            </ul>
          </div>
        </div>

        <div className="mt-12 pt-8 border-t border-border/40 flex flex-col sm:flex-row items-center justify-between gap-4">
          <p className="text-sm text-landing-muted">
            &copy; {new Date().getFullYear()} Invoice Flow. All rights reserved.
          </p>
          <p className="text-xs text-landing-muted/70">
            Built for freelancers, agencies, and growing businesses.
          </p>
        </div>
      </div>
    </footer>
  )
}
