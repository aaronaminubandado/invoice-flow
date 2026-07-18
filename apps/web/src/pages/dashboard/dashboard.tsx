import { useQuery } from '@tanstack/react-query'
import { Link } from 'react-router-dom'
import {
  DollarSign,
  TrendingUp,
  Clock,
  AlertCircle,
  ArrowUpRight,
  ArrowDownRight,
  CheckCircle2,
  Circle,
} from 'lucide-react'
import {
  AreaChart,
  Area,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
} from 'recharts'
import { Card, CardContent, CardHeader, CardTitle, Skeleton } from '@/components/ui'
import { metricsApi, clientsApi, invoicesApi } from '@/services'
import { useSettings } from '@/hooks/useSettings'
import { formatCurrency } from '@/lib/utils'
import {
  buildOnboardingSteps,
  shouldShowOnboarding,
} from '@/lib/onboarding'

const statCards = [
  {
    label: 'Total Revenue',
    key: 'total_revenue',
    icon: DollarSign,
    dotColor: 'bg-primary',
    iconColor: 'text-primary',
  },
  {
    label: 'Total Paid',
    key: 'total_paid',
    icon: TrendingUp,
    dotColor: 'bg-emerald-500',
    iconColor: 'text-emerald-500',
  },
  {
    label: 'Outstanding',
    key: 'total_outstanding',
    icon: Clock,
    dotColor: 'bg-amber-500',
    iconColor: 'text-amber-500',
  },
  {
    label: 'Overdue',
    key: 'total_overdue',
    icon: AlertCircle,
    dotColor: 'bg-destructive',
    iconColor: 'text-destructive',
  },
]

export function DashboardPage() {
  const { data: summary, isLoading: summaryLoading } = useQuery({
    queryKey: ['revenue-summary'],
    queryFn: metricsApi.getRevenueSummary,
  })

  const { data: monthly, isLoading: monthlyLoading } = useQuery({
    queryKey: ['monthly-revenue'],
    queryFn: metricsApi.getMonthlyRevenue,
  })

  const { currency, hasSettings, isLoading: settingsLoading, isError: settingsMissing } =
    useSettings()

  const { data: clientsPage, isLoading: clientsLoading } = useQuery({
    queryKey: ['clients', 'count'],
    queryFn: () => clientsApi.list({ limit: 1, offset: 0 }),
  })

  const { data: invoicesPage, isLoading: invoicesLoading } = useQuery({
    queryKey: ['invoices', 'count'],
    queryFn: () => invoicesApi.list({ limit: 1, offset: 0 }),
  })

  const invoiceTotal = invoicesPage?.total ?? 0
  const clientTotal = clientsPage?.total ?? 0
  const onboardingSteps = buildOnboardingSteps(
    !settingsMissing && hasSettings,
    clientTotal,
    invoiceTotal
  )
  const onboardingReady =
    !summaryLoading && !settingsLoading && !clientsLoading && !invoicesLoading
  const showOnboarding = onboardingReady && shouldShowOnboarding(onboardingSteps)

  return (
    <div className="space-y-8 animate-fade-in">
      <div>
        <h1 className="text-2xl font-semibold tracking-tight">Dashboard</h1>
        <p className="text-muted-foreground mt-1">
          Revenue, collections, and what needs attention
        </p>
      </div>

      {showOnboarding && (
        <Card>
          <CardHeader>
            <CardTitle className="text-base">Get started with InvoiceFlow</CardTitle>
          </CardHeader>
          <CardContent className="space-y-3">
            {onboardingSteps.map((step) => (
              <Link
                key={step.id}
                to={step.href}
                className="flex items-center gap-3 rounded-lg border border-border px-4 py-3 hover:bg-accent/50 transition-colors"
              >
                {step.done ? (
                  <CheckCircle2 className="h-5 w-5 text-primary shrink-0" />
                ) : (
                  <Circle className="h-5 w-5 text-muted-foreground shrink-0" />
                )}
                <span className={step.done ? 'text-muted-foreground line-through' : ''}>
                  {step.label}
                </span>
              </Link>
            ))}
          </CardContent>
        </Card>
      )}

      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
        {statCards.map((stat) => (
          <div
            key={stat.key}
          >
            <Card>
              <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                <span className="text-sm font-medium text-muted-foreground">
                  {stat.label}
                </span>
                <div
                  className={`flex h-9 w-9 items-center justify-center rounded-lg ${stat.dotColor}/10`}
                >
                  <stat.icon className={`h-4 w-4 ${stat.iconColor}`} />
                </div>
              </CardHeader>
              <CardContent>
                {summaryLoading ? (
                  <Skeleton className="h-9 w-28" />
                ) : (
                  <span className="text-2xl font-bold font-mono tabular-nums">
                    {summary
                      ? formatCurrency(summary[stat.key as keyof typeof summary], currency)
                      : formatCurrency('0', currency)}
                  </span>
                )}
              </CardContent>
            </Card>
          </div>
        ))}
      </div>

      <div className="grid gap-4 md:grid-cols-2">
        <div>
          <Card>
            <CardHeader>
              <CardTitle>Revenue Overview</CardTitle>
              <p className="text-sm text-muted-foreground">
                Monthly paid and outstanding amounts
              </p>
            </CardHeader>
            <CardContent>
              {monthlyLoading ? (
                <Skeleton className="h-[320px] w-full rounded-lg" />
              ) : monthly && monthly.length > 0 ? (
                <ResponsiveContainer width="100%" height={320}>
                  <AreaChart data={monthly} margin={{ top: 8, right: 8, left: 0, bottom: 0 }}>
                    <defs>
                      <linearGradient id="colorPaid" x1="0" y1="0" x2="0" y2="1">
                        <stop offset="0%" stopColor="#0f766e" stopOpacity={0.4} />
                        <stop offset="100%" stopColor="#0f766e" stopOpacity={0} />
                      </linearGradient>
                      <linearGradient id="colorOutstanding" x1="0" y1="0" x2="0" y2="1">
                        <stop offset="0%" stopColor="#f59e0b" stopOpacity={0.3} />
                        <stop offset="100%" stopColor="#f59e0b" stopOpacity={0} />
                      </linearGradient>
                    </defs>
                    <CartesianGrid
                      strokeDasharray="3 3"
                      stroke="var(--color-border)"
                      vertical={false}
                    />
                    <XAxis
                      dataKey="month"
                      stroke="var(--color-muted-foreground)"
                      tick={{ fontSize: 12, fill: 'var(--color-muted-foreground)' }}
                      axisLine={false}
                      tickLine={false}
                      tickFormatter={(value) => {
                        const [year, month] = value.split('-')
                        return new Date(+year, +month - 1).toLocaleString(
                          'default',
                          { month: 'short' }
                        )
                      }}
                    />
                    <YAxis
                      stroke="var(--color-muted-foreground)"
                      tick={{ fontSize: 12, fill: 'var(--color-muted-foreground)' }}
                      axisLine={false}
                      tickLine={false}
                      tickFormatter={(value) => `$${value / 1000}k`}
                    />
                    <Tooltip
                      content={({ active, payload, label }) => {
                        if (!active || !payload?.length) return null
                        const [year, month] = (label as string).split('-')
                        const monthLabel = new Date(+year, +month - 1).toLocaleString(
                          'default',
                          { month: 'long', year: 'numeric' }
                        )
                        return (
                          <div className="rounded-lg border border-border bg-card px-4 py-3 shadow-lg">
                            <p className="text-sm font-medium text-foreground mb-2">
                              {monthLabel}
                            </p>
                            <div className="space-y-1">
                              {payload.map((entry, index) => (
                                <div
                                  key={`entry-${index}`}
                                  className="flex items-center justify-between gap-4 text-sm"
                                >
                                  <span className="text-muted-foreground">
                                    {entry.name}
                                  </span>
                                  <span className="font-mono tabular-nums font-medium">
                                    {formatCurrency(entry.value as string, currency)}
                                  </span>
                                </div>
                              ))}
                            </div>
                          </div>
                        )
                      }}
                    />
                    <Area
                      type="monotone"
                      dataKey="paid"
                      stroke="#0f766e"
                      strokeWidth={2}
                      fill="url(#colorPaid)"
                      name="Paid"
                    />
                    <Area
                      type="monotone"
                      dataKey="outstanding"
                      stroke="#f59e0b"
                      strokeWidth={2}
                      fill="url(#colorOutstanding)"
                      name="Outstanding"
                    />
                  </AreaChart>
                </ResponsiveContainer>
              ) : (
                <div className="flex h-[320px] items-center justify-center rounded-lg border border-dashed border-border text-muted-foreground">
                  No revenue data available
                </div>
              )}
            </CardContent>
          </Card>
        </div>

        <div>
          <Card>
            <CardHeader>
              <CardTitle>Quick Stats</CardTitle>
              <p className="text-sm text-muted-foreground">
                Key collection metrics at a glance
              </p>
            </CardHeader>
            <CardContent className="space-y-4">
              {summaryLoading ? (
                <>
                  <Skeleton className="h-20 w-full rounded-lg" />
                  <Skeleton className="h-20 w-full rounded-lg" />
                  <Skeleton className="h-20 w-full rounded-lg" />
                </>
              ) : (
                summary && (
                  <>
                    <div className="flex items-center gap-4 rounded-lg bg-emerald-500/5 p-4 border border-emerald-500/10">
                      <div className="flex h-10 w-10 shrink-0 items-center justify-center rounded-lg bg-emerald-500/15">
                        <ArrowUpRight className="h-5 w-5 text-emerald-500" />
                      </div>
                      <div className="min-w-0 flex-1">
                        <p className="text-sm text-muted-foreground">
                          Collection Rate
                        </p>
                        <p className="text-xl font-semibold font-mono tabular-nums">
                          {parseFloat(summary.total_revenue) > 0
                            ? `${Math.round(
                                (parseFloat(summary.total_paid) /
                                  parseFloat(summary.total_revenue)) *
                                  100
                              )}%`
                            : '0%'}
                        </p>
                      </div>
                    </div>

                    <div className="flex items-center gap-4 rounded-lg bg-amber-500/5 p-4 border border-amber-500/10">
                      <div className="flex h-10 w-10 shrink-0 items-center justify-center rounded-lg bg-amber-500/15">
                        <Clock className="h-5 w-5 text-amber-500" />
                      </div>
                      <div className="min-w-0 flex-1">
                        <p className="text-sm text-muted-foreground">
                          Pending Amount
                        </p>
                        <p className="text-xl font-semibold font-mono tabular-nums">
                          {formatCurrency(summary.total_outstanding, currency)}
                        </p>
                      </div>
                    </div>

                    <div className="flex items-center gap-4 rounded-lg bg-destructive/5 p-4 border border-destructive/10">
                      <div className="flex h-10 w-10 shrink-0 items-center justify-center rounded-lg bg-destructive/15">
                        <ArrowDownRight className="h-5 w-5 text-destructive" />
                      </div>
                      <div className="min-w-0 flex-1">
                        <p className="text-sm text-muted-foreground">
                          Overdue Amount
                        </p>
                        <p className="text-xl font-semibold font-mono tabular-nums">
                          {formatCurrency(summary.total_overdue, currency)}
                        </p>
                      </div>
                    </div>
                  </>
                )
              )}
            </CardContent>
          </Card>
        </div>
      </div>
    </div>
  )
}
