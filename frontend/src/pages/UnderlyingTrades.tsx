import { useState } from 'react'
import { useParams, useNavigate, Link } from 'react-router-dom'
import { useQuery } from '@tanstack/react-query'
import { motion, AnimatePresence } from 'framer-motion'
import clsx from 'clsx'
import { tradesApi, formatCurrency, formatRiskMetric } from '../services/api'
import type { TradeDetail } from '../types'
import ValuationModal from '../components/riskboard/ValuationModal'

// Asset class display names
const assetClassDisplayNames: Record<string, string> = {
  equity: 'Equities',
  fixed_income: 'Fixed Income',
  option: 'Options',
  fx: 'FX',
  cds: 'Credit Default Swaps',
  future: 'Futures',
  swap: 'Swaps',
}

// Price source badges
const priceSourceBadge = (source: string) => {
  switch (source) {
    case 'market':
      return { label: 'Market', color: 'bg-emerald-500/20 text-emerald-400 border-emerald-500/30' }
    case 'model':
      return { label: 'Model', color: 'bg-blue-500/20 text-blue-400 border-blue-500/30' }
    case 'manual':
      return { label: 'Manual', color: 'bg-amber-500/20 text-amber-400 border-amber-500/30' }
    case 'stale':
      return { label: 'Stale', color: 'bg-red-500/20 text-red-400 border-red-500/30' }
    default:
      return { label: source, color: 'bg-slate-500/20 text-slate-400 border-slate-500/30' }
  }
}

// Side colors
const sideColors: Record<string, string> = {
  buy: 'text-emerald-400',
  sell: 'text-rose-400',
  short: 'text-rose-400',
  cover: 'text-emerald-400',
}

export default function UnderlyingTrades() {
  const { bookId, assetClass } = useParams<{ bookId: string; assetClass: string }>()
  const navigate = useNavigate()

  // Pagination state
  const [page, setPage] = useState(1)
  const [pageSize] = useState(25)

  // Valuation modal state
  const [selectedTrade, setSelectedTrade] = useState<TradeDetail | null>(null)
  const [showValuationModal, setShowValuationModal] = useState(false)

  // Fetch trades
  const {
    data: tradesResponse,
    isLoading,
    error,
  } = useQuery({
    queryKey: ['trades', bookId, assetClass, page, pageSize],
    queryFn: () => {
      if (bookId === 'firm') {
        // Firm-wide trades (all books, filtered by asset class)
        return tradesApi.getByBook('', assetClass, page, pageSize)
      }
      return tradesApi.getByBook(bookId!, assetClass, page, pageSize)
    },
    enabled: !!bookId,
  })

  const trades = tradesResponse?.trades ?? []
  const totalTrades = tradesResponse?.total ?? 0
  const totalPages = Math.ceil(totalTrades / pageSize)

  // Handle valuation click
  const handleValuationClick = (trade: TradeDetail) => {
    setSelectedTrade(trade)
    setShowValuationModal(true)
  }

  // Format date
  const formatDate = (dateStr: string) => {
    const date = new Date(dateStr)
    return date.toLocaleDateString('en-US', {
      year: 'numeric',
      month: 'short',
      day: 'numeric',
    })
  }

  // Get primary risk metric based on asset class
  const getPrimaryRiskColumn = () => {
    switch (assetClass) {
      case 'fixed_income':
      case 'swap':
        return { key: 'dv01', label: 'DV01' }
      case 'cds':
        return { key: 'cs01', label: 'CS01' }
      default:
        return { key: 'delta', label: 'Delta' }
    }
  }

  const primaryRisk = getPrimaryRiskColumn()

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-950 via-slate-900 to-slate-950">
      <div className="max-w-[1800px] mx-auto px-6 py-8">
        {/* Breadcrumb */}
        <nav className="flex items-center gap-2 text-sm text-slate-500 mb-6">
          <Link to="/cio" className="hover:text-slate-300 transition-colors">
            CIO Dashboard
          </Link>
          <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
          </svg>
          <span className="text-slate-300">
            {bookId === 'firm' ? 'Firm-Wide' : 'Portfolio'} Trades
          </span>
          <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
          </svg>
          <span className="text-slate-100">
            {assetClassDisplayNames[assetClass || ''] || assetClass}
          </span>
        </nav>

        {/* Header */}
        <motion.div
          initial={{ opacity: 0, y: -20 }}
          animate={{ opacity: 1, y: 0 }}
          className="flex items-start justify-between mb-8"
        >
          <div>
            <h1 className="text-2xl font-bold text-slate-100">
              {assetClassDisplayNames[assetClass || ''] || assetClass} Trades
            </h1>
            <p className="text-slate-500 mt-1">
              {bookId === 'firm'
                ? 'All trades across the firm'
                : `Trades in the selected portfolio`}{' '}
              • {totalTrades.toLocaleString()} total
            </p>
          </div>
          <button
            onClick={() => navigate(-1)}
            className="flex items-center gap-2 px-4 py-2 text-sm text-slate-400 hover:text-slate-200
                     bg-white/5 hover:bg-white/10 rounded-lg transition-all duration-200
                     border border-white/5 hover:border-white/10"
          >
            <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10 19l-7-7m0 0l7-7m-7 7h18" />
            </svg>
            Back
          </button>
        </motion.div>

        {/* Trades Table */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.1 }}
          className="glass overflow-hidden"
        >
          {/* Loading State */}
          {isLoading && (
            <div className="p-8 text-center">
              <div className="animate-spin w-8 h-8 border-2 border-blue-500 border-t-transparent rounded-full mx-auto mb-4" />
              <p className="text-slate-400">Loading trades...</p>
            </div>
          )}

          {/* Error State */}
          {error && (
            <div className="p-8 text-center">
              <svg className="w-12 h-12 text-red-400 mx-auto mb-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
              </svg>
              <p className="text-red-400">Failed to load trades</p>
              <p className="text-sm text-slate-500 mt-1">{(error as Error).message}</p>
            </div>
          )}

          {/* Empty State */}
          {!isLoading && !error && trades.length === 0 && (
            <div className="p-8 text-center">
              <svg className="w-12 h-12 text-slate-600 mx-auto mb-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2" />
              </svg>
              <p className="text-slate-400">No trades found</p>
              <p className="text-sm text-slate-500 mt-1">
                There are no {assetClassDisplayNames[assetClass || ''] || assetClass} trades in this portfolio
              </p>
            </div>
          )}

          {/* Table */}
          {!isLoading && !error && trades.length > 0 && (
            <>
              <div className="overflow-x-auto">
                <table className="w-full">
                  <thead>
                    <tr className="border-b border-white/5">
                      <th className="text-left px-4 py-3 text-xs font-medium text-slate-500 uppercase tracking-wider">
                        Security
                      </th>
                      <th className="text-left px-4 py-3 text-xs font-medium text-slate-500 uppercase tracking-wider">
                        Book
                      </th>
                      <th className="text-center px-4 py-3 text-xs font-medium text-slate-500 uppercase tracking-wider">
                        Side
                      </th>
                      <th className="text-right px-4 py-3 text-xs font-medium text-slate-500 uppercase tracking-wider">
                        Quantity
                      </th>
                      <th className="text-right px-4 py-3 text-xs font-medium text-slate-500 uppercase tracking-wider">
                        Price
                      </th>
                      <th className="text-right px-4 py-3 text-xs font-medium text-slate-500 uppercase tracking-wider">
                        Notional
                      </th>
                      <th className="text-right px-4 py-3 text-xs font-medium text-slate-500 uppercase tracking-wider">
                        {primaryRisk.label}
                      </th>
                      {assetClass === 'option' && (
                        <>
                          <th className="text-right px-4 py-3 text-xs font-medium text-slate-500 uppercase tracking-wider">
                            Gamma
                          </th>
                          <th className="text-right px-4 py-3 text-xs font-medium text-slate-500 uppercase tracking-wider">
                            Vega
                          </th>
                        </>
                      )}
                      <th className="text-center px-4 py-3 text-xs font-medium text-slate-500 uppercase tracking-wider">
                        Price Source
                      </th>
                      <th className="text-left px-4 py-3 text-xs font-medium text-slate-500 uppercase tracking-wider">
                        Trade Date
                      </th>
                      <th className="text-center px-4 py-3 text-xs font-medium text-slate-500 uppercase tracking-wider">
                        Actions
                      </th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-white/5">
                    {trades.map((trade) => {
                      const priceBadge = priceSourceBadge(trade.price_source)
                      return (
                        <motion.tr
                          key={trade.trade_id}
                          initial={{ opacity: 0 }}
                          animate={{ opacity: 1 }}
                          className="hover:bg-white/5 transition-colors"
                        >
                          {/* Security */}
                          <td className="px-4 py-3">
                            <div>
                              <p className="font-medium text-slate-100">{trade.ticker}</p>
                              <p className="text-xs text-slate-500 truncate max-w-[200px]">
                                {trade.security_name}
                              </p>
                            </div>
                          </td>

                          {/* Book */}
                          <td className="px-4 py-3">
                            <p className="text-sm text-slate-300">{trade.book_name}</p>
                          </td>

                          {/* Side */}
                          <td className="px-4 py-3 text-center">
                            <span
                              className={clsx(
                                'text-sm font-medium uppercase',
                                sideColors[trade.side] || 'text-slate-400'
                              )}
                            >
                              {trade.side}
                            </span>
                          </td>

                          {/* Quantity */}
                          <td className="px-4 py-3 text-right">
                            <span className="font-mono text-sm text-slate-300">
                              {trade.quantity.toLocaleString()}
                            </span>
                          </td>

                          {/* Price */}
                          <td className="px-4 py-3 text-right">
                            <span className="font-mono text-sm text-slate-300">
                              ${trade.price.toFixed(2)}
                            </span>
                          </td>

                          {/* Notional */}
                          <td className="px-4 py-3 text-right">
                            <span className="font-mono text-sm text-slate-300">
                              {formatCurrency(trade.notional)}
                            </span>
                          </td>

                          {/* Primary Risk */}
                          <td className="px-4 py-3 text-right">
                            <span
                              className={clsx(
                                'font-mono text-sm',
                                (trade[primaryRisk.key as keyof TradeDetail] as number ?? 0) >= 0
                                  ? 'text-emerald-400'
                                  : 'text-rose-400'
                              )}
                            >
                              {formatRiskMetric(
                                trade[primaryRisk.key as keyof TradeDetail] as number ?? 0,
                                primaryRisk.key
                              )}
                            </span>
                          </td>

                          {/* Greeks for options */}
                          {assetClass === 'option' && (
                            <>
                              <td className="px-4 py-3 text-right">
                                <span className="font-mono text-sm text-slate-300">
                                  {formatRiskMetric(trade.gamma ?? 0, 'gamma')}
                                </span>
                              </td>
                              <td className="px-4 py-3 text-right">
                                <span className="font-mono text-sm text-slate-300">
                                  {formatRiskMetric(trade.vega ?? 0, 'vega')}
                                </span>
                              </td>
                            </>
                          )}

                          {/* Price Source */}
                          <td className="px-4 py-3 text-center">
                            <span
                              className={clsx(
                                'inline-flex px-2 py-0.5 text-xs font-medium rounded border',
                                priceBadge.color
                              )}
                            >
                              {priceBadge.label}
                            </span>
                          </td>

                          {/* Trade Date */}
                          <td className="px-4 py-3">
                            <span className="text-sm text-slate-400">
                              {formatDate(trade.trade_date)}
                            </span>
                          </td>

                          {/* Actions */}
                          <td className="px-4 py-3 text-center">
                            {trade.has_model_details && (
                              <button
                                onClick={() => handleValuationClick(trade)}
                                className="text-blue-400 hover:text-blue-300 text-sm font-medium
                                         transition-colors duration-150"
                              >
                                Valuation
                              </button>
                            )}
                          </td>
                        </motion.tr>
                      )
                    })}
                  </tbody>
                </table>
              </div>

              {/* Pagination */}
              {totalPages > 1 && (
                <div className="flex items-center justify-between px-4 py-3 border-t border-white/5">
                  <p className="text-sm text-slate-500">
                    Showing {(page - 1) * pageSize + 1} to{' '}
                    {Math.min(page * pageSize, totalTrades)} of {totalTrades.toLocaleString()}{' '}
                    trades
                  </p>
                  <div className="flex items-center gap-2">
                    <button
                      onClick={() => setPage((p) => Math.max(1, p - 1))}
                      disabled={page === 1}
                      className="px-3 py-1.5 text-sm text-slate-400 hover:text-slate-200
                               bg-white/5 hover:bg-white/10 rounded-lg transition-all
                               disabled:opacity-50 disabled:cursor-not-allowed"
                    >
                      Previous
                    </button>
                    <span className="text-sm text-slate-500">
                      Page {page} of {totalPages}
                    </span>
                    <button
                      onClick={() => setPage((p) => Math.min(totalPages, p + 1))}
                      disabled={page === totalPages}
                      className="px-3 py-1.5 text-sm text-slate-400 hover:text-slate-200
                               bg-white/5 hover:bg-white/10 rounded-lg transition-all
                               disabled:opacity-50 disabled:cursor-not-allowed"
                    >
                      Next
                    </button>
                  </div>
                </div>
              )}
            </>
          )}
        </motion.div>

        {/* Valuation Modal */}
        <AnimatePresence>
          {showValuationModal && selectedTrade && (
            <ValuationModal
              tradeId={selectedTrade.trade_id}
              securityName={selectedTrade.security_name}
              ticker={selectedTrade.ticker}
              onClose={() => {
                setShowValuationModal(false)
                setSelectedTrade(null)
              }}
            />
          )}
        </AnimatePresence>
      </div>
    </div>
  )
}
