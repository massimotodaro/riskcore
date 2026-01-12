import { useQuery } from '@tanstack/react-query'
import { motion } from 'framer-motion'
import { correlationApi, formatCorrelation } from '../../services/api'

// Get color for correlation value - dark theme optimized
function getCorrelationColor(value: number): string {
  if (value >= 0.7) return 'bg-rose-500/80'
  if (value >= 0.4) return 'bg-rose-500/50'
  if (value >= 0.2) return 'bg-rose-500/30'
  if (value > -0.2) return 'bg-slate-700/50'
  if (value > -0.4) return 'bg-blue-500/30'
  if (value > -0.7) return 'bg-blue-500/50'
  return 'bg-blue-500/80'
}

function getTextColor(value: number): string {
  if (Math.abs(value) >= 0.4) return 'text-white'
  return 'text-slate-300'
}

const containerVariants = {
  hidden: { opacity: 0 },
  visible: {
    opacity: 1,
    transition: { staggerChildren: 0.02 },
  },
}

const cellVariants = {
  hidden: { opacity: 0, scale: 0.8 },
  visible: { opacity: 1, scale: 1 },
}

export default function CorrelationHeatmap() {
  const { data: matrix, isLoading, error } = useQuery({
    queryKey: ['correlationMatrix'],
    queryFn: () => correlationApi.getMatrix(undefined, '21d'),
  })

  const { data: concerns } = useQuery({
    queryKey: ['correlationConcerns'],
    queryFn: () => correlationApi.getConcerns(),
  })

  if (isLoading) {
    return (
      <div className="glass p-6">
        <h3 className="section-title mb-4">PM Correlation Matrix</h3>
        <div className="animate-pulse">
          <div className="h-64 bg-white/5 rounded-xl"></div>
        </div>
      </div>
    )
  }

  if (error || !matrix) {
    return (
      <div className="glass p-6">
        <h3 className="section-title mb-4">PM Correlation Matrix</h3>
        <div className="text-slate-500 text-center py-8">
          Unable to load correlation data. Make sure the backend is running and has return history.
        </div>
      </div>
    )
  }

  // Extract first names for cleaner display
  const pmLabels = matrix.pm_names.map((name) => name.split(' ')[0])

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.4 }}
      className="glass p-6"
    >
      <div className="flex items-center justify-between mb-6">
        <div>
          <h3 className="section-title">PM Correlation Matrix</h3>
          <p className="section-subtitle mt-1">{matrix.window_days}-day realized correlation</p>
        </div>
        {concerns && concerns.length > 0 && (
          <span className="badge badge-red">
            {concerns.length} high correlation pair{concerns.length > 1 ? 's' : ''}
          </span>
        )}
      </div>

      {/* Heatmap grid */}
      <div className="overflow-x-auto">
        <div className="inline-block min-w-full">
          {/* Header row */}
          <div className="flex">
            <div className="w-16 shrink-0"></div>
            {pmLabels.map((label, i) => (
              <div
                key={i}
                className="w-12 h-8 flex items-center justify-center text-xs font-medium text-slate-400 transform -rotate-45 origin-left translate-x-3"
              >
                {label}
              </div>
            ))}
          </div>

          {/* Data rows */}
          <motion.div
            variants={containerVariants}
            initial="hidden"
            animate="visible"
          >
            {matrix.matrix.map((row, i) => (
              <div key={i} className="flex items-center">
                <div className="w-16 shrink-0 text-xs font-medium text-slate-400 pr-2 text-right">
                  {pmLabels[i]}
                </div>
                {row.map((value, j) => (
                  <motion.div
                    key={j}
                    variants={cellVariants}
                    className={`
                      w-12 h-10 flex items-center justify-center text-xs font-mono font-medium
                      heatmap-cell ${getCorrelationColor(value)} ${getTextColor(value)}
                      ${i === j ? 'opacity-30' : ''}
                    `}
                    title={`${matrix.pm_names[i]} vs ${matrix.pm_names[j]}: ${formatCorrelation(value)}`}
                  >
                    {i !== j ? formatCorrelation(value) : '-'}
                  </motion.div>
                ))}
              </div>
            ))}
          </motion.div>
        </div>
      </div>

      {/* Legend */}
      <div className="mt-6 flex items-center justify-center gap-6 text-xs text-slate-500">
        <div className="flex items-center gap-2">
          <div className="w-4 h-4 rounded bg-blue-500/80"></div>
          <span>Strong Negative</span>
        </div>
        <div className="flex items-center gap-2">
          <div className="w-4 h-4 rounded bg-slate-700/50 border border-white/10"></div>
          <span>Uncorrelated</span>
        </div>
        <div className="flex items-center gap-2">
          <div className="w-4 h-4 rounded bg-rose-500/80"></div>
          <span>Strong Positive</span>
        </div>
      </div>

      {/* High correlation warnings */}
      {concerns && concerns.length > 0 && (
        <div className="mt-6 pt-6 border-t border-white/5">
          <h4 className="text-sm font-medium text-slate-300 mb-3">High Correlation Pairs</h4>
          <div className="space-y-2">
            {concerns.slice(0, 3).map((pair, i) => (
              <motion.div
                key={i}
                initial={{ opacity: 0, x: -10 }}
                animate={{ opacity: 1, x: 0 }}
                transition={{ delay: i * 0.1 }}
                className="flex items-center justify-between text-sm glass-hover p-3 rounded-xl"
              >
                <span className="text-slate-300">
                  {pair.pm1_name.split(' ')[0]} <span className="text-slate-500">↔</span> {pair.pm2_name.split(' ')[0]}
                </span>
                <span className="font-mono font-medium text-rose-400">
                  {formatCorrelation(pair.correlation)}
                </span>
              </motion.div>
            ))}
          </div>
        </div>
      )}
    </motion.div>
  )
}
