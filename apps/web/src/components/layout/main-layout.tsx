import { Outlet } from 'react-router-dom'
import { useEffect, useState } from 'react'
import { Menu } from 'lucide-react'
import { Sidebar } from './sidebar'
import { Button } from '@/components/ui'
import { LogoMark } from '@/components/brand/logo-mark'
import { cn } from '@/lib/utils'

export function MainLayout() {
  const [collapsed, setCollapsed] = useState(false)
  const [mobileOpen, setMobileOpen] = useState(false)
  const [isDesktop, setIsDesktop] = useState(
    () => typeof window !== 'undefined' && window.matchMedia('(min-width: 1024px)').matches
  )

  useEffect(() => {
    const media = window.matchMedia('(min-width: 1024px)')
    const handler = (event: MediaQueryListEvent) => {
      setIsDesktop(event.matches)
      if (event.matches) setMobileOpen(false)
    }
    media.addEventListener('change', handler)
    return () => media.removeEventListener('change', handler)
  }, [])

  return (
    <div className="min-h-screen bg-background">
      <header className="lg:hidden fixed top-0 inset-x-0 z-50 flex h-14 items-center gap-3 border-b border-border bg-card/95 px-4 backdrop-blur">
        <Button
          variant="ghost"
          size="icon"
          aria-label="Open menu"
          onClick={() => setMobileOpen(true)}
        >
          <Menu className="h-5 w-5" />
        </Button>
        <LogoMark className="h-8 w-8" />
        <span className="font-semibold tracking-tight">InvoiceFlow</span>
      </header>

      <Sidebar
        collapsed={collapsed}
        onCollapse={setCollapsed}
        mobileOpen={mobileOpen}
        onMobileClose={() => setMobileOpen(false)}
        isDesktop={isDesktop}
      />

      <main
        className={cn(
          'min-h-screen transition-all duration-200 pt-14 lg:pt-0',
          isDesktop ? (collapsed ? 'lg:ml-[68px]' : 'lg:ml-[240px]') : 'ml-0'
        )}
      >
        <div className="mx-auto max-w-[1400px] px-4 py-6 sm:px-6 lg:px-10 lg:py-8">
          <Outlet />
        </div>
      </main>
    </div>
  )
}
