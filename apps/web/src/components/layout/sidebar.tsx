import { Link, useLocation } from 'react-router-dom'
import { motion } from 'framer-motion'
import {
  LayoutDashboard,
  Receipt,
  Users,
  BarChart3,
  Settings,
  LogOut,
  FileText,
  Sun,
  Moon,
} from 'lucide-react'
import { cn } from '@/lib/utils'
import { useTheme } from '@/contexts/theme'

const navItems = [
  { path: '/dashboard', label: 'Dashboard', icon: LayoutDashboard },
  { path: '/invoices', label: 'Invoices', icon: Receipt },
  { path: '/clients', label: 'Clients', icon: Users },
  { path: '/metrics', label: 'Metrics', icon: BarChart3 },
]

interface SidebarProps {
  collapsed?: boolean
  onCollapse?: (collapsed: boolean) => void
}

import { supabase } from '@/lib/supabase'

export function Sidebar({ collapsed = false }: SidebarProps) {
  const location = useLocation()
  const { theme, toggleTheme } = useTheme()

  const handleLogout = async () => {
    await supabase.auth.signOut()
    window.location.href = '/login'
  }

  return (
    <motion.aside
      initial={false}
      animate={{ width: collapsed ? 68 : 240 }}
      className="fixed left-0 top-0 z-40 h-screen border-r border-border bg-card/50 backdrop-blur-xl"
    >
      <div className="flex h-full flex-col">
        <div
          className={cn(
            'flex items-center border-b border-border h-16 px-4',
            collapsed ? 'justify-center' : 'gap-2.5'
          )}
        >
          <div className="flex h-8 w-8 shrink-0 items-center justify-center rounded-lg bg-primary/10 border border-primary/50">
            <FileText className="h-4 w-4 text-primary" />
          </div>
          {!collapsed && (
            <motion.span
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              className="text-[15px] font-semibold tracking-tight"
            >
              InvoiceFlow
            </motion.span>
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
                className={cn(
                  'group relative flex items-center gap-2.5 rounded-lg px-3 py-2 text-[13px] font-medium transition-all duration-150',
                  isActive
                    ? 'bg-primary/10 text-primary'
                    : 'text-muted-foreground hover:bg-accent hover:text-foreground',
                  collapsed && 'justify-center px-0'
                )}
              >
                {isActive && (
                  <motion.div
                    layoutId="sidebar-active"
                    className="absolute left-0 top-1/2 -translate-y-1/2 h-5 w-[3px] rounded-r-full bg-primary"
                    transition={{ type: 'spring', stiffness: 350, damping: 30 }}
                  />
                )}
                <Icon
                  className={cn(
                    'h-[18px] w-[18px] shrink-0',
                    isActive ? 'text-primary' : 'text-muted-foreground group-hover:text-foreground'
                  )}
                />
                {!collapsed && <span>{item.label}</span>}
              </Link>
            )
          })}
        </nav>

        <div className="border-t border-border px-2 py-3 space-y-0.5">
          <button
            onClick={toggleTheme}
            className={cn(
              'flex w-full items-center gap-2.5 rounded-lg px-3 py-2 text-[13px] font-medium text-muted-foreground transition-colors hover:bg-accent hover:text-foreground',
              collapsed && 'justify-center px-0'
            )}
          >
            {theme === 'dark' ? (
              <Sun className="h-[18px] w-[18px] shrink-0" />
            ) : (
              <Moon className="h-[18px] w-[18px] shrink-0" />
            )}
            {!collapsed && (
              <span>{theme === 'dark' ? 'Light Mode' : 'Dark Mode'}</span>
            )}
          </button>

          <Link
            to="/settings"
            className={cn(
              'flex items-center gap-2.5 rounded-lg px-3 py-2 text-[13px] font-medium text-muted-foreground transition-colors hover:bg-accent hover:text-foreground',
              location.pathname === '/settings' && 'bg-primary/10 text-primary',
              collapsed && 'justify-center px-0'
            )}
          >
            <Settings className="h-[18px] w-[18px] shrink-0" />
            {!collapsed && <span>Settings</span>}
          </Link>

          <button
            onClick={handleLogout}
            className={cn(
              'flex w-full items-center gap-2.5 rounded-lg px-3 py-2 text-[13px] font-medium text-muted-foreground transition-colors hover:bg-destructive/10 hover:text-destructive',
              collapsed && 'justify-center px-0'
            )}
          >
            <LogOut className="h-[18px] w-[18px] shrink-0" />
            {!collapsed && <span>Logout</span>}
          </button>
        </div>
      </div>
    </motion.aside>
  )
}
