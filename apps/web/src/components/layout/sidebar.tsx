import { Link, useLocation } from 'react-router-dom'
import { motion, AnimatePresence } from 'framer-motion'
import {
  LayoutDashboard,
  Receipt,
  Users,
  Package,
  BarChart3,
  Settings,
  LogOut,
  Sun,
  Moon,
  PanelLeftClose,
  PanelLeftOpen,
  X,
} from 'lucide-react'
import { cn } from '@/lib/utils'
import { useTheme } from '@/hooks/useTheme'
import { supabase } from '@/lib/supabase'
import { LogoMark } from '@/components/brand/logo-mark'
import { Button } from '@/components/ui'

const navItems = [
  { path: '/dashboard', label: 'Dashboard', icon: LayoutDashboard },
  { path: '/invoices', label: 'Invoices', icon: Receipt },
  { path: '/clients', label: 'Clients', icon: Users },
  { path: '/products', label: 'Products', icon: Package },
  { path: '/metrics', label: 'Metrics', icon: BarChart3 },
]

interface SidebarProps {
  collapsed?: boolean
  onCollapse?: (collapsed: boolean) => void
  mobileOpen?: boolean
  onMobileClose?: () => void
  isDesktop?: boolean
}

export function Sidebar({
  collapsed = false,
  onCollapse,
  mobileOpen = false,
  onMobileClose,
  isDesktop = true,
}: SidebarProps) {
  const location = useLocation()
  const { theme, toggleTheme } = useTheme()

  const handleLogout = async () => {
    await supabase.auth.signOut()
    window.location.href = '/login'
  }

  const showExpanded = isDesktop ? !collapsed : true

  return (
    <>
      <AnimatePresence>
        {!isDesktop && mobileOpen && (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            className="fixed inset-0 z-40 bg-black/50 lg:hidden"
            onClick={onMobileClose}
          />
        )}
      </AnimatePresence>

      <motion.aside
        initial={false}
        animate={{
          width: isDesktop ? (collapsed ? 68 : 240) : 280,
          x: isDesktop || mobileOpen ? 0 : -280,
        }}
        transition={{ type: 'spring', stiffness: 320, damping: 32 }}
        className={cn(
          'fixed left-0 top-0 z-50 h-screen border-r border-border bg-card/95 backdrop-blur-xl',
          !isDesktop && 'shadow-2xl'
        )}
      >
        <div className="flex h-full flex-col">
          <div
            className={cn(
              'flex items-center border-b border-border h-16 px-4',
              showExpanded ? 'justify-between' : 'justify-center'
            )}
          >
            {showExpanded && (
              <div className="flex items-center gap-2.5">
                <LogoMark className="h-8 w-8 shrink-0" />
                <span className="text-[15px] font-semibold tracking-tight">
                  InvoiceFlow
                </span>
              </div>
            )}
            {!isDesktop && (
              <Button variant="ghost" size="icon" onClick={onMobileClose} aria-label="Close menu">
                <X className="h-4 w-4" />
              </Button>
            )}
            {isDesktop && onCollapse && (
              <Button
                variant="ghost"
                size="icon"
                onClick={() => onCollapse(!collapsed)}
                aria-label={collapsed ? 'Expand sidebar' : 'Collapse sidebar'}
              >
                {collapsed ? (
                  <PanelLeftOpen className="h-4 w-4" />
                ) : (
                  <PanelLeftClose className="h-4 w-4" />
                )}
              </Button>
            )}
          </div>

          <nav className="flex-1 space-y-0.5 px-2 py-3">
            {navItems.map((item) => {
              const isActive = location.pathname.startsWith(item.path)
              const Icon = item.icon

              return (
                <Link
                  key={item.path}
                  to={item.path}
                  onClick={onMobileClose}
                  className={cn(
                    'group relative flex items-center gap-2.5 rounded-lg px-3 py-2 text-[13px] font-medium transition-all duration-150',
                    isActive
                      ? 'bg-primary/10 text-primary'
                      : 'text-muted-foreground hover:bg-accent hover:text-foreground',
                    !showExpanded && 'justify-center px-0'
                  )}
                >
                  {isActive && (
                    <div className="absolute left-0 top-1/2 -translate-y-1/2 h-5 w-[3px] rounded-r-full bg-primary" />
                  )}
                  <Icon
                    className={cn(
                      'h-[18px] w-[18px] shrink-0',
                      isActive ? 'text-primary' : 'text-muted-foreground group-hover:text-foreground'
                    )}
                  />
                  {showExpanded && <span>{item.label}</span>}
                </Link>
              )
            })}
          </nav>

          <div className="border-t border-border px-2 py-3 space-y-0.5">
            <button
              onClick={toggleTheme}
              className={cn(
                'flex w-full items-center gap-2.5 rounded-lg px-3 py-2 text-[13px] font-medium text-muted-foreground transition-colors hover:bg-accent hover:text-foreground',
                !showExpanded && 'justify-center px-0'
              )}
            >
              {theme === 'dark' ? (
                <Sun className="h-[18px] w-[18px] shrink-0" />
              ) : (
                <Moon className="h-[18px] w-[18px] shrink-0" />
              )}
              {showExpanded && (
                <span>{theme === 'dark' ? 'Light Mode' : 'Dark Mode'}</span>
              )}
            </button>

            <Link
              to="/settings"
              onClick={onMobileClose}
              className={cn(
                'flex items-center gap-2.5 rounded-lg px-3 py-2 text-[13px] font-medium text-muted-foreground transition-colors hover:bg-accent hover:text-foreground',
                location.pathname === '/settings' && 'bg-primary/10 text-primary',
                !showExpanded && 'justify-center px-0'
              )}
            >
              <Settings className="h-[18px] w-[18px] shrink-0" />
              {showExpanded && <span>Settings</span>}
            </Link>

            <button
              onClick={handleLogout}
              className={cn(
                'flex w-full items-center gap-2.5 rounded-lg px-3 py-2 text-[13px] font-medium text-muted-foreground transition-colors hover:bg-destructive/10 hover:text-destructive',
                !showExpanded && 'justify-center px-0'
              )}
            >
              <LogOut className="h-[18px] w-[18px] shrink-0" />
              {showExpanded && <span>Logout</span>}
            </button>
          </div>
        </div>
      </motion.aside>
    </>
  )
}
