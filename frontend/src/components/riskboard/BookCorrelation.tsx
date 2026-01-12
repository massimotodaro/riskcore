import { motion } from 'framer-motion'
import clsx from 'clsx'
import type { BookCorrelation as BookCorrelationType } from '../../types'
import { formatCurrency } from '../../services/api'

interface BookCorrelationProps {
  data: BookCorrelationType | null
  isLoading?: boolean
  book1Name?: string
  book2Name?: string
}

// Get correlation strength label and color
function getCorrelationInfo(correlation: number): { label: string; color: string; bgColor: string } {
  const absCorr = Math.abs(correlation)

  if (absCorr >= 0.8) {
    return correlation > 0
      ? { label: 'Strong Positive', color: 'text-red-400', bgColor: 'bg-red-500/20' }
      : { label: 'Strong Negative', color: 'text-emerald-400', bgColor: 'bg-emerald-500/20' }
  }
  if (absCorr >= 0.5) {
    return correlation > 0
      ? { label: 'Moderate Positive', color: 'text-amber-400', bgColor: 'bg-amber-500/20' }
      : { label: 'Moderate Negative', color: 'text-cyan-400', bgColor: 'bg-cyan-500/20' }
  }
  return { label: 'Weak', color: 'text-slate-400', bgColor: 'bg-slate-500/20' }
}

export default function BookCorrelation({
  data,
  isLoading = false,
  book1Name,
  book2Name,
}: BookCorrelationProps) {
  // Loading state
  if (isLoading) {
    return (
      <div className="glass p-6 animate-pulse">
        <div className="flex items-center justify-between mb-6">
          <div className="h-6 w-48 bg-slate-700/50 rounded" />
          <div className="h-8 w-24 bg-slate-700/50 rounded" />
        </div>
        <div className="grid grid-cols-3 gap-6">
          {[...Array(3)].map((_, i) => (
            <div key={i} className="space-y-2">
              <div className="h-4 w-24 bg-slate-700/30 rounded" />
              <div className="h-8 w-32 bg-slate-700/50 rounded" />
            </div>
          ))}
        </div>
      </div>
    )
  }

  // Empty state - no portfolios selected
  if (!data) {
    return (
      <div className="glass p-6">
        <div className="text-center py-8">
          <svg
            className="w-12 h-12 text-slate-600 mx-auto mb-3"
            fill="none"
            viewBox="0 0 24 24"
            stroke="currentColor"
          >
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              strokeWidth={1.5}
              d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z"
            />
          </svg>
          <p className="text-slate-400">Select two portfolios to compare</p>
          <p className="text-sm text-slate-500 mt-1">
            See correlation, overlapping positions, and netting opportunities
          </p>
        </div>
      </div>
    )
  }

  const corrInfo = getCorrelationInfo(data.correlation)

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      className="glass p-6"
    >
      {/* Header */}
      <div className="flex items-start justify-between mb-6">
        <div>
          <h3 className="text-lg font-semibold text-slate-100">
            Portfolio Correlation
          </h3>
          <p className="text-sm text-slate-500 mt-1">
            {book1Name || data.book1_name} vs {book2Name || data.book2_name}
          </p>
        </div>

        {/* Correlation Badge */}
        <div className={clsx('px-3 py-1.5 rounded-lg', corrInfo.bgColor)}>
          <span className={clsx('text-lg font-bold font-mono', corrInfo.color)}>
            {data.correlation.toFixed(2)}
          </span>
        </div>
      </div>

      {/* Metrics Grid */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
        {/* Correlation Strength */}
        <div className="space-y-2">
          <p className="text-xs text-slate-500 uppercase tracking-wider">
            Correlation Strength
          </p>
          <div className="flex items-center gap-2">
            <div className={clsx('w-3 h-3 rounded-full', corrInfo.bgColor)} />
            <span className={clsx('font-medium', corrInfo.color)}>
              {corrInfo.label}
            </span>
          </div>
          <p className="text-xs text-slate-500">
            Based on {data.data_points} data points
          </p>
        </div>

        {/* Overlapping Securities */}
        <div className="space-y-2">
          <p className="text-xs text-slate-500 uppercase tracking-wider">
            Overlapping Securities
          </p>
          <p className="text-2xl font-bold font-mono text-slate-100">
            {data.overlapping_securities}
          </p>
          <p className="text-xs text-slate-500">
            Securities held by both portfolios
          </p>
        </div>

        {/* Netting Opportunity */}
        <div className="space-y-2">
          <p className="text-xs text-slate-500 uppercase tracking-wider">
            Netting Opportunity
          </p>
          <p className={clsx(
            'text-2xl font-bold font-mono',
            data.netting_opportunity > 0 ? 'text-emerald-400' : 'text-slate-400'
          )}>
            {formatCurrency(data.netting_opportunity)}
          </p>
          <p className="text-xs text-slate-500">
            Potential exposure reduction
          </p>
        </div>

        {/* Visual Correlation Bar */}
        <div className="space-y-2">
          <p className="text-xs text-slate-500 uppercase tracking-wider">
            Correlation Spectrum
          </p>
          <div className="relative h-8">
            {/* Background gradient */}
            <div className="absolute inset-0 rounded-lg overflow-hidden">
              <div className="h-full w-full flex">
                <div className="flex-1 bg-gradient-to-r from-emerald-500/30 to-slate-500/30" />
                <div className="flex-1 bg-gradient-to-r from-slate-500/30 to-red-500/30" />
              </div>
            </div>
            {/* Marker */}
            <motion.div
              initial={{ left: '50%' }}
              animate={{ left: `${((data.correlation + 1) / 2) * 100}%` }}
              transition={{ type: 'spring', stiffness: 200, damping: 20 }}
              className="absolute top-0 h-full w-1"
            >
              <div className="absolute top-0 left-1/2 -translate-x-1/2 w-3 h-full bg-white rounded-full shadow-lg" />
            </motion.div>
            {/* Labels */}
            <div className="absolute -bottom-5 left-0 text-[10px] text-slate-600">-1.0</div>
            <div className="absolute -bottom-5 left-1/2 -translate-x-1/2 text-[10px] text-slate-600">0</div>
            <div className="absolute -bottom-5 right-0 text-[10px] text-slate-600">+1.0</div>
          </div>
        </div>
      </div>

      {/* Interpretation */}
      <div className="mt-6 p-4 bg-slate-800/30 rounded-lg border border-white/5">
        <div className="flex items-start gap-3">
          <svg
            className="w-5 h-5 text-blue-400 flex-shrink-0 mt-0.5"
            fill="none"
            viewBox="0 0 24 24"
            stroke="currentColor"
          >
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              strokeWidth={2}
              d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"
            />
          </svg>
          <div>
            <p className="text-sm text-slate-300">
              {data.correlation > 0.7 && (
                <>
                  <span className="text-amber-400 font-medium">High positive correlation</span> suggests these portfolios
                  may have concentrated risk. Consider reviewing overlapping positions for diversification.
                </>
              )}
              {data.correlation > 0.3 && data.correlation <= 0.7 && (
                <>
                  <span className="text-slate-200 font-medium">Moderate correlation</span> indicates some shared
                  exposures. The portfolios have reasonable diversification.
                </>
              )}
              {data.correlation >= -0.3 && data.correlation <= 0.3 && (
                <>
                  <span className="text-emerald-400 font-medium">Low correlation</span> means these portfolios are
                  well-diversified from each other, providing good risk distribution.
                </>
              )}
              {data.correlation < -0.3 && data.correlation >= -0.7 && (
                <>
                  <span className="text-cyan-400 font-medium">Negative correlation</span> suggests natural hedging
                  between these portfolios. They tend to offset each other's risk.
                </>
              )}
              {data.correlation < -0.7 && (
                <>
                  <span className="text-emerald-400 font-medium">Strong negative correlation</span> indicates these
                  portfolios act as natural hedges. Consider if this is intentional.
                </>
              )}
            </p>
            {data.netting_opportunity > 0 && (
              <p className="text-xs text-slate-500 mt-2">
                Potential netting of {formatCurrency(data.netting_opportunity)} available through the overlay book.
              </p>
            )}
          </div>
        </div>
      </div>
    </motion.div>
  )
}
