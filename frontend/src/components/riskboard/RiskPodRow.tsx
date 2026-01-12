import { motion } from 'framer-motion'
import clsx from 'clsx'
import type { AssetClassRisk } from '../../types'
import AssetClassCard from './AssetClassCard'

interface RiskPodRowProps {
  data: AssetClassRisk[]
  title: string
  subtitle?: string
  bookId?: string
  bookType?: 'firm' | 'overlay' | 'trading'
  isLoading?: boolean
  onTradesClick?: (assetClass: string) => void
  variant?: 'default' | 'compact'
  showEmptyState?: boolean
}

// Animation variants for staggered children
const containerVariants = {
  hidden: { opacity: 0 },
  visible: {
    opacity: 1,
    transition: {
      staggerChildren: 0.1,
    },
  },
}

const itemVariants = {
  hidden: { opacity: 0, y: 20 },
  visible: {
    opacity: 1,
    y: 0,
    transition: { duration: 0.3 },
  },
}

// Asset class ordering for consistent display
const assetClassOrder = [
  'equity',
  'fixed_income',
  'option',
  'fx',
  'cds',
  'future',
  'swap',
]

export default function RiskPodRow({
  data,
  title,
  subtitle,
  bookId,
  bookType = 'trading',
  isLoading = false,
  onTradesClick,
  variant = 'default',
  showEmptyState = true,
}: RiskPodRowProps) {
  // Sort data by asset class order
  const sortedData = [...data].sort((a, b) => {
    const aIndex = assetClassOrder.indexOf(a.asset_class)
    const bIndex = assetClassOrder.indexOf(b.asset_class)
    // Unknown asset classes go to the end
    const aOrder = aIndex === -1 ? 999 : aIndex
    const bOrder = bIndex === -1 ? 999 : bIndex
    return aOrder - bOrder
  })

  // Loading skeleton
  if (isLoading) {
    return (
      <div className="space-y-4">
        <div className="flex items-baseline justify-between">
          <div>
            <div className="h-6 w-48 bg-slate-700/50 rounded animate-pulse" />
            {subtitle && (
              <div className="h-4 w-32 bg-slate-700/30 rounded animate-pulse mt-1" />
            )}
          </div>
        </div>
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-5 gap-4">
          {[...Array(5)].map((_, i) => (
            <div
              key={i}
              className="glass p-5 h-64 animate-pulse"
            >
              <div className="flex items-center gap-3 mb-4">
                <div className="w-9 h-9 bg-slate-700/50 rounded-lg" />
                <div>
                  <div className="h-5 w-20 bg-slate-700/50 rounded" />
                  <div className="h-3 w-16 bg-slate-700/30 rounded mt-1" />
                </div>
              </div>
              <div className="h-8 w-24 bg-slate-700/50 rounded mb-4" />
              <div className="grid grid-cols-2 gap-3 mb-4">
                <div className="h-12 bg-slate-700/30 rounded" />
                <div className="h-12 bg-slate-700/30 rounded" />
              </div>
            </div>
          ))}
        </div>
      </div>
    )
  }

  // Empty state
  if (data.length === 0 && showEmptyState) {
    return (
      <div className="space-y-4">
        <div className="flex items-baseline justify-between">
          <div>
            <h2 className="text-lg font-semibold text-slate-100">{title}</h2>
            {subtitle && (
              <p className="text-sm text-slate-500">{subtitle}</p>
            )}
          </div>
        </div>
        <div className="glass p-8 text-center">
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
              d="M20 13V6a2 2 0 00-2-2H6a2 2 0 00-2 2v7m16 0v5a2 2 0 01-2 2H6a2 2 0 01-2-2v-5m16 0h-2.586a1 1 0 00-.707.293l-2.414 2.414a1 1 0 01-.707.293h-3.172a1 1 0 01-.707-.293l-2.414-2.414A1 1 0 006.586 13H4"
            />
          </svg>
          <p className="text-slate-400">No positions in this portfolio</p>
          <p className="text-sm text-slate-500 mt-1">
            Add trades to see risk metrics by asset class
          </p>
        </div>
      </div>
    )
  }

  return (
    <div className="space-y-4">
      {/* Row Header */}
      <div className="flex items-baseline justify-between">
        <div>
          <h2 className={clsx(
            'font-semibold text-slate-100',
            variant === 'compact' ? 'text-base' : 'text-lg'
          )}>
            {title}
          </h2>
          {subtitle && (
            <p className="text-sm text-slate-500">{subtitle}</p>
          )}
        </div>
        {/* Optional: Could add summary metrics here */}
        <div className="flex items-center gap-4 text-sm text-slate-400">
          <span>{sortedData.length} asset classes</span>
          <span className="text-slate-600">|</span>
          <span>
            {sortedData.reduce((sum, d) => sum + d.position_count, 0)} positions
          </span>
        </div>
      </div>

      {/* Asset Class Cards Grid */}
      <motion.div
        variants={containerVariants}
        initial="hidden"
        animate="visible"
        className={clsx(
          'grid gap-4',
          variant === 'compact'
            ? 'grid-cols-1 md:grid-cols-2 lg:grid-cols-4 xl:grid-cols-6'
            : 'grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-5'
        )}
      >
        {sortedData.map((assetData) => (
          <motion.div key={assetData.asset_class} variants={itemVariants}>
            <AssetClassCard
              data={assetData}
              bookId={bookId}
              bookType={bookType}
              variant={variant}
              onTradesClick={
                onTradesClick
                  ? () => onTradesClick(assetData.asset_class)
                  : undefined
              }
            />
          </motion.div>
        ))}
      </motion.div>
    </div>
  )
}
