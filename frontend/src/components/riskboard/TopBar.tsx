import { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { motion } from 'framer-motion'
import { riskboardApi, pricingApi, formatCurrency } from '../../services/api'
import MarketSnapshot from './MarketSnapshot'

interface TopBarProps {
  tenantId?: string
  bookIds?: string[]
}

export default function TopBar({ tenantId, bookIds }: TopBarProps) {
  const queryClient = useQueryClient()
  const [repricing, setRepricing] = useState(false)

  // Fetch risk summary
  const { data: summary, isLoading: summaryLoading } = useQuery({
    queryKey: ['riskSummary', tenantId, bookIds],
    queryFn: () => riskboardApi.getSummary(tenantId, bookIds),
    refetchInterval: 30000, // Refresh every 30 seconds
  })

  // Fetch pricing status
  const { data: pricingStatus } = useQuery({
    queryKey: ['pricingStatus', tenantId],
    queryFn: () => pricingApi.getStatus(tenantId),
    refetchInterval: 30000,
  })

  // Reprice mutation
  const repriceMutation = useMutation({
    mutationFn: () => pricingApi.repriceAll(tenantId),
    onMutate: () => setRepricing(true),
    onSettled: () => {
      setRepricing(false)
      queryClient.invalidateQueries({ queryKey: ['riskSummary'] })
      queryClient.invalidateQueries({ queryKey: ['pricingStatus'] })
    },
  })

  // Format last priced time
  const formatLastPriced = (isoString?: string) => {
    if (!isoString) return 'Never'
    const date = new Date(isoString)
    return date.toLocaleTimeString('en-US', {
      hour: 'numeric',
      minute: '2-digit',
      hour12: true,
    })
  }

  const lastPricedTime = pricingStatus?.latest_run?.completed_at
    ? formatLastPriced(pricingStatus.latest_run.completed_at)
    : summary?.last_priced
    ? formatLastPriced(summary.last_priced)
    : 'Never'

  return (
    <div className="space-y-4">
      {/* Market Snapshot Row */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2">
          <span className="text-xs text-slate-500 uppercase tracking-wider">Market</span>
          <div className="w-2 h-2 rounded-full bg-emerald-400 animate-pulse" title="Live" />
        </div>
        <MarketSnapshot />
      </div>

      {/* Risk Summary Row */}
      <motion.div
        initial={{ opacity: 0, y: 10 }}
        animate={{ opacity: 1, y: 0 }}
        className="glass p-4"
      >
        <div className="flex items-center justify-between">
          {/* Metrics */}
          <div className="flex items-center gap-8">
            {/* NAV */}
            <div>
              <p className="text-xs text-slate-500 uppercase tracking-wider">NAV</p>
              <p className="text-xl font-bold font-mono text-slate-100">
                {summaryLoading ? (
                  <span className="animate-pulse">Loading...</span>
                ) : (
                  formatCurrency(summary?.nav || 0)
                )}
              </p>
            </div>

            {/* Gross Exposure */}
            <div>
              <p className="text-xs text-slate-500 uppercase tracking-wider">Gross</p>
              <p className="text-xl font-bold font-mono text-slate-100">
                {summaryLoading ? (
                  <span className="animate-pulse">...</span>
                ) : (
                  formatCurrency(summary?.gross_exposure || 0)
                )}
              </p>
            </div>

            {/* Net Exposure */}
            <div>
              <p className="text-xs text-slate-500 uppercase tracking-wider">Net</p>
              <p
                className={`text-xl font-bold font-mono ${
                  (summary?.net_exposure || 0) >= 0 ? 'text-emerald-400' : 'text-rose-400'
                }`}
              >
                {summaryLoading ? (
                  <span className="animate-pulse">...</span>
                ) : (
                  formatCurrency(summary?.net_exposure || 0)
                )}
              </p>
            </div>

            {/* Long/Short */}
            <div className="flex items-center gap-4 border-l border-white/10 pl-6">
              <div>
                <p className="text-xs text-slate-500 uppercase tracking-wider">Long</p>
                <p className="text-sm font-mono text-emerald-400">
                  {formatCurrency(summary?.long_exposure || 0)}
                </p>
              </div>
              <div>
                <p className="text-xs text-slate-500 uppercase tracking-wider">Short</p>
                <p className="text-sm font-mono text-rose-400">
                  {formatCurrency(summary?.short_exposure || 0)}
                </p>
              </div>
            </div>

            {/* Counts */}
            <div className="flex items-center gap-4 border-l border-white/10 pl-6">
              <div>
                <p className="text-xs text-slate-500 uppercase tracking-wider">Positions</p>
                <p className="text-sm font-mono text-slate-300">
                  {summary?.position_count?.toLocaleString() || 0}
                </p>
              </div>
              <div>
                <p className="text-xs text-slate-500 uppercase tracking-wider">Securities</p>
                <p className="text-sm font-mono text-slate-300">
                  {summary?.security_count?.toLocaleString() || 0}
                </p>
              </div>
              <div>
                <p className="text-xs text-slate-500 uppercase tracking-wider">Books</p>
                <p className="text-sm font-mono text-slate-300">
                  {summary?.book_count || 0}
                </p>
              </div>
            </div>

            {/* Key Risk Metrics */}
            <div className="flex items-center gap-4 border-l border-white/10 pl-6">
              <div>
                <p className="text-xs text-slate-500 uppercase tracking-wider">Delta</p>
                <p className="text-sm font-mono text-slate-300">
                  {formatCurrency(summary?.total_delta || 0)}
                </p>
              </div>
              <div>
                <p className="text-xs text-slate-500 uppercase tracking-wider">DV01</p>
                <p className="text-sm font-mono text-slate-300">
                  {formatCurrency(summary?.total_dv01 || 0)}
                </p>
              </div>
              <div>
                <p className="text-xs text-slate-500 uppercase tracking-wider">CS01</p>
                <p className="text-sm font-mono text-slate-300">
                  {formatCurrency(summary?.total_cs01 || 0)}
                </p>
              </div>
            </div>
          </div>

          {/* Pricing Controls */}
          <div className="flex items-center gap-4">
            {/* Stale Warning */}
            {pricingStatus?.stale_price_count && pricingStatus.stale_price_count > 0 && (
              <div className="flex items-center gap-2 px-3 py-1 bg-amber-500/10 rounded-lg border border-amber-500/20">
                <svg className="w-4 h-4 text-amber-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    strokeWidth={2}
                    d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z"
                  />
                </svg>
                <span className="text-xs text-amber-400">
                  {pricingStatus.stale_price_count} stale
                </span>
              </div>
            )}

            {/* Last Priced */}
            <div className="text-right">
              <p className="text-xs text-slate-500">Last Priced</p>
              <p className="text-sm font-mono text-slate-300">{lastPricedTime}</p>
            </div>

            {/* Reprice Button */}
            <motion.button
              whileHover={{ scale: 1.02 }}
              whileTap={{ scale: 0.98 }}
              onClick={() => repriceMutation.mutate()}
              disabled={repricing}
              className={`px-4 py-2 rounded-lg font-medium text-sm transition-colors flex items-center gap-2
                ${
                  repricing
                    ? 'bg-slate-700 text-slate-400 cursor-not-allowed'
                    : 'bg-blue-500/20 text-blue-300 hover:bg-blue-500/30 border border-blue-500/30'
                }`}
            >
              {repricing ? (
                <>
                  <svg className="w-4 h-4 animate-spin" fill="none" viewBox="0 0 24 24">
                    <circle
                      className="opacity-25"
                      cx="12"
                      cy="12"
                      r="10"
                      stroke="currentColor"
                      strokeWidth="4"
                    />
                    <path
                      className="opacity-75"
                      fill="currentColor"
                      d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"
                    />
                  </svg>
                  Repricing...
                </>
              ) : (
                <>
                  <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path
                      strokeLinecap="round"
                      strokeLinejoin="round"
                      strokeWidth={2}
                      d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15"
                    />
                  </svg>
                  Reprice All
                </>
              )}
            </motion.button>
          </div>
        </div>
      </motion.div>
    </div>
  )
}
