import { useState, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import { useQuery } from '@tanstack/react-query'
import { motion } from 'framer-motion'
import TopBar from '../components/riskboard/TopBar'
import RiskPodRow from '../components/riskboard/RiskPodRow'
import PortfolioSelector from '../components/riskboard/PortfolioSelector'
import CorrelationPanel from '../components/riskboard/CorrelationPanel'
import {
  riskboardApi,
  formatCurrency,
} from '../services/api'
import type { Book } from '../types'

// Default tenant ID for development (from mock data generator)
const DEFAULT_TENANT_ID = 'b95fbd3b-e6f0-41f8-9c0c-5337e469cf50'

interface RiskPodState {
  id: string
  selectedBookIds: string[]
}

export default function Riskboard() {
  const navigate = useNavigate()

  // RiskPod states - dynamic array
  const [riskPods, setRiskPods] = useState<RiskPodState[]>([
    { id: 'pod-1', selectedBookIds: [] }, // First pod (cannot be deleted)
  ])

  // Selected books for correlation panel
  const [selectedBooksForCorrelation, setSelectedBooksForCorrelation] = useState<string[]>([])

  // Fetch all books for portfolio selector
  const { data: allBooks } = useQuery({
    queryKey: ['books'],
    queryFn: () => riskboardApi.getBooks(DEFAULT_TENANT_ID),
  })

  // Fetch trading books only
  const { data: tradingBooks } = useQuery({
    queryKey: ['tradingBooks'],
    queryFn: () => riskboardApi.getBooks(DEFAULT_TENANT_ID, 'trading'),
  })

  // Fetch overlay books
  const { data: overlayBooks } = useQuery({
    queryKey: ['overlayBooks'],
    queryFn: () => riskboardApi.getBooks(DEFAULT_TENANT_ID, 'overlay'),
  })

  // Auto-select all books for the first pod
  useEffect(() => {
    if (allBooks && allBooks.length > 0 && riskPods[0].selectedBookIds.length === 0) {
      setRiskPods((prev) => [
        { ...prev[0], selectedBookIds: allBooks.map((b) => b.book_id) },
        ...prev.slice(1),
      ])
    }
  }, [allBooks])

  // Update selected books for correlation when pods change
  useEffect(() => {
    const allSelectedIds = riskPods.flatMap((pod) => pod.selectedBookIds)
    setSelectedBooksForCorrelation([...new Set(allSelectedIds)])
  }, [riskPods])

  // Add a new RiskPod
  const addRiskPod = () => {
    setRiskPods((prev) => [
      ...prev,
      { id: `pod-${Date.now()}`, selectedBookIds: [] },
    ])
  }

  // Delete a RiskPod (cannot delete the first one)
  const deleteRiskPod = (podId: string) => {
    if (riskPods.length > 1 && podId !== riskPods[0].id) {
      setRiskPods((prev) => prev.filter((p) => p.id !== podId))
    }
  }

  // Update selected books for a RiskPod
  const updatePodBooks = (podId: string, bookIds: string[]) => {
    setRiskPods((prev) =>
      prev.map((p) => (p.id === podId ? { ...p, selectedBookIds: bookIds } : p))
    )
  }

  // Handle trades click - navigate to positions drill-down
  const handleTradesClick = (bookIds: string[], assetClass: string) => {
    if (bookIds.length > 0) {
      navigate(`/trades/${bookIds.join(',')}/${assetClass}`)
    }
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-950 via-slate-900 to-slate-950">
      <div className="max-w-[1900px] mx-auto px-6 py-6">
        {/* Top Bar with Market Snapshot and Risk Summary */}
        <TopBar tenantId={DEFAULT_TENANT_ID} />

        {/* Header */}
        <motion.div
          initial={{ opacity: 0, y: -10 }}
          animate={{ opacity: 1, y: 0 }}
          className="mt-8 mb-6 flex items-center justify-between"
        >
          <div>
            <h1 className="text-2xl font-bold text-slate-100">Riskboard</h1>
            <p className="text-slate-500 mt-1">
              Unified risk view across all portfolios - NO P&L
            </p>
          </div>

          {/* Add RiskPod Button */}
          <motion.button
            whileHover={{ scale: 1.02 }}
            whileTap={{ scale: 0.98 }}
            onClick={addRiskPod}
            className="px-4 py-2 bg-slate-800 text-slate-300 rounded-lg hover:bg-slate-700
                       transition-colors flex items-center gap-2 border border-white/5"
          >
            <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 4v16m8-8H4" />
            </svg>
            Add RiskPod
          </motion.button>
        </motion.div>

        {/* RiskPods */}
        <div className="space-y-8">
          {riskPods.map((pod, index) => (
            <RiskPodSection
              key={pod.id}
              pod={pod}
              index={index}
              allBooks={allBooks || []}
              tradingBooks={tradingBooks || []}
              overlayBooks={overlayBooks || []}
              canDelete={index > 0}
              onDelete={() => deleteRiskPod(pod.id)}
              onBookSelectionChange={(bookIds) => updatePodBooks(pod.id, bookIds)}
              onTradesClick={handleTradesClick}
            />
          ))}
        </div>

        {/* Correlation Panel */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.3 }}
          className="mt-10"
        >
          <CorrelationPanel
            tenantId={DEFAULT_TENANT_ID}
            bookIds={selectedBooksForCorrelation}
          />
        </motion.div>
      </div>
    </div>
  )
}

// RiskPod Section Component
interface RiskPodSectionProps {
  pod: RiskPodState
  index: number
  allBooks: Book[]
  tradingBooks: Book[]
  overlayBooks: Book[]
  canDelete: boolean
  onDelete: () => void
  onBookSelectionChange: (bookIds: string[]) => void
  onTradesClick: (bookIds: string[], assetClass: string) => void
}

function RiskPodSection({
  pod,
  index,
  allBooks,
  tradingBooks,
  overlayBooks,
  canDelete,
  onDelete,
  onBookSelectionChange,
  onTradesClick,
}: RiskPodSectionProps) {
  // Fetch risk by asset class for selected books
  const { data: riskData, isLoading } = useQuery({
    queryKey: ['riskByAssetClass', pod.selectedBookIds],
    queryFn: () => riskboardApi.getRiskByAssetClass(pod.selectedBookIds),
    enabled: pod.selectedBookIds.length > 0,
  })

  // Get selected books info
  const selectedBooks = allBooks.filter((b) => pod.selectedBookIds.includes(b.book_id))
  const isAllBooks = pod.selectedBookIds.length === allBooks.length
  const hasOverlay = selectedBooks.some((b) => b.book_type === 'overlay')

  // Calculate summary for this pod
  const podNetExposure = riskData?.reduce((sum, r) => sum + r.net_exposure, 0) ?? 0
  const podPositionCount = riskData?.reduce((sum, r) => sum + r.position_count, 0) ?? 0

  return (
    <motion.section
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ delay: index * 0.1 }}
      className="glass p-6"
    >
      {/* Pod Header */}
      <div className="flex items-center justify-between mb-4">
        <div className="flex items-center gap-4">
          <h2 className="text-lg font-semibold text-slate-100">
            {index === 0 ? 'Firm-Wide' : `RiskPod ${index + 1}`}
          </h2>

          {/* Multi-Select Portfolio Dropdown */}
          <MultiSelectPortfolio
            books={allBooks}
            selectedBookIds={pod.selectedBookIds}
            onChange={onBookSelectionChange}
          />

          {/* Selection Summary */}
          <div className="flex items-center gap-2 text-sm text-slate-500">
            {isAllBooks ? (
              <span className="px-2 py-1 bg-blue-500/20 text-blue-300 rounded">All Books</span>
            ) : (
              <span>{selectedBooks.length} books selected</span>
            )}
            {hasOverlay && (
              <span className="px-2 py-1 bg-purple-500/20 text-purple-300 rounded text-xs">
                + Overlay
              </span>
            )}
          </div>
        </div>

        <div className="flex items-center gap-4">
          {/* Pod Summary */}
          <div className="flex items-center gap-4 text-sm">
            <div>
              <span className="text-slate-500">Net: </span>
              <span
                className={`font-mono ${
                  podNetExposure >= 0 ? 'text-emerald-400' : 'text-rose-400'
                }`}
              >
                {formatCurrency(podNetExposure)}
              </span>
            </div>
            <div>
              <span className="text-slate-500">Positions: </span>
              <span className="font-mono text-slate-300">{podPositionCount.toLocaleString()}</span>
            </div>
          </div>

          {/* Delete Button */}
          {canDelete && (
            <button
              onClick={onDelete}
              className="p-2 text-slate-500 hover:text-rose-400 hover:bg-rose-500/10 rounded-lg transition-colors"
              title="Delete RiskPod"
            >
              <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={2}
                  d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16"
                />
              </svg>
            </button>
          )}
        </div>
      </div>

      {/* Risk Cards */}
      {pod.selectedBookIds.length > 0 ? (
        <RiskPodRow
          data={riskData ?? []}
          title=""
          subtitle=""
          bookType={hasOverlay ? 'overlay' : 'trading'}
          isLoading={isLoading}
          onTradesClick={(assetClass) => onTradesClick(pod.selectedBookIds, assetClass)}
          showEmptyState={!isLoading}
        />
      ) : (
        <div className="text-center py-12 text-slate-500">
          <p>Select portfolios to view risk metrics</p>
        </div>
      )}
    </motion.section>
  )
}

// Multi-Select Portfolio Component
interface MultiSelectPortfolioProps {
  books: Book[]
  selectedBookIds: string[]
  onChange: (bookIds: string[]) => void
}

function MultiSelectPortfolio({ books, selectedBookIds, onChange }: MultiSelectPortfolioProps) {
  const [isOpen, setIsOpen] = useState(false)

  const toggleBook = (bookId: string) => {
    if (selectedBookIds.includes(bookId)) {
      onChange(selectedBookIds.filter((id) => id !== bookId))
    } else {
      onChange([...selectedBookIds, bookId])
    }
  }

  const selectAll = () => {
    onChange(books.map((b) => b.book_id))
  }

  const clearAll = () => {
    onChange([])
  }

  // Group books by type
  const tradingBooks = books.filter((b) => b.book_type !== 'overlay')
  const overlayBooks = books.filter((b) => b.book_type === 'overlay')

  return (
    <div className="relative">
      <button
        onClick={() => setIsOpen(!isOpen)}
        className="px-3 py-1.5 bg-slate-800 rounded-lg text-sm text-slate-300
                   hover:bg-slate-700 transition-colors flex items-center gap-2 border border-white/5"
      >
        <span>Select Portfolios</span>
        <svg
          className={`w-4 h-4 transition-transform ${isOpen ? 'rotate-180' : ''}`}
          fill="none"
          viewBox="0 0 24 24"
          stroke="currentColor"
        >
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
        </svg>
      </button>

      {isOpen && (
        <>
          {/* Backdrop */}
          <div className="fixed inset-0 z-10" onClick={() => setIsOpen(false)} />

          {/* Dropdown */}
          <div className="absolute top-full left-0 mt-2 w-72 bg-slate-800 rounded-xl shadow-xl
                          border border-white/10 z-20 overflow-hidden">
            {/* Header */}
            <div className="p-3 border-b border-white/5 flex items-center justify-between">
              <span className="text-sm font-medium text-slate-300">Portfolios</span>
              <div className="flex items-center gap-2">
                <button
                  onClick={selectAll}
                  className="text-xs text-blue-400 hover:text-blue-300"
                >
                  All
                </button>
                <span className="text-slate-600">|</span>
                <button
                  onClick={clearAll}
                  className="text-xs text-slate-500 hover:text-slate-400"
                >
                  Clear
                </button>
              </div>
            </div>

            {/* Trading Books */}
            <div className="p-2 max-h-60 overflow-y-auto">
              <p className="text-xs text-slate-500 uppercase tracking-wider px-2 py-1">
                Trading Books
              </p>
              {tradingBooks.map((book) => (
                <label
                  key={book.book_id}
                  className="flex items-center gap-3 px-2 py-2 hover:bg-slate-700/50 rounded cursor-pointer"
                >
                  <input
                    type="checkbox"
                    checked={selectedBookIds.includes(book.book_id)}
                    onChange={() => toggleBook(book.book_id)}
                    className="w-4 h-4 rounded bg-slate-700 border-slate-600 text-blue-500
                               focus:ring-blue-500 focus:ring-offset-slate-800"
                  />
                  <div className="flex-1">
                    <p className="text-sm text-slate-200">{book.name}</p>
                    {book.pm_name && (
                      <p className="text-xs text-slate-500">PM: {book.pm_name}</p>
                    )}
                  </div>
                </label>
              ))}

              {/* Overlay Books */}
              {overlayBooks.length > 0 && (
                <>
                  <p className="text-xs text-slate-500 uppercase tracking-wider px-2 py-1 mt-2">
                    Overlay Books
                  </p>
                  {overlayBooks.map((book) => (
                    <label
                      key={book.book_id}
                      className="flex items-center gap-3 px-2 py-2 hover:bg-slate-700/50 rounded cursor-pointer"
                    >
                      <input
                        type="checkbox"
                        checked={selectedBookIds.includes(book.book_id)}
                        onChange={() => toggleBook(book.book_id)}
                        className="w-4 h-4 rounded bg-slate-700 border-slate-600 text-purple-500
                                   focus:ring-purple-500 focus:ring-offset-slate-800"
                      />
                      <div className="flex-1">
                        <p className="text-sm text-purple-300">{book.name}</p>
                        <p className="text-xs text-slate-500">CIO Hedge</p>
                      </div>
                    </label>
                  ))}
                </>
              )}
            </div>
          </div>
        </>
      )}
    </div>
  )
}
