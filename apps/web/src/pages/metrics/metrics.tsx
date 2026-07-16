import { useQuery } from '@tanstack/react-query'
import { motion } from 'framer-motion'
import {
  DollarSign,
  TrendingUp,
  Clock,
  PieChart,
} from 'lucide-react'
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  PieChart as RechartsPieChart,
  Pie,
  Cell,
  Legend,
} from 'recharts'
import {
  Card,
  CardContent,
  CardHeader,
  CardTitle,
  Skeleton,
  ExportDropdown,
} from '@/components/ui'
import { useToast } from '@/components/ui/toast'
import { metricsApi } from '@/services'
import type { ExportFormat } from '@/services/invoices'

const COLORS = ['#635bff', '#f59e0b', '#e5484d', '#30a46c']

const formatCurrency = (value: string | number) => {
  const num = typeof value === 'string' ? parseFloat(value) : value
  return new Intl.NumberFormat('en-US', {
    style: 'currency',
    currency: 'USD',
    minimumFractionDigits: 0,
    maximumFractionDigits: 0,
  }).format(num)
}

const FILE_EXTENSIONS: Record<ExportFormat, string> = {
  csv: '.csv',
  xlsx: '.xlsx',
  pdf: '.pdf',
}

function downloadBlob(blob: Blob, filename: string) {
  const url = window.URL.createObjectURL(blob)
  const a = document.createElement('a')
  a.href = url
  a.download = filename
  document.body.appendChild(a)
  a.click()
  window.URL.revokeObjectURL(url)
  document.body.removeChild(a)
}

export function MetricsPage() {
  const { success, error } = useToast()

  const { data: summary, isLoading: summaryLoading } = useQuery({
    queryKey: ['revenue-summary'],
    queryFn: metricsApi.getRevenueSummary,
  })

  const { data: monthly, isLoading: monthlyLoading } = useQuery({
    queryKey: ['monthly-revenue'],
    queryFn: metricsApi.getMonthlyRevenue,
  })

  const pieData = summary
    ? [
        { name: 'Paid', value: parseFloat(summary.total_paid) },
        { name: 'Outstanding', value: parseFloat(summary.total_outstanding) },
        { name: 'Overdue', value: parseFloat(summary.total_overdue) },
      ].filter((d) => d.value > 0)
    : []

  const handleExport = (fmt: ExportFormat) => {
    metricsApi
      .export(fmt)
      .then((blob) => {
        const date = new Date().toISOString().split('T')[0]
        downloadBlob(blob, `metrics_${date}${FILE_EXTENSIONS[fmt]}`)
        success('Metrics exported successfully')
      })
      .catch(() => error('Failed to export metrics'))
  }

  return (
    <div className="space-y-8 animate-fade-in">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-semibold tracking-tight">Metrics</h1>
          <p className="text-muted-foreground mt-1">
            Financial analytics and insights
          </p>
        </div>
        <ExportDropdown onExport={handleExport} />
      </div>

      <div className="grid gap-4 md:grid-cols-4">
        {[
          {
            label: 'Total Revenue',
            value: summary?.total_revenue,
            icon: DollarSign,
            color: 'text-primary',
            bg: 'bg-primary/10',
          },
          {
            label: 'Paid Revenue',
            value: summary?.total_paid,
            icon: TrendingUp,
            color: 'text-emerald-500',
            bg: 'bg-emerald-500/10',
          },
          {
            label: 'Outstanding',
            value: summary?.total_outstanding,
            icon: Clock,
            color: 'text-amber-500',
            bg: 'bg-amber-500/10',
          },
          {
            label: 'Overdue',
            value: summary?.total_overdue,
            icon: PieChart,
            color: 'text-destructive',
            bg: 'bg-destructive/10',
          },
        ].map((stat, index) => (
          <motion.div
            key={stat.label}
            initial={{ opacity: 0, y: 12 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: index * 0.08 }}
          >
            <Card>
              <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                <span className="text-sm font-medium text-muted-foreground">
                  {stat.label}
                </span>
                <div
                  className={`flex h-9 w-9 items-center justify-center rounded-lg ${stat.bg}`}
                >
                  <stat.icon className={`h-4 w-4 ${stat.color}`} />
                </div>
              </CardHeader>
              <CardContent>
                {summaryLoading ? (
                  <Skeleton className="h-9 w-24" />
                ) : (
                  <span className="text-2xl font-bold font-mono tabular-nums">
                    {stat.value ? formatCurrency(stat.value) : '$0'}
                  </span>
                )}
              </CardContent>
            </Card>
          </motion.div>
        ))}
      </div>

      <div className="grid gap-4 md:grid-cols-2">
        <motion.div
          initial={{ opacity: 0, y: 12 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.32 }}
        >
          <Card className="h-full">
            <CardHeader>
              <CardTitle>Monthly Revenue</CardTitle>
              <p className="text-sm text-muted-foreground">
                Paid vs outstanding by month
              </p>
            </CardHeader>
            <CardContent>
              {monthlyLoading ? (
                <Skeleton className="h-[350px] w-full rounded-lg" />
              ) : monthly && monthly.length > 0 ? (
                <ResponsiveContainer width="100%" height={350}>
                  <BarChart data={monthly}>
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
                        return (
                          <div className="rounded-lg border border-border bg-card px-4 py-3 shadow-lg">
                            <p className="text-sm font-medium mb-1.5">{label}</p>
                            {payload.map((entry, index) => (
                              <div
                                key={`entry-${index}`}
                                className="flex items-center justify-between gap-4 text-sm"
                              >
                                <span className="text-muted-foreground">
                                  {entry.name}
                                </span>
                                <span className="font-mono tabular-nums font-medium">
                                  {formatCurrency(entry.value as number)}
                                </span>
                              </div>
                            ))}
                          </div>
                        )
                      }}
                    />
                    <Bar
                      dataKey="paid"
                      fill="#635bff"
                      name="Paid"
                      radius={[4, 4, 0, 0]}
                    />
                    <Bar
                      dataKey="outstanding"
                      fill="#f59e0b"
                      name="Outstanding"
                      radius={[4, 4, 0, 0]}
                    />
                  </BarChart>
                </ResponsiveContainer>
              ) : (
                <div className="flex h-[350px] items-center justify-center rounded-lg border border-dashed border-border text-muted-foreground">
                  No data available
                </div>
              )}
            </CardContent>
          </Card>
        </motion.div>

        <motion.div
          initial={{ opacity: 0, y: 12 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.4 }}
        >
          <Card className="h-full">
            <CardHeader>
              <CardTitle>Revenue Distribution</CardTitle>
              <p className="text-sm text-muted-foreground">
                Breakdown by payment status
              </p>
            </CardHeader>
            <CardContent>
              {summaryLoading ? (
                <Skeleton className="h-[350px] w-full rounded-lg" />
              ) : pieData.length > 0 ? (
                <ResponsiveContainer width="100%" height={350}>
                  <RechartsPieChart>
                    <Pie
                      data={pieData}
                      cx="50%"
                      cy="50%"
                      innerRadius={70}
                      outerRadius={110}
                      paddingAngle={3}
                      dataKey="value"
                      strokeWidth={0}
                    >
                      {pieData.map((_entry, index) => (
                        <Cell
                          key={`cell-${index}`}
                          fill={COLORS[index % COLORS.length]}
                        />
                      ))}
                    </Pie>
                    <Tooltip
                      content={({ active, payload }) => {
                        if (!active || !payload?.length) return null
                        return (
                          <div className="rounded-lg border border-border bg-card px-4 py-3 shadow-lg">
                            <p className="text-sm font-medium mb-0.5">
                              {payload[0].name}
                            </p>
                            <p className="font-mono tabular-nums text-sm">
                              {formatCurrency(payload[0].value as number)}
                            </p>
                          </div>
                        )
                      }}
                    />
                    <Legend
                      wrapperStyle={{ fontSize: 13, paddingTop: 16 }}
                      formatter={(value) => (
                        <span className="text-foreground">{value}</span>
                      )}
                    />
                  </RechartsPieChart>
                </ResponsiveContainer>
              ) : (
                <div className="flex h-[350px] items-center justify-center rounded-lg border border-dashed border-border text-muted-foreground">
                  No data available
                </div>
              )}
            </CardContent>
          </Card>
        </motion.div>
      </div>

      <motion.div
        initial={{ opacity: 0, y: 12 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.48 }}
      >
        <Card>
          <CardHeader>
            <CardTitle>Performance Summary</CardTitle>
            <p className="text-sm text-muted-foreground">
              Key performance indicators
            </p>
          </CardHeader>
          <CardContent>
            {summaryLoading ? (
              <Skeleton className="h-32 w-full rounded-lg" />
            ) : (
              summary && (
                <div className="grid gap-4 md:grid-cols-3">
                  <div className="p-4 rounded-lg bg-emerald-500/5 border border-emerald-500/10">
                    <p className="text-sm text-emerald-500 font-medium mb-1">
                      Collection Rate
                    </p>
                    <p className="text-2xl font-bold font-mono tabular-nums">
                      {parseFloat(summary.total_revenue) > 0
                        ? `${Math.round(
                            (parseFloat(summary.total_paid) /
                              parseFloat(summary.total_revenue)) *
                              100
                          )}%`
                        : '0%'}
                    </p>
                  </div>
                  <div className="p-4 rounded-lg bg-amber-500/5 border border-amber-500/10">
                    <p className="text-sm text-amber-500 font-medium mb-1">
                      Outstanding Rate
                    </p>
                    <p className="text-2xl font-bold font-mono tabular-nums">
                      {parseFloat(summary.total_revenue) > 0
                        ? `${Math.round(
                            (parseFloat(summary.total_outstanding) /
                              parseFloat(summary.total_revenue)) *
                              100
                          )}%`
                        : '0%'}
                    </p>
                  </div>
                  <div className="p-4 rounded-lg bg-destructive/5 border border-destructive/10">
                    <p className="text-sm text-destructive font-medium mb-1">
                      Overdue Rate
                    </p>
                    <p className="text-2xl font-bold font-mono tabular-nums">
                      {parseFloat(summary.total_revenue) > 0
                        ? `${Math.round(
                            (parseFloat(summary.total_overdue) /
                              parseFloat(summary.total_revenue)) *
                              100
                          )}%`
                        : '0%'}
                    </p>
                  </div>
                </div>
              )
            )}
          </CardContent>
        </Card>
      </motion.div>
    </div>
  )
}
