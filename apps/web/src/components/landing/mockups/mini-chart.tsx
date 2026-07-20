import { cn } from '@/lib/utils'

interface MiniChartProps {
  data: number[]
  className?: string
  animated?: boolean
  height?: number
  width?: number
}

export function MiniChart({
  data,
  className,
  animated = true,
  height = 80,
  width = 280,
}: MiniChartProps) {
  const max = Math.max(...data)
  const min = Math.min(...data)
  const range = max - min || 1
  const padding = 4

  const points = data.map((value, i) => {
    const x = padding + (i / (data.length - 1)) * (width - padding * 2)
    const y = padding + (1 - (value - min) / range) * (height - padding * 2)
    return `${x},${y}`
  })

  const linePath = `M ${points.join(' L ')}`
  const areaPath = `${linePath} L ${width - padding},${height - padding} L ${padding},${height - padding} Z`

  return (
    <svg
      viewBox={`0 0 ${width} ${height}`}
      className={cn('w-full h-auto', className)}
      aria-hidden="true"
    >
      <defs>
        <linearGradient id="chartGradient" x1="0" y1="0" x2="0" y2="1">
          <stop offset="0%" stopColor="var(--color-landing-accent-glow)" stopOpacity="0.3" />
          <stop offset="100%" stopColor="var(--color-landing-accent-glow)" stopOpacity="0" />
        </linearGradient>
      </defs>
      <path d={areaPath} fill="url(#chartGradient)" />
      <path
        d={linePath}
        fill="none"
        stroke="var(--color-landing-accent)"
        strokeWidth="2"
        strokeLinecap="round"
        strokeLinejoin="round"
        className={animated ? 'animate-chart-draw' : undefined}
        style={
          animated
            ? {
                strokeDasharray: 1000,
                strokeDashoffset: 0,
              }
            : undefined
        }
      />
    </svg>
  )
}
