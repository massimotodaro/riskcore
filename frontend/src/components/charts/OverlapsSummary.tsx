import { useQuery } from '@tanstack/react-query'
import { motion } from 'framer-motion'
import { aggregationApi, formatCurrency } from '../../services/api'
import clsx from 'clsx'

const itemVariants = {
  hidden: { opacity: 0, x: -10 },
  visible: { opacity: 1, x: 0 },
}

export default function OverlapsSummary() {
  const { data: overlaps, isLoading, error } = useQuery({
    queryKey: ['overlaps'],
    queryFn: () => aggregationApi.getOverlapsBySecurity(undefined, 'high'),
  })

  const { data: summary } = useQuery({
    queryKey: ['overlapsSummary'],
    queryFn: () => aggregationApi.getOverlapsSummary(),
  })

  if (isLoading) {
    return (
      <div className="glass p-6">
        <h3 className="section-title mb-4">Overlapping Positions</h3>
        <div className="animate-pulse space-y-3">
          {[...Array(5)].map((_, i) => (
            <div key={i} className="h-12 bg-white/5 rounded-xl"></div>
          ))}
        </div>
      </div>
    )
  }

  if (error) {
    return (
      <div className="glass p-6">
        <h3 className="section-title mb-4">Overlapping Positions</h3>
        <div className="text-slate-500 text-center py-8">
          Unable to load overlap data.
        </div>
      </div>
    )
  }

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.4, delay: 0.1 }}
      className="glass p-6"
    >
      <div className="flex items-center justify-between mb-6">
        <div>
          <h3 className="section-title">Overlapping Positions</h3>
          <p className="section-subtitle mt-1">Securities held by multiple PMs</p>
        </div>
        {summary && (
          <div className="flex gap-2">
            <span className="badge badge-red">{summary.high_severity} High</span>
            <span className="badge badge-yellow">{summary.medium_severity} Med</span>
          </div>
        )}
      </div>

      {/* Overlaps list */}
      <div className="space-y-2">
        {overlaps && overlaps.length > 0 ? (
          overlaps.slice(0, 6).map((overlap, i) => (
            <motion.div
              key={i}
              variants={itemVariants}
              initial="hidden"
              animate="visible"
              transition={{ delay: i * 0.05 }}
              className="flex items-center justify-between p-3 rounded-xl glass-hover cursor-default"
            >
              <div className="flex items-center gap-3">
                <span
                  className={clsx(
                    'w-2 h-2 rounded-full',
                    overlap.severity === 'high' && 'bg-rose-500 shadow-glow-red',
                    overlap.severity === 'medium' && 'bg-amber-500',
                    overlap.severity === 'low' && 'bg-emerald-500'
                  )}
                />
                <div>
                  <div className="font-medium text-slate-100">{overlap.ticker}</div>
                  <div className="text-xs text-slate-500">
                    {overlap.pm_count} PMs &bull; {overlap.overlap_type.replace('_', ' ')}
                  </div>
                </div>
              </div>
              <div className="text-right">
                <div className="font-mono font-medium text-slate-100 tabular-nums">
                  {formatCurrency(Math.abs(overlap.net_exposure))}
                </div>
                <div
                  className={clsx(
                    'text-xs font-medium',
                    overlap.net_exposure > 0 ? 'text-emerald-400' : 'text-rose-400'
                  )}
                >
                  {overlap.net_exposure > 0 ? 'Net Long' : 'Net Short'}
                </div>
              </div>
            </motion.div>
          ))
        ) : (
          <div className="text-slate-500 text-center py-8">No overlapping positions detected</div>
        )}
      </div>

      {/* Summary stats */}
      {summary && summary.total_netting_opportunity > 0 && (
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ delay: 0.3 }}
          className="mt-6 pt-6 border-t border-white/5"
        >
          <div className="flex items-center justify-between text-sm">
            <span className="text-slate-400">Total netting opportunity:</span>
            <span className="font-mono font-medium text-emerald-400">
              {formatCurrency(summary.total_netting_opportunity)}
            </span>
          </div>
        </motion.div>
      )}
    </motion.div>
  )
}
