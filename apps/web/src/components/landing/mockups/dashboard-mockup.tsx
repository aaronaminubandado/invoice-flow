import { motion, useReducedMotion } from 'framer-motion'
import {
  DollarSign,
  TrendingUp,
  Clock,
  AlertCircle,
  CheckCircle2,
} from 'lucide-react'
import { cn } from '@/lib/utils'
import { mockInvoices, mockStats, mockChartData } from '../data/landing-content'
import { MiniChart } from './mini-chart'

const statusStyles = {
  paid: 'bg-emerald-500/10 text-emerald-600 dark:text-emerald-400',
  pending: 'bg-amber-500/10 text-amber-600 dark:text-amber-400',
  overdue: 'bg-red-500/10 text-red-600 dark:text-red-400',
}

const statIcons = [DollarSign, TrendingUp, Clock, AlertCircle]

export function DashboardMockup({ className }: { className?: string }) {
  const prefersReducedMotion = useReducedMotion()

  return (
    <div
      data-screenshot="dashboard"
      className={cn('relative', className)}
      aria-hidden="true"
    >
      <motion.div
        initial={prefersReducedMotion ? false : { opacity: 0, y: 32 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.7, delay: 0.2, ease: [0.16, 1, 0.3, 1] }}
        className="rounded-2xl landing-surface shadow-2xl shadow-black/10 dark:shadow-black/40 overflow-hidden border border-border/60"
      >
        {/* Window chrome */}
        <div className="flex items-center gap-2 px-4 py-3 border-b border-border/40 bg-landing-surface">
          <div className="flex gap-1.5">
            <div className="h-2.5 w-2.5 rounded-full bg-red-400/70" />
            <div className="h-2.5 w-2.5 rounded-full bg-amber-400/70" />
            <div className="h-2.5 w-2.5 rounded-full bg-emerald-400/70" />
          </div>
          <div className="flex-1 flex justify-center">
            <div className="h-5 w-48 rounded-md bg-muted/50 text-[10px] flex items-center justify-center text-muted-foreground font-mono">
              app.invoiceflow.io/dashboard
            </div>
          </div>
        </div>

        <div className="p-4 md:p-6 space-y-4 bg-background/50">
          {/* Stats row */}
          <div className="grid grid-cols-2 lg:grid-cols-4 gap-3">
            {mockStats.map((stat, i) => {
              const Icon = statIcons[i]
              return (
                <div
                  key={stat.label}
                  className="rounded-xl border border-border/50 bg-card p-3 md:p-4"
                >
                  <div className="flex items-center gap-2 mb-2">
                    <Icon className="h-3.5 w-3.5 text-primary" />
                    <span className="text-[10px] md:text-xs text-muted-foreground">{stat.label}</span>
                  </div>
                  <p className="text-lg md:text-xl font-semibold tabular-nums tracking-tight">
                    {stat.value}
                  </p>
                  <p
                    className={cn(
                      'text-[10px] md:text-xs mt-0.5',
                      stat.positive ? 'text-emerald-500' : 'text-amber-500'
                    )}
                  >
                    {stat.change}
                  </p>
                </div>
              )
            })}
          </div>

          <div className="grid lg:grid-cols-5 gap-4">
            {/* Chart */}
            <div className="lg:col-span-3 rounded-xl border border-border/50 bg-card p-4">
              <div className="flex items-center justify-between mb-3">
                <p className="text-sm font-medium">Monthly revenue</p>
                <span className="text-xs text-muted-foreground">Last 12 months</span>
              </div>
              <MiniChart data={mockChartData} height={120} width={400} />
            </div>

            {/* Client snippet */}
            <div className="lg:col-span-2 rounded-xl border border-border/50 bg-card p-4">
              <p className="text-sm font-medium mb-3">Recent clients</p>
              <div className="space-y-2">
                {['Northline Studio', 'Parcel & Co.', 'Meridian Labs'].map((client) => (
                  <div key={client} className="flex items-center gap-2.5">
                    <div className="h-7 w-7 rounded-full bg-primary/10 flex items-center justify-center text-[10px] font-medium text-primary">
                      {client.charAt(0)}
                    </div>
                    <span className="text-xs text-muted-foreground truncate">{client}</span>
                  </div>
                ))}
              </div>
            </div>
          </div>

          {/* Invoice table */}
          <div className="rounded-xl border border-border/50 bg-card overflow-hidden">
            <div className="px-4 py-3 border-b border-border/40">
              <p className="text-sm font-medium">Recent invoices</p>
            </div>
            <div className="divide-y divide-border/30">
              {mockInvoices.slice(0, 4).map((inv) => (
                <div
                  key={inv.id}
                  className="flex items-center justify-between px-4 py-2.5 text-xs"
                >
                  <div className="flex items-center gap-3 min-w-0">
                    <span className="font-mono text-muted-foreground">{inv.id}</span>
                    <span className="truncate text-foreground/80">{inv.client}</span>
                  </div>
                  <div className="flex items-center gap-3 shrink-0">
                    <span className="font-mono tabular-nums">
                      ${inv.amount.toLocaleString()}
                    </span>
                    <span
                      className={cn(
                        'px-2 py-0.5 rounded-full text-[10px] font-medium capitalize',
                        statusStyles[inv.status]
                      )}
                    >
                      {inv.status}
                    </span>
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>
      </motion.div>

      {/* Floating notification */}
      <motion.div
        initial={prefersReducedMotion ? false : { opacity: 0, x: 20, y: -10 }}
        animate={{ opacity: 1, x: 0, y: 0 }}
        transition={{ duration: 0.5, delay: 0.8, ease: [0.16, 1, 0.3, 1] }}
        className="absolute -right-2 md:-right-6 top-16 md:top-20 z-10"
      >
        <div className="flex items-center gap-2.5 rounded-xl border border-emerald-500/20 bg-card px-4 py-3 shadow-lg shadow-emerald-500/10">
          <CheckCircle2 className="h-5 w-5 text-emerald-500 shrink-0" />
          <div>
            <p className="text-xs font-medium">Payment received</p>
            <p className="text-sm font-semibold tabular-nums">$4,200.00</p>
          </div>
        </div>
      </motion.div>
    </div>
  )
}
