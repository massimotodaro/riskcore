import { useQuery } from '@tanstack/react-query'
import { motion } from 'framer-motion'
import { riskboardApi, formatCurrency } from '../../services/api'

interface CorrelationPanelProps {
  tenantId?: string
  bookIds?: string[]
}

export default function CorrelationPanel({ tenantId, bookIds }: CorrelationPanelProps) {
  // Fetch position overlap
  const { data: overlaps, isLoading: overlapsLoading } = useQuery({
    queryKey: ['positionOverlap', tenantId, bookIds],
    queryFn: () => riskboardApi.getPositionOverlap(tenantId, bookIds),
  })

  // Fetch sector concentration
  const { data: sectorConcentration, isLoading: sectorLoading } = useQuery({
    queryKey: ['sectorConcentration', tenantId, bookIds],
    queryFn: () => riskboardApi.getConcentrationBySector(tenantId, bookIds),
  })

  // Fetch security concentration
  const { data: securityConcentration, isLoading: securityLoading } = useQuery({
    queryKey: ['securityConcentration', tenantId, bookIds],
    queryFn: () => riskboardApi.getConcentrationBySecurity(tenantId, bookIds, 10),
  })

  // Calculate netting stats
  const totalNettingOpportunity =
    overlaps?.reduce((sum, o) => sum + o.netting_opportunity, 0) || 0
  const overlappingSecurities = overlaps?.length || 0

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      className="glass p-6"
    >
      <h3 className="text-lg font-semibold text-slate-100 mb-6">
        Correlation & Concentration Analysis
      </h3>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Position Overlap */}
        <div>
          <h4 className="text-sm font-medium text-slate-400 uppercase tracking-wider mb-4">
            Position Overlap
          </h4>

          {overlapsLoading ? (
            <div className="animate-pulse space-y-3">
              {[1, 2, 3].map((i) => (
                <div key={i} className="h-12 bg-slate-800 rounded" />
              ))}
            </div>
          ) : overlaps && overlaps.length > 0 ? (
            <div className="space-y-2">
              {/* Summary Stats */}
              <div className="flex items-center justify-between p-3 bg-slate-800/50 rounded-lg mb-4">
                <div>
                  <p className="text-xs text-slate-500">Securities in Common</p>
                  <p className="text-lg font-mono text-slate-100">{overlappingSecurities}</p>
                </div>
                <div className="text-right">
                  <p className="text-xs text-slate-500">Netting Opportunity</p>
                  <p className="text-lg font-mono text-emerald-400">
                    {formatCurrency(totalNettingOpportunity)}
                  </p>
                </div>
              </div>

              {/* Top Overlaps */}
              <div className="space-y-2 max-h-60 overflow-y-auto">
                {overlaps.slice(0, 8).map((overlap) => (
                  <div
                    key={overlap.security_id}
                    className="flex items-center justify-between p-2 bg-slate-800/30 rounded"
                  >
                    <div>
                      <p className="text-sm font-medium text-slate-200">
                        {overlap.ticker || overlap.security_name.substring(0, 15)}
                      </p>
                      <p className="text-xs text-slate-500">
                        {overlap.book_count} books
                      </p>
                    </div>
                    <div className="text-right">
                      <p className="text-sm font-mono text-emerald-400">
                        +{formatCurrency(overlap.netting_opportunity)}
                      </p>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          ) : (
            <div className="text-center py-8 text-slate-500">
              <p>No overlapping positions</p>
              <p className="text-xs mt-1">Select books with shared holdings</p>
            </div>
          )}
        </div>

        {/* Sector Concentration */}
        <div>
          <h4 className="text-sm font-medium text-slate-400 uppercase tracking-wider mb-4">
            Sector Concentration
          </h4>

          {sectorLoading ? (
            <div className="animate-pulse space-y-3">
              {[1, 2, 3, 4].map((i) => (
                <div key={i} className="h-8 bg-slate-800 rounded" />
              ))}
            </div>
          ) : sectorConcentration && sectorConcentration.length > 0 ? (
            <div className="space-y-3">
              {sectorConcentration.slice(0, 6).map((item) => (
                <div key={item.sector} className="space-y-1">
                  <div className="flex items-center justify-between">
                    <span className="text-sm text-slate-300">{item.sector}</span>
                    <div className="flex items-center gap-2">
                      <span
                        className={`text-sm font-mono ${
                          item.is_warning ? 'text-amber-400' : 'text-slate-400'
                        }`}
                      >
                        {item.percentage.toFixed(1)}%
                      </span>
                      {item.is_warning && (
                        <svg
                          className="w-4 h-4 text-amber-400"
                          fill="none"
                          viewBox="0 0 24 24"
                          stroke="currentColor"
                        >
                          <path
                            strokeLinecap="round"
                            strokeLinejoin="round"
                            strokeWidth={2}
                            d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z"
                          />
                        </svg>
                      )}
                    </div>
                  </div>
                  <div className="h-2 bg-slate-800 rounded-full overflow-hidden">
                    <motion.div
                      initial={{ width: 0 }}
                      animate={{ width: `${Math.min(item.percentage, 100)}%` }}
                      transition={{ duration: 0.5 }}
                      className={`h-full ${
                        item.is_warning
                          ? 'bg-gradient-to-r from-amber-500 to-amber-400'
                          : 'bg-gradient-to-r from-blue-500 to-cyan-500'
                      }`}
                    />
                  </div>
                </div>
              ))}
            </div>
          ) : (
            <div className="text-center py-8 text-slate-500">
              <p>No sector data available</p>
            </div>
          )}
        </div>

        {/* Single-Name Concentration */}
        <div>
          <h4 className="text-sm font-medium text-slate-400 uppercase tracking-wider mb-4">
            Top Single Names
          </h4>

          {securityLoading ? (
            <div className="animate-pulse space-y-3">
              {[1, 2, 3, 4, 5].map((i) => (
                <div key={i} className="h-8 bg-slate-800 rounded" />
              ))}
            </div>
          ) : securityConcentration && securityConcentration.length > 0 ? (
            <div className="space-y-2">
              {securityConcentration.map((item, i) => (
                <div
                  key={item.security_id}
                  className={`flex items-center justify-between p-2 rounded ${
                    item.is_warning ? 'bg-amber-500/10 border border-amber-500/20' : 'bg-slate-800/30'
                  }`}
                >
                  <div className="flex items-center gap-2">
                    <span className="text-xs text-slate-500 w-4">{i + 1}.</span>
                    <div>
                      <p className="text-sm font-medium text-slate-200">
                        {item.ticker || item.security_name?.substring(0, 12)}
                      </p>
                      <p className="text-xs text-slate-500">{item.asset_class}</p>
                    </div>
                  </div>
                  <div className="text-right">
                    <p
                      className={`text-sm font-mono ${
                        item.is_warning ? 'text-amber-400' : 'text-slate-300'
                      }`}
                    >
                      {item.percentage.toFixed(1)}%
                    </p>
                    <p className="text-xs text-slate-500">
                      {formatCurrency(item.gross_exposure)}
                    </p>
                  </div>
                </div>
              ))}
            </div>
          ) : (
            <div className="text-center py-8 text-slate-500">
              <p>No concentration data</p>
            </div>
          )}
        </div>
      </div>

      {/* Footer with thresholds */}
      <div className="mt-6 pt-4 border-t border-white/5 flex items-center justify-between text-xs text-slate-500">
        <div className="flex items-center gap-4">
          <span>Sector Warning: &gt;40%</span>
          <span>Single-Name Warning: &gt;10%</span>
        </div>
        <span>
          {overlappingSecurities > 0 && (
            <span className="text-emerald-400">
              Potential savings from netting: {formatCurrency(totalNettingOpportunity)}
            </span>
          )}
        </span>
      </div>
    </motion.div>
  )
}
