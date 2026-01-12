import { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { motion } from 'framer-motion'
import clsx from 'clsx'
import { valuationApi } from '../../services/api'

interface ValuationModalProps {
  tradeId: string
  securityName: string
  ticker: string
  onClose: () => void
}

// Format input value for display
function formatInputValue(key: string, value: number): string {
  switch (key) {
    case 'spot':
    case 'strike':
    case 'price':
      return `$${value.toFixed(2)}`
    case 'vol':
    case 'volatility':
    case 'rate':
    case 'dividend_yield':
      return `${(value * 100).toFixed(2)}%`
    case 'time_to_expiry':
      return `${value.toFixed(4)} yrs`
    default:
      return value.toFixed(4)
  }
}

// Human-readable input names
const inputLabels: Record<string, string> = {
  spot: 'Spot Price',
  strike: 'Strike Price',
  vol: 'Implied Volatility',
  volatility: 'Volatility',
  rate: 'Risk-Free Rate',
  dividend_yield: 'Dividend Yield',
  time_to_expiry: 'Time to Expiry',
  recovery_rate: 'Recovery Rate',
  spread: 'Credit Spread',
}

export default function ValuationModal({
  tradeId,
  securityName,
  ticker,
  onClose,
}: ValuationModalProps) {
  const queryClient = useQueryClient()

  // Override form state
  const [showOverrideForm, setShowOverrideForm] = useState(false)
  const [overrideInputs, setOverrideInputs] = useState<Record<string, number>>({})
  const [overrideReason, setOverrideReason] = useState('')

  // Fetch valuation details
  const {
    data: valuation,
    isLoading,
    error,
  } = useQuery({
    queryKey: ['valuation', tradeId],
    queryFn: () => valuationApi.getPositionValuation(tradeId),
  })

  // Override mutation
  const overrideMutation = useMutation({
    mutationFn: () =>
      valuationApi.overrideModelInputs(tradeId, overrideInputs, overrideReason),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['valuation', tradeId] })
      setShowOverrideForm(false)
      setOverrideInputs({})
      setOverrideReason('')
    },
  })

  // Initialize override inputs from current model inputs
  const handleStartOverride = () => {
    if (valuation?.model_inputs) {
      setOverrideInputs({ ...valuation.model_inputs })
    }
    setShowOverrideForm(true)
  }

  // Handle input change
  const handleInputChange = (key: string, value: string) => {
    const numValue = parseFloat(value)
    if (!isNaN(numValue)) {
      setOverrideInputs((prev) => ({ ...prev, [key]: numValue }))
    }
  }

  // Price source badge
  const getPriceSourceBadge = (source: string) => {
    switch (source) {
      case 'market':
        return { label: 'Market Price', color: 'bg-emerald-500/20 text-emerald-400', icon: '📊' }
      case 'model':
        return { label: 'Model Derived', color: 'bg-blue-500/20 text-blue-400', icon: '🔬' }
      case 'manual':
        return { label: 'Manual Override', color: 'bg-amber-500/20 text-amber-400', icon: '✏️' }
      case 'stale':
        return { label: 'Stale Price', color: 'bg-red-500/20 text-red-400', icon: '⚠️' }
      default:
        return { label: source, color: 'bg-slate-500/20 text-slate-400', icon: '❓' }
    }
  }

  return (
    <motion.div
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      exit={{ opacity: 0 }}
      className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/60 backdrop-blur-sm"
      onClick={onClose}
    >
      <motion.div
        initial={{ scale: 0.95, opacity: 0 }}
        animate={{ scale: 1, opacity: 1 }}
        exit={{ scale: 0.95, opacity: 0 }}
        transition={{ type: 'spring', damping: 25, stiffness: 300 }}
        onClick={(e) => e.stopPropagation()}
        className="w-full max-w-2xl glass border border-white/10 rounded-xl shadow-2xl overflow-hidden"
      >
        {/* Header */}
        <div className="flex items-center justify-between px-6 py-4 border-b border-white/5">
          <div>
            <h2 className="text-lg font-semibold text-slate-100">Valuation Details</h2>
            <p className="text-sm text-slate-500">
              {ticker} - {securityName}
            </p>
          </div>
          <button
            onClick={onClose}
            className="p-2 text-slate-400 hover:text-slate-200 hover:bg-white/5 rounded-lg transition-colors"
          >
            <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>
        </div>

        {/* Content */}
        <div className="p-6 max-h-[70vh] overflow-y-auto">
          {/* Loading State */}
          {isLoading && (
            <div className="text-center py-8">
              <div className="animate-spin w-8 h-8 border-2 border-blue-500 border-t-transparent rounded-full mx-auto mb-4" />
              <p className="text-slate-400">Loading valuation data...</p>
            </div>
          )}

          {/* Error State */}
          {error && (
            <div className="text-center py-8">
              <svg className="w-12 h-12 text-red-400 mx-auto mb-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
              </svg>
              <p className="text-red-400">Failed to load valuation</p>
            </div>
          )}

          {/* Valuation Content */}
          {valuation && (
            <div className="space-y-6">
              {/* Price Source Section */}
              <div>
                <h3 className="text-xs font-medium text-slate-500 uppercase tracking-wider mb-3">
                  Price Source
                </h3>
                <div className="flex items-center justify-between p-4 bg-slate-800/30 rounded-lg">
                  <div className="flex items-center gap-3">
                    <span className="text-2xl">{getPriceSourceBadge(valuation.price_source).icon}</span>
                    <div>
                      <span className={clsx(
                        'inline-block px-3 py-1 rounded-full text-sm font-medium',
                        getPriceSourceBadge(valuation.price_source).color
                      )}>
                        {getPriceSourceBadge(valuation.price_source).label}
                      </span>
                      <p className="text-xs text-slate-500 mt-1">
                        As of {new Date(valuation.price_as_of).toLocaleString()}
                      </p>
                    </div>
                  </div>
                  <div className="text-right">
                    <p className="text-2xl font-bold font-mono text-slate-100">
                      ${valuation.current_price.toFixed(2)}
                    </p>
                  </div>
                </div>
              </div>

              {/* Model Details (if model-derived) */}
              {valuation.model_name && (
                <div>
                  <h3 className="text-xs font-medium text-slate-500 uppercase tracking-wider mb-3">
                    Model Information
                  </h3>
                  <div className="p-4 bg-slate-800/30 rounded-lg space-y-4">
                    <div className="flex items-center justify-between">
                      <span className="text-slate-400">Model</span>
                      <span className="text-slate-100 font-medium">{valuation.model_name}</span>
                    </div>
                    {valuation.model_version && (
                      <div className="flex items-center justify-between">
                        <span className="text-slate-400">Version</span>
                        <span className="text-slate-300">{valuation.model_version}</span>
                      </div>
                    )}
                    {valuation.model_output !== undefined && (
                      <div className="flex items-center justify-between">
                        <span className="text-slate-400">Model Output</span>
                        <span className="text-slate-100 font-mono">${valuation.model_output.toFixed(4)}</span>
                      </div>
                    )}
                  </div>
                </div>
              )}

              {/* Model Inputs */}
              {valuation.model_inputs && Object.keys(valuation.model_inputs).length > 0 && (
                <div>
                  <div className="flex items-center justify-between mb-3">
                    <h3 className="text-xs font-medium text-slate-500 uppercase tracking-wider">
                      Model Inputs
                    </h3>
                    {valuation.can_override && !showOverrideForm && (
                      <button
                        onClick={handleStartOverride}
                        className="text-xs text-blue-400 hover:text-blue-300 font-medium transition-colors"
                      >
                        Override Inputs
                      </button>
                    )}
                  </div>

                  {!showOverrideForm ? (
                    <div className="grid grid-cols-2 gap-3">
                      {Object.entries(valuation.model_inputs).map(([key, value]) => (
                        <div key={key} className="p-3 bg-slate-800/30 rounded-lg">
                          <p className="text-xs text-slate-500 mb-1">
                            {inputLabels[key] || key}
                          </p>
                          <p className="font-mono text-slate-100">
                            {formatInputValue(key, value as number)}
                          </p>
                        </div>
                      ))}
                    </div>
                  ) : (
                    /* Override Form */
                    <div className="space-y-4">
                      <div className="grid grid-cols-2 gap-3">
                        {Object.entries(overrideInputs).map(([key, value]) => (
                          <div key={key}>
                            <label className="block text-xs text-slate-500 mb-1">
                              {inputLabels[key] || key}
                            </label>
                            <input
                              type="number"
                              value={value}
                              onChange={(e) => handleInputChange(key, e.target.value)}
                              step="0.0001"
                              className="w-full px-3 py-2 bg-slate-800/50 border border-white/10 rounded-lg
                                       text-slate-100 font-mono text-sm
                                       focus:outline-none focus:border-blue-500/50 focus:ring-1 focus:ring-blue-500/20"
                            />
                          </div>
                        ))}
                      </div>
                      <div>
                        <label className="block text-xs text-slate-500 mb-1">
                          Override Reason
                        </label>
                        <textarea
                          value={overrideReason}
                          onChange={(e) => setOverrideReason(e.target.value)}
                          rows={2}
                          placeholder="Enter reason for override..."
                          className="w-full px-3 py-2 bg-slate-800/50 border border-white/10 rounded-lg
                                   text-slate-100 text-sm placeholder-slate-500
                                   focus:outline-none focus:border-blue-500/50 focus:ring-1 focus:ring-blue-500/20"
                        />
                      </div>
                      <div className="flex items-center gap-3">
                        <button
                          onClick={() => overrideMutation.mutate()}
                          disabled={!overrideReason.trim() || overrideMutation.isPending}
                          className="px-4 py-2 bg-blue-500 hover:bg-blue-600 text-white text-sm font-medium
                                   rounded-lg transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
                        >
                          {overrideMutation.isPending ? 'Saving...' : 'Save Override'}
                        </button>
                        <button
                          onClick={() => {
                            setShowOverrideForm(false)
                            setOverrideInputs({})
                            setOverrideReason('')
                          }}
                          className="px-4 py-2 text-slate-400 hover:text-slate-200 text-sm font-medium
                                   transition-colors"
                        >
                          Cancel
                        </button>
                      </div>
                    </div>
                  )}
                </div>
              )}

              {/* Override History */}
              {valuation.has_override && valuation.override_inputs && (
                <div>
                  <h3 className="text-xs font-medium text-slate-500 uppercase tracking-wider mb-3">
                    Current Override
                  </h3>
                  <div className="p-4 bg-amber-500/10 border border-amber-500/20 rounded-lg">
                    <div className="flex items-start gap-3">
                      <svg className="w-5 h-5 text-amber-400 flex-shrink-0 mt-0.5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
                      </svg>
                      <div className="flex-1">
                        <p className="text-sm text-amber-300 font-medium">Manual Override Active</p>
                        {valuation.override_reason && (
                          <p className="text-sm text-slate-400 mt-1">
                            Reason: {valuation.override_reason}
                          </p>
                        )}
                        <p className="text-xs text-slate-500 mt-2">
                          {valuation.override_by && `By ${valuation.override_by} • `}
                          {valuation.override_at && new Date(valuation.override_at).toLocaleString()}
                        </p>
                        <div className="grid grid-cols-2 gap-2 mt-3">
                          {Object.entries(valuation.override_inputs).map(([key, value]) => (
                            <div key={key} className="text-xs">
                              <span className="text-slate-500">{inputLabels[key] || key}:</span>{' '}
                              <span className="text-amber-300 font-mono">
                                {formatInputValue(key, value as number)}
                              </span>
                            </div>
                          ))}
                        </div>
                      </div>
                    </div>
                  </div>
                </div>
              )}
            </div>
          )}
        </div>

        {/* Footer */}
        <div className="flex items-center justify-end px-6 py-4 border-t border-white/5 bg-slate-900/50">
          <button
            onClick={onClose}
            className="px-4 py-2 text-sm text-slate-400 hover:text-slate-200
                     bg-white/5 hover:bg-white/10 rounded-lg transition-all"
          >
            Close
          </button>
        </div>
      </motion.div>
    </motion.div>
  )
}
