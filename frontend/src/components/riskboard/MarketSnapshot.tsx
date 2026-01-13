import { useQuery } from '@tanstack/react-query'
import { motion } from 'framer-motion'
import { marketApi } from '../../services/api'

interface SparklineProps {
  data: number[]
  direction: 'up' | 'down' | 'flat'
}

function Sparkline({ data, direction }: SparklineProps) {
  if (!data || data.length < 2) return null

  const min = Math.min(...data)
  const max = Math.max(...data)
  const range = max - min || 1

  const width = 60
  const height = 20
  const points = data
    .map((value, i) => {
      const x = (i / (data.length - 1)) * width
      const y = height - ((value - min) / range) * height
      return `${x},${y}`
    })
    .join(' ')

  const colorClass =
    direction === 'up'
      ? 'text-emerald-400'
      : direction === 'down'
      ? 'text-rose-400'
      : 'text-slate-500'

  return (
    <svg width={width} height={height} className={colorClass}>
      <polyline
        points={points}
        fill="none"
        stroke="currentColor"
        strokeWidth="1.5"
        strokeLinecap="round"
        strokeLinejoin="round"
      />
    </svg>
  )
}

export default function MarketSnapshot() {
  const { data: snapshot, isLoading } = useQuery({
    queryKey: ['marketSnapshot'],
    queryFn: () => marketApi.getSnapshot(),
    refetchInterval: 60000, // Refresh every minute
  })

  if (isLoading) {
    return (
      <div className="flex items-center gap-4">
        {[1, 2, 3, 4].map((i) => (
          <div key={i} className="glass px-4 py-2 w-32 animate-pulse">
            <div className="h-3 bg-slate-700 rounded w-16 mb-2" />
            <div className="h-4 bg-slate-700 rounded w-20" />
          </div>
        ))}
      </div>
    )
  }

  return (
    <motion.div
      initial={{ opacity: 0, y: -10 }}
      animate={{ opacity: 1, y: 0 }}
      className="flex items-center gap-3 flex-wrap"
    >
      {snapshot?.indices.map((index, i) => (
        <motion.div
          key={index.symbol}
          initial={{ opacity: 0, y: -10 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: i * 0.05 }}
          className="glass px-4 py-2 flex items-center gap-3"
        >
          <div className="flex-1">
            <div className="flex items-center gap-2">
              <span className="text-xs text-slate-500 uppercase tracking-wider">
                {index.symbol}
              </span>
              {index.change_direction === 'up' && (
                <svg className="w-3 h-3 text-emerald-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 10l7-7m0 0l7 7m-7-7v18" />
                </svg>
              )}
              {index.change_direction === 'down' && (
                <svg className="w-3 h-3 text-rose-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 14l-7 7m0 0l-7-7m7 7V3" />
                </svg>
              )}
            </div>
            <div className="flex items-baseline gap-2">
              <span className="text-sm font-mono font-medium text-slate-100">
                {index.formatted_value}
              </span>
              <span
                className={`text-xs font-mono ${
                  index.change_direction === 'up'
                    ? 'text-emerald-400'
                    : index.change_direction === 'down'
                    ? 'text-rose-400'
                    : 'text-slate-500'
                }`}
              >
                {index.change_pct > 0 ? '+' : ''}
                {index.change_pct.toFixed(2)}%
              </span>
            </div>
          </div>
          <Sparkline data={index.sparkline} direction={index.change_direction} />
        </motion.div>
      ))}
    </motion.div>
  )
}
