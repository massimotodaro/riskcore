import { useState } from 'react'
import { motion } from 'framer-motion'
import clsx from 'clsx'
import { formatCurrency } from '../../services/api'
import type { HistoricalPosition } from '../../types'

interface RepricingModalProps {
  position: HistoricalPosition
  onClose: () => void
  onSave: (price: number) => void
}

export default function RepricingModal({
  position,
  onClose,
  onSave,
}: RepricingModalProps) {
  const [newPrice, setNewPrice] = useState(position.price.toString())
  const [reason, setReason] = useState('')
  const [isSubmitting, setIsSubmitting] = useState(false)

  const priceNum = parseFloat(newPrice)
  const isValid = !isNaN(priceNum) && priceNum > 0
  const priceChange = isValid ? ((priceNum - position.price) / position.price) * 100 : 0
  const newMarketValue = isValid ? position.quantity * priceNum : position.market_value

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!isValid) return

    setIsSubmitting(true)
    try {
      await onSave(priceNum)
    } finally {
      setIsSubmitting(false)
    }
  }

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center">
      {/* Backdrop */}
      <motion.div
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        exit={{ opacity: 0 }}
        className="absolute inset-0 bg-black/60 backdrop-blur-sm"
        onClick={onClose}
      />

      {/* Modal */}
      <motion.div
        initial={{ opacity: 0, scale: 0.95 }}
        animate={{ opacity: 1, scale: 1 }}
        exit={{ opacity: 0, scale: 0.95 }}
        className="relative w-full max-w-md glass rounded-xl border border-white/10 shadow-2xl"
      >
        {/* Header */}
        <div className="px-6 py-4 border-b border-white/10">
          <div className="flex items-center justify-between">
            <h3 className="text-lg font-semibold text-white">Manual Reprice</h3>
            <button
              onClick={onClose}
              className="p-1 hover:bg-white/10 rounded transition-colors"
            >
              <svg
                className="w-5 h-5 text-slate-400"
                fill="none"
                viewBox="0 0 24 24"
                stroke="currentColor"
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={1.5}
                  d="M6 18L18 6M6 6l12 12"
                />
              </svg>
            </button>
          </div>
        </div>

        {/* Content */}
        <form onSubmit={handleSubmit} className="p-6 space-y-4">
          {/* Security info */}
          <div className="space-y-2">
            <div className="text-sm text-slate-400">Security</div>
            <div className="flex items-center justify-between">
              <div>
                <div className="font-medium text-white">
                  {position.ticker || position.security_name?.slice(0, 10)}
                </div>
                <div className="text-xs text-slate-500">{position.security_name}</div>
              </div>
              <div className="text-right">
                <div className="text-xs text-slate-500">Quantity</div>
                <div className="text-sm text-white font-mono">
                  {position.quantity.toLocaleString()}
                </div>
              </div>
            </div>
          </div>

          {/* Current price */}
          <div className="flex items-center justify-between p-3 rounded-lg bg-white/5 border border-white/10">
            <div>
              <div className="text-xs text-slate-500">Current Price</div>
              <div className="text-lg font-medium text-white">
                ${position.price.toFixed(2)}
              </div>
            </div>
            <div className={clsx(
              'px-2 py-1 rounded text-xs font-medium',
              position.price_source === 'market' && 'bg-emerald-500/20 text-emerald-300',
              position.price_source === 'manual' && 'bg-amber-500/20 text-amber-300',
              position.price_source === 'model' && 'bg-blue-500/20 text-blue-300',
              (!position.price_source || position.price_source === 'stale') && 'bg-red-500/20 text-red-300'
            )}>
              {position.price_source?.toUpperCase() || 'UNKNOWN'}
            </div>
          </div>

          {/* New price input */}
          <div className="space-y-2">
            <label className="text-sm text-slate-400">New Price</label>
            <div className="relative">
              <span className="absolute left-3 top-1/2 -translate-y-1/2 text-slate-400">$</span>
              <input
                type="number"
                step="0.01"
                value={newPrice}
                onChange={(e) => setNewPrice(e.target.value)}
                className={clsx(
                  'w-full pl-7 pr-4 py-3 rounded-lg',
                  'bg-white/5 border transition-colors',
                  'text-white text-lg font-medium',
                  'focus:outline-none focus:ring-2 focus:ring-blue-500',
                  isValid ? 'border-white/10' : 'border-red-500/50'
                )}
                placeholder="0.00"
                autoFocus
              />
            </div>

            {/* Price change indicator */}
            {isValid && priceChange !== 0 && (
              <div className={clsx(
                'flex items-center gap-2 text-sm',
                priceChange > 0 ? 'text-emerald-400' : 'text-red-400'
              )}>
                <span>{priceChange > 0 ? '+' : ''}{priceChange.toFixed(2)}%</span>
                <span className="text-slate-500">|</span>
                <span>New MV: {formatCurrency(newMarketValue)}</span>
              </div>
            )}
          </div>

          {/* Reason (optional) */}
          <div className="space-y-2">
            <label className="text-sm text-slate-400">Reason (optional)</label>
            <textarea
              value={reason}
              onChange={(e) => setReason(e.target.value)}
              className={clsx(
                'w-full px-4 py-2 rounded-lg',
                'bg-white/5 border border-white/10',
                'text-white text-sm',
                'focus:outline-none focus:ring-2 focus:ring-blue-500',
                'resize-none'
              )}
              rows={2}
              placeholder="E.g., Broker quote, market data correction..."
            />
          </div>

          {/* Actions */}
          <div className="flex items-center gap-3 pt-2">
            <button
              type="button"
              onClick={onClose}
              className="flex-1 px-4 py-2.5 rounded-lg border border-white/10 text-slate-300 hover:bg-white/5 transition-colors"
            >
              Cancel
            </button>
            <button
              type="submit"
              disabled={!isValid || isSubmitting}
              className={clsx(
                'flex-1 px-4 py-2.5 rounded-lg font-medium transition-colors',
                isValid && !isSubmitting
                  ? 'bg-blue-500 hover:bg-blue-600 text-white'
                  : 'bg-white/5 text-slate-500 cursor-not-allowed'
              )}
            >
              {isSubmitting ? 'Saving...' : 'Save Price'}
            </button>
          </div>
        </form>
      </motion.div>
    </div>
  )
}
