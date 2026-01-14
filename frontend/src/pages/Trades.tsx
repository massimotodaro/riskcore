import { useState, useEffect } from 'react'
import { useSearchParams } from 'react-router-dom'
import { useQuery } from '@tanstack/react-query'
import { motion } from 'framer-motion'
import clsx from 'clsx'
import { riskboardApi, tradesPageApi, formatCurrency, formatQuantity, RISKPOD_CONFIG } from '../services/api'
import TimeSelector from '../components/common/TimeSelector'
import AssetClassFilter from '../components/common/AssetClassFilter'
import PositionTable from '../components/trades/PositionTable'
import RepricingModal from '../components/trades/RepricingModal'
import type { RiskPodType, HistoricalPosition, RiskPodPositions } from '../types'

const DEFAULT_TENANT_ID = 'b95fbd3b-e6f0-41f8-9c0c-5337e469cf50'

export default function Trades() {
  const [searchParams, setSearchParams] = useSearchParams()

  // URL state
  const initialBooks = searchParams.get('books')?.split(',').filter(Boolean) || []
  const initialTime = searchParams.get('time') || null
  const initialAssets = (searchParams.get('asset')?.split(',').filter(Boolean) as RiskPodType[]) || ['equity', 'rates', 'credit', 'fx', 'other']

  // Local state
  const [selectedBooks, setSelectedBooks] = useState<string[]>(initialBooks)
  const [timeSelection, setTimeSelection] = useState<string | null>(initialTime)
  const [assetFilter, setAssetFilter] = useState<RiskPodType[]>(initialAssets)
  const [repricingPosition, setRepricingPosition] = useState<HistoricalPosition | null>(null)

  // Fetch books for selector
  const { data: books = [] } = useQuery({
    queryKey: ['books'],
    queryFn: () => riskboardApi.getBooks(DEFAULT_TENANT_ID),
    staleTime: 60000,
  })

  // Auto-select first book if none selected
  useEffect(() => {
    if (books.length > 0 && selectedBooks.length === 0) {
      setSelectedBooks([books[0].book_id])
    }
  }, [books])

  // Fetch positions by RiskPod
  const { data: riskpodData, isLoading, error } = useQuery({
    queryKey: ['positions-by-riskpod', selectedBooks, timeSelection],
    queryFn: () => tradesPageApi.getPositionsByRiskPod(selectedBooks, timeSelection || undefined),
    enabled: selectedBooks.length > 0,
    staleTime: 30000,
  })

  // Update URL when state changes
  useEffect(() => {
    const params = new URLSearchParams()
    if (selectedBooks.length > 0) params.set('books', selectedBooks.join(','))
    if (timeSelection) params.set('time', timeSelection)
    if (assetFilter.length < 5) params.set('asset', assetFilter.join(','))
    setSearchParams(params, { replace: true })
  }, [selectedBooks, timeSelection, assetFilter])

  const handleBookToggle = (bookId: string) => {
    setSelectedBooks((prev) =>
      prev.includes(bookId)
        ? prev.filter((id) => id !== bookId)
        : [...prev, bookId]
    )
  }

  const handleReprice = (position: HistoricalPosition) => {
    setRepricingPosition(position)
  }

  return (
    <div className="h-full flex flex-col">
      {/* Header with selectors */}
      <header className="flex-shrink-0 px-6 py-4 border-b border-white/5">
        <div className="flex items-center justify-between mb-4">
          <div className="flex items-center gap-4">
            <h1 className="text-2xl font-bold gradient-text">Trades</h1>
            <TimeSelector
              value={timeSelection}
              onChange={setTimeSelection}
              tenantId={DEFAULT_TENANT_ID}
            />
          </div>

          <div className="flex items-center gap-2">
            {/* Book Selector Pills */}
            <div className="flex items-center gap-1.5 px-2 py-1 rounded-lg bg-white/5 border border-white/10">
              <span className="text-xs text-slate-500 px-2">Books:</span>
              {books.slice(0, 6).map((book) => (
                <button
                  key={book.book_id}
                  onClick={() => handleBookToggle(book.book_id)}
                  className={clsx(
                    'px-2 py-1 rounded text-xs font-medium transition-colors',
                    selectedBooks.includes(book.book_id)
                      ? 'bg-blue-500/20 text-blue-300 border border-blue-500/30'
                      : 'text-slate-400 hover:text-white hover:bg-white/5'
                  )}
                >
                  {book.name}
                </button>
              ))}
              {books.length > 6 && (
                <span className="text-xs text-slate-500 px-1">
                  +{books.length - 6}
                </span>
              )}
            </div>
          </div>
        </div>

        {/* Asset Class Filter */}
        <AssetClassFilter
          selected={assetFilter}
          onChange={setAssetFilter}
        />
      </header>

      {/* Main content - 5 RiskPod tables */}
      <main className="flex-1 overflow-y-auto px-6 py-4">
        {isLoading ? (
          <div className="flex items-center justify-center h-64">
            <div className="text-slate-500">Loading positions...</div>
          </div>
        ) : error ? (
          <div className="flex items-center justify-center h-64">
            <div className="text-red-400">Error loading positions</div>
          </div>
        ) : selectedBooks.length === 0 ? (
          <div className="flex items-center justify-center h-64">
            <div className="text-slate-500">Select at least one book to view positions</div>
          </div>
        ) : (
          <div className="space-y-6">
            {/* Render tables for each selected asset class */}
            {assetFilter.map((pod) => {
              const podData = riskpodData?.[pod]
              const config = RISKPOD_CONFIG[pod]

              if (!podData || podData.position_count === 0) {
                return (
                  <motion.div
                    key={pod}
                    initial={{ opacity: 0, y: 20 }}
                    animate={{ opacity: 1, y: 0 }}
                    className="glass rounded-xl p-4"
                  >
                    <div className="flex items-center justify-between mb-3">
                      <h3 className="text-lg font-semibold text-white">{config.label}</h3>
                      <span className="text-sm text-slate-500">0 positions</span>
                    </div>
                    <div className="text-center py-8 text-slate-500">
                      No {config.label.toLowerCase()} positions
                    </div>
                  </motion.div>
                )
              }

              return (
                <motion.div
                  key={pod}
                  initial={{ opacity: 0, y: 20 }}
                  animate={{ opacity: 1, y: 0 }}
                  className="glass rounded-xl overflow-hidden"
                >
                  {/* Table header */}
                  <div className="px-4 py-3 border-b border-white/5 flex items-center justify-between">
                    <div className="flex items-center gap-3">
                      <h3 className="text-lg font-semibold text-white">{config.label}</h3>
                      <span className="text-sm text-slate-500">
                        {podData.position_count} positions
                      </span>
                    </div>
                    <div className="flex items-center gap-4 text-sm">
                      <div>
                        <span className="text-slate-500">Gross: </span>
                        <span className="text-white font-medium">
                          {formatCurrency(podData.gross_exposure)}
                        </span>
                      </div>
                      <div>
                        <span className="text-slate-500">Net: </span>
                        <span className={clsx(
                          'font-medium',
                          podData.net_exposure >= 0 ? 'text-emerald-400' : 'text-red-400'
                        )}>
                          {formatCurrency(podData.net_exposure)}
                        </span>
                      </div>
                      <div>
                        <span className="text-slate-500">{config.primaryMetricLabel}: </span>
                        <span className="text-white font-medium">
                          {formatQuantity(podData[`total_${config.primaryMetric}` as keyof RiskPodPositions] as number || 0)}
                        </span>
                      </div>
                    </div>
                  </div>

                  {/* Position table */}
                  <PositionTable
                    positions={podData.positions}
                    riskpod={pod}
                    onReprice={handleReprice}
                  />
                </motion.div>
              )
            })}
          </div>
        )}
      </main>

      {/* Repricing Modal */}
      {repricingPosition && (
        <RepricingModal
          position={repricingPosition}
          onClose={() => setRepricingPosition(null)}
          onSave={(price) => {
            console.log('Saving price:', price, 'for:', repricingPosition.security_id)
            setRepricingPosition(null)
          }}
        />
      )}
    </div>
  )
}
