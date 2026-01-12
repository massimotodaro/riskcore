import { motion } from 'framer-motion'
import clsx from 'clsx'
import { useNavigate } from 'react-router-dom'
import type { AssetClassRisk } from '../../types'
import { formatCurrency, formatRiskMetric } from '../../services/api'

interface AssetClassCardProps {
  data: AssetClassRisk
  bookId?: string // For drill-down navigation
  bookType?: 'firm' | 'overlay' | 'trading'
  variant?: 'default' | 'compact'
  onTradesClick?: () => void
}

// Asset class icons
const assetClassIcons: Record<string, JSX.Element> = {
  equity: (
    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M13 7h8m0 0v8m0-8l-8 8-4-4-6 6" />
  ),
  fixed_income: (
    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />
  ),
  option: (
    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M7 21a4 4 0 01-4-4V5a2 2 0 012-2h4a2 2 0 012 2v12a4 4 0 01-4 4zm0 0h12a2 2 0 002-2v-4a2 2 0 00-2-2h-2.343M11 7.343l1.657-1.657a2 2 0 012.828 0l2.829 2.829a2 2 0 010 2.828l-8.486 8.485M7 17h.01" />
  ),
  fx: (
    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M12 8c-1.657 0-3 .895-3 2s1.343 2 3 2 3 .895 3 2-1.343 2-3 2m0-8c1.11 0 2.08.402 2.599 1M12 8V7m0 1v8m0 0v1m0-1c-1.11 0-2.08-.402-2.599-1M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
  ),
  cds: (
    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M9 12l2 2 4-4m5.618-4.016A11.955 11.955 0 0112 2.944a11.955 11.955 0 01-8.618 3.04A12.02 12.02 0 003 9c0 5.591 3.824 10.29 9 11.622 5.176-1.332 9-6.03 9-11.622 0-1.042-.133-2.052-.382-3.016z" />
  ),
  future: (
    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M8 7V3m8 4V3m-9 8h10M5 21h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v12a2 2 0 002 2z" />
  ),
  swap: (
    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M8 7h12m0 0l-4-4m4 4l-4 4m0 6H4m0 0l4 4m-4-4l4-4" />
  ),
}

// Color schemes by asset class
const assetClassColors: Record<string, { bg: string; border: string; icon: string; glow: string }> = {
  equity: { bg: 'bg-blue-500/10', border: 'border-blue-500/20', icon: 'text-blue-400', glow: 'hover:shadow-glow-blue' },
  fixed_income: { bg: 'bg-cyan-500/10', border: 'border-cyan-500/20', icon: 'text-cyan-400', glow: 'hover:shadow-glow-cyan' },
  option: { bg: 'bg-purple-500/10', border: 'border-purple-500/20', icon: 'text-purple-400', glow: 'hover:shadow-glow-purple' },
  fx: { bg: 'bg-emerald-500/10', border: 'border-emerald-500/20', icon: 'text-emerald-400', glow: 'hover:shadow-glow-green' },
  cds: { bg: 'bg-amber-500/10', border: 'border-amber-500/20', icon: 'text-amber-400', glow: 'hover:shadow-glow-amber' },
  future: { bg: 'bg-rose-500/10', border: 'border-rose-500/20', icon: 'text-rose-400', glow: 'hover:shadow-glow-red' },
  swap: { bg: 'bg-indigo-500/10', border: 'border-indigo-500/20', icon: 'text-indigo-400', glow: 'hover:shadow-glow-indigo' },
  other: { bg: 'bg-slate-500/10', border: 'border-slate-500/20', icon: 'text-slate-400', glow: 'hover:shadow-glow-slate' },
}

export default function AssetClassCard({
  data,
  bookId,
  bookType = 'trading',
  variant = 'default',
  onTradesClick,
}: AssetClassCardProps) {
  const navigate = useNavigate()
  const colors = assetClassColors[data.asset_class] || assetClassColors.other
  const icon = assetClassIcons[data.asset_class] || assetClassIcons.equity

  const handleTradesClick = () => {
    if (onTradesClick) {
      onTradesClick()
    } else if (bookId) {
      navigate(`/trades/${bookId}/${data.asset_class}`)
    }
  }

  // Determine if net exposure is positive (long) or negative (short)
  const isNetLong = data.net_exposure >= 0
  const exposureColor = isNetLong ? 'text-emerald-400' : 'text-rose-400'

  // For overlay books, typically negative = hedging
  const isHedge = bookType === 'overlay' && data.net_exposure < 0

  return (
    <motion.div
      whileHover={{ y: -2 }}
      transition={{ duration: 0.2 }}
      className={clsx(
        'glass group cursor-default relative',
        variant === 'compact' ? 'p-4' : 'p-5',
        colors.glow
      )}
    >
      {/* Header */}
      <div className="flex items-start justify-between mb-4">
        <div className="flex items-center gap-3">
          <div className={clsx('p-2 rounded-lg', colors.bg)}>
            <svg className={clsx('w-5 h-5', colors.icon)} fill="none" viewBox="0 0 24 24" stroke="currentColor">
              {icon}
            </svg>
          </div>
          <div>
            <h3 className="font-semibold text-slate-100">{data.asset_class_display}</h3>
            <p className="text-xs text-slate-500">{data.position_count} positions</p>
          </div>
        </div>
        {bookType === 'overlay' && isHedge && (
          <span className="badge badge-blue text-xs">Hedge</span>
        )}
      </div>

      {/* Primary Risk Metric */}
      <div className="mb-4">
        <p className="text-xs text-slate-500 uppercase tracking-wider mb-1">
          {data.primary_risk_metric === 'delta' && 'Delta'}
          {data.primary_risk_metric === 'dv01' && 'DV01'}
          {data.primary_risk_metric === 'cs01' && 'CS01'}
          {data.primary_risk_metric === 'net_exposure' && 'Net Exposure'}
        </p>
        <p className={clsx('text-2xl font-bold font-mono', exposureColor)}>
          {data.primary_risk_metric === 'net_exposure'
            ? formatCurrency(data.primary_risk_value)
            : formatRiskMetric(data.primary_risk_value, data.primary_risk_metric)
          }
        </p>
      </div>

      {/* Secondary Metrics */}
      <div className="grid grid-cols-2 gap-3 mb-4">
        <div>
          <p className="text-xs text-slate-500">Gross</p>
          <p className="text-sm font-mono text-slate-300">{formatCurrency(data.gross_exposure)}</p>
        </div>
        <div>
          <p className="text-xs text-slate-500">Net</p>
          <p className={clsx('text-sm font-mono', exposureColor)}>
            {formatCurrency(data.net_exposure)}
          </p>
        </div>
      </div>

      {/* Greeks Row (for options/equity) */}
      {(data.asset_class === 'equity' || data.asset_class === 'option') && data.gamma !== 0 && (
        <div className="flex gap-4 text-xs text-slate-500 border-t border-white/5 pt-3 mb-3">
          {data.gamma !== 0 && (
            <span>
              <span className="text-slate-400">Gamma:</span>{' '}
              <span className="font-mono text-slate-300">{formatRiskMetric(data.gamma, 'gamma')}</span>
            </span>
          )}
          {data.vega !== 0 && (
            <span>
              <span className="text-slate-400">Vega:</span>{' '}
              <span className="font-mono text-slate-300">{formatRiskMetric(data.vega, 'vega')}</span>
            </span>
          )}
        </div>
      )}

      {/* Fixed Income Metrics */}
      {(data.asset_class === 'fixed_income' || data.asset_class === 'swap') && data.convexity !== 0 && (
        <div className="flex gap-4 text-xs text-slate-500 border-t border-white/5 pt-3 mb-3">
          <span>
            <span className="text-slate-400">Convexity:</span>{' '}
            <span className="font-mono text-slate-300">{data.convexity.toFixed(2)}</span>
          </span>
        </div>
      )}

      {/* Underlying Trades Button */}
      <motion.button
        whileHover={{ x: 4 }}
        onClick={handleTradesClick}
        className="w-full flex items-center justify-between px-3 py-2 text-sm text-slate-400
                   hover:text-slate-200 bg-white/5 hover:bg-white/10 rounded-lg
                   transition-all duration-200 border border-white/5 hover:border-white/10"
      >
        <span>Underlying Trades</span>
        <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
        </svg>
      </motion.button>
    </motion.div>
  )
}
