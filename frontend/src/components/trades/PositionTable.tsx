import { useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { motion, AnimatePresence } from 'framer-motion'
import clsx from 'clsx'
import { tradesPageApi, formatCurrency, formatQuantity, formatDate, RISKPOD_CONFIG } from '../../services/api'
import type { HistoricalPosition, RiskPodType } from '../../types'

interface PositionTableProps {
  positions: HistoricalPosition[]
  riskpod: RiskPodType
  onReprice: (position: HistoricalPosition) => void
  isDarkMode?: boolean
}

interface ExpandedRowProps {
  position: HistoricalPosition
}

function ExpandedTradeRow({ position }: ExpandedRowProps) {
  const { data: trades = [], isLoading } = useQuery({
    queryKey: ['position-trades', position.book_id, position.security_id],
    queryFn: () => tradesPageApi.getTradesForPosition(position.book_id, position.security_id),
    staleTime: 30000,
  })

  if (isLoading) {
    return (
      <tr>
        <td colSpan={10} className="px-4 py-4 text-center text-slate-500">
          Loading trades...
        </td>
      </tr>
    )
  }

  if (trades.length === 0) {
    return (
      <tr>
        <td colSpan={10} className="px-4 py-4 text-center text-slate-500">
          No underlying trades found
        </td>
      </tr>
    )
  }

  return (
    <>
      {/* Expanded header */}
      <tr className="bg-slate-800/30">
        <td colSpan={10} className="px-4 py-2">
          <div className="flex items-center gap-2 text-xs font-medium text-slate-400">
            <span className="w-4" /> {/* Indent */}
            <span className="w-24">Trade ID</span>
            <span className="w-20">Date</span>
            <span className="w-16">Side</span>
            <span className="w-20 text-right">Qty</span>
            <span className="w-20 text-right">Price</span>
            <span className="w-24 text-right">Notional</span>
            <span className="flex-1">Counterparty</span>
            <span className="w-24">Broker</span>
          </div>
        </td>
      </tr>

      {/* Trade rows */}
      {trades.map((trade) => (
        <motion.tr
          key={trade.trade_id}
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          className="bg-slate-800/20 border-t border-white/5"
        >
          <td colSpan={10} className="px-4 py-2">
            <div className="flex items-center gap-2 text-xs">
              <span className="w-4" /> {/* Indent */}
              <span className="w-24 text-slate-400 font-mono">
                {trade.trade_id_external || trade.trade_id.slice(0, 8)}
              </span>
              <span className="w-20 text-slate-400">
                {formatDate(trade.trade_date)}
              </span>
              <span className={clsx(
                'w-16 font-medium',
                trade.side === 'buy' || trade.side === 'cover' ? 'text-emerald-400' : 'text-red-400'
              )}>
                {trade.side.toUpperCase()}
              </span>
              <span className="w-20 text-right text-white">
                {formatQuantity(trade.quantity)}
              </span>
              <span className="w-20 text-right text-slate-300">
                ${trade.price.toFixed(2)}
              </span>
              <span className="w-24 text-right text-white">
                {formatCurrency(trade.notional)}
              </span>
              <span className="flex-1 text-amber-300 font-medium">
                {trade.counterparty || '-'}
              </span>
              <span className="w-24 text-slate-400">
                {trade.broker || '-'}
              </span>
            </div>
          </td>
        </motion.tr>
      ))}
    </>
  )
}

export default function PositionTable({
  positions,
  riskpod,
  onReprice,
  isDarkMode = true,
}: PositionTableProps) {
  const [expandedId, setExpandedId] = useState<string | null>(null)
  const config = RISKPOD_CONFIG[riskpod]

  // Theme-aware colors
  const colors = {
    text: isDarkMode ? '#e2e8f0' : '#1e293b',
    textMuted: '#64748b',
    textLight: isDarkMode ? '#94a3b8' : '#475569',
    border: isDarkMode ? 'rgba(255, 255, 255, 0.1)' : 'rgba(0, 0, 0, 0.1)',
    borderFaint: isDarkMode ? 'rgba(255, 255, 255, 0.05)' : 'rgba(0, 0, 0, 0.05)',
    hover: isDarkMode ? 'rgba(255, 255, 255, 0.05)' : 'rgba(0, 0, 0, 0.03)',
    expanded: isDarkMode ? 'rgba(255, 255, 255, 0.05)' : 'rgba(0, 0, 0, 0.03)',
    expandedTrades: isDarkMode ? 'rgba(30, 41, 59, 0.5)' : 'rgba(0, 0, 0, 0.02)',
  }

  const toggleExpand = (positionId: string) => {
    setExpandedId((prev) => (prev === positionId ? null : positionId))
  }

  // Get risk metric columns based on riskpod
  const getRiskMetricValue = (position: HistoricalPosition, metric: string): string => {
    const value = position[metric as keyof HistoricalPosition]
    if (typeof value === 'number') {
      if (Math.abs(value) >= 1_000_000) {
        return `${(value / 1_000_000).toFixed(2)}M`
      }
      if (Math.abs(value) >= 1_000) {
        return `${(value / 1_000).toFixed(1)}K`
      }
      return value.toFixed(0)
    }
    return '-'
  }

  return (
    <div className="overflow-x-auto">
      <table className="w-full">
        <thead>
          <tr style={{ borderBottom: `1px solid ${colors.border}` }}>
            <th className="px-4 py-3 text-left text-xs font-medium uppercase tracking-wider w-8" style={{ color: colors.textMuted }}>
              {/* Expand icon */}
            </th>
            <th className="px-4 py-3 text-left text-xs font-medium uppercase tracking-wider" style={{ color: colors.textMuted }}>
              Instrument
            </th>
            <th className="px-4 py-3 text-left text-xs font-medium uppercase tracking-wider" style={{ color: colors.textMuted }}>
              Book
            </th>
            <th className="px-4 py-3 text-left text-xs font-medium uppercase tracking-wider" style={{ color: colors.textMuted }}>
              PM
            </th>
            <th className="px-4 py-3 text-center text-xs font-medium uppercase tracking-wider" style={{ color: colors.textMuted }}>
              Direction
            </th>
            <th className="px-4 py-3 text-right text-xs font-medium uppercase tracking-wider" style={{ color: colors.textMuted }}>
              Quantity
            </th>
            <th className="px-4 py-3 text-right text-xs font-medium uppercase tracking-wider" style={{ color: colors.textMuted }}>
              Market Value
            </th>
            {/* Dynamic risk metric columns */}
            {config.columns.map((col) => (
              <th
                key={col}
                className="px-4 py-3 text-right text-xs font-medium uppercase tracking-wider"
                style={{ color: colors.textMuted }}
              >
                {col === 'sector' ? 'Sector' : col.toUpperCase()}
              </th>
            ))}
            <th className="px-4 py-3 text-center text-xs font-medium uppercase tracking-wider w-24" style={{ color: colors.textMuted }}>
              Reprice
            </th>
          </tr>
        </thead>
        <tbody style={{ borderTop: `1px solid ${colors.borderFaint}` }}>
          {positions.map((position) => {
            const positionId = position.position_id || position.history_id || `${position.book_id}-${position.security_id}`
            const isExpanded = expandedId === positionId

            return (
              <AnimatePresence key={positionId}>
                {/* Main position row */}
                <motion.tr
                  initial={{ opacity: 0 }}
                  animate={{ opacity: 1 }}
                  className="transition-colors"
                  style={{
                    background: isExpanded ? colors.expanded : undefined,
                    borderBottom: `1px solid ${colors.borderFaint}`,
                  }}
                >
                  {/* Expand button */}
                  <td className="px-4 py-3">
                    <button
                      onClick={() => toggleExpand(positionId)}
                      className="p-1 rounded transition-colors"
                      style={{ color: colors.textMuted }}
                    >
                      <svg
                        className={clsx(
                          'w-4 h-4 transition-transform',
                          isExpanded && 'rotate-90'
                        )}
                        fill="none"
                        viewBox="0 0 24 24"
                        stroke="currentColor"
                      >
                        <path
                          strokeLinecap="round"
                          strokeLinejoin="round"
                          strokeWidth={1.5}
                          d="M9 5l7 7-7 7"
                        />
                      </svg>
                    </button>
                  </td>

                  {/* Instrument */}
                  <td className="px-4 py-3">
                    <button
                      onClick={() => toggleExpand(positionId)}
                      className="text-left hover:text-blue-400 transition-colors"
                    >
                      <div className="font-medium" style={{ color: colors.text }}>
                        {position.ticker || position.security_name?.slice(0, 10)}
                      </div>
                      <div className="text-xs truncate max-w-[150px]" style={{ color: colors.textMuted }}>
                        {position.security_name}
                      </div>
                    </button>
                  </td>

                  {/* Book */}
                  <td className="px-4 py-3 text-sm" style={{ color: colors.textLight }}>
                    {position.book_name}
                  </td>

                  {/* PM */}
                  <td className="px-4 py-3 text-sm" style={{ color: colors.textMuted }}>
                    {position.pm_name || '-'}
                  </td>

                  {/* Direction */}
                  <td className="px-4 py-3 text-center">
                    <span
                      className="inline-flex px-2 py-0.5 rounded-full text-xs font-medium"
                      style={position.direction === 'long'
                        ? { background: 'rgba(34, 197, 94, 0.2)', color: '#4ade80' }
                        : { background: 'rgba(239, 68, 68, 0.2)', color: '#f87171' }
                      }
                    >
                      {position.direction.toUpperCase()}
                    </span>
                  </td>

                  {/* Quantity */}
                  <td className="px-4 py-3 text-right text-sm font-mono" style={{ color: colors.text }}>
                    {formatQuantity(position.quantity)}
                  </td>

                  {/* Market Value */}
                  <td className="px-4 py-3 text-right text-sm font-medium">
                    <span style={{ color: position.market_value >= 0 ? '#34d399' : '#f87171' }}>
                      {formatCurrency(position.market_value)}
                    </span>
                  </td>

                  {/* Dynamic risk metric columns */}
                  {config.columns.map((col) => (
                    <td key={col} className="px-4 py-3 text-right text-sm">
                      {col === 'sector' ? (
                        <span style={{ color: colors.textMuted }}>{position.sector || '-'}</span>
                      ) : (
                        <span className="font-mono" style={{ color: colors.textLight }}>
                          {getRiskMetricValue(position, col)}
                        </span>
                      )}
                    </td>
                  ))}

                  {/* Reprice button */}
                  <td className="px-4 py-3 text-center">
                    <button
                      onClick={() => onReprice(position)}
                      className="px-2 py-1 rounded text-xs font-medium transition-colors"
                      style={{
                        background: 'rgba(245, 158, 11, 0.1)',
                        color: '#fbbf24',
                        border: '1px solid rgba(245, 158, 11, 0.2)',
                      }}
                    >
                      Reprice
                    </button>
                  </td>
                </motion.tr>

                {/* Expanded trades section */}
                {isExpanded && (
                  <ExpandedTradeRow position={position} />
                )}
              </AnimatePresence>
            )
          })}
        </tbody>
      </table>
    </div>
  )
}
