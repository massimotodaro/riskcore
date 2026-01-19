import { useState, useEffect } from 'react'
import { useSearchParams } from 'react-router-dom'
import { useQuery } from '@tanstack/react-query'
import { motion } from 'framer-motion'
import { riskboardApi, tradesPageApi, formatCurrency, formatQuantity, RISKPOD_CONFIG } from '../services/api'
import PositionTable from '../components/trades/PositionTable'
import RepricingModal from '../components/trades/RepricingModal'
import { useTheme } from '../context/ThemeContext'
import '../components/riskboard/riskboard.css'
import type { RiskPodType, HistoricalPosition, RiskPodPositions } from '../types'

// Time presets matching Riskboard
const TIME_PRESETS = [
  { type: 'live', label: 'Live', sublabel: 'Real-time data', isHistorical: false },
  { type: 'cob', label: 'COB Yesterday', sublabel: 'Close of business', isHistorical: true },
  { type: 'som', label: 'Start of Month', sublabel: 'Month beginning', isHistorical: true },
  { type: 'soq', label: 'Start of Quarter', sublabel: 'Quarter beginning', isHistorical: true },
  { type: 'soy', label: 'Start of Year', sublabel: 'Year beginning', isHistorical: true },
]

const DEFAULT_TENANT_ID = 'b95fbd3b-e6f0-41f8-9c0c-5337e469cf50'

export default function Trades() {
  const { isDarkMode } = useTheme()
  const [searchParams, setSearchParams] = useSearchParams()

  // URL state
  const initialBooks = searchParams.get('books')?.split(',').filter(Boolean) || []

  // Local state
  const [selectedBooks, setSelectedBooks] = useState<string[]>(initialBooks)
  const [repricingPosition, setRepricingPosition] = useState<HistoricalPosition | null>(null)

  // Time Travel state (matching Riskboard)
  const [selectedTime, setSelectedTime] = useState(TIME_PRESETS[0])
  const [isTimeSelectorOpen, setIsTimeSelectorOpen] = useState(false)
  const [customDateTime, setCustomDateTime] = useState('')
  const [isCalculating, setIsCalculating] = useState(false)
  const [lastCalculated, setLastCalculated] = useState('Just now')

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
  const timeParam = selectedTime.isHistorical ? selectedTime.type : undefined
  const { data: riskpodData, isLoading, error } = useQuery({
    queryKey: ['positions-by-riskpod', selectedBooks, timeParam],
    queryFn: () => tradesPageApi.getPositionsByRiskPod(selectedBooks, timeParam),
    enabled: selectedBooks.length > 0,
    staleTime: 30000,
  })

  // Update URL when state changes
  useEffect(() => {
    const params = new URLSearchParams()
    if (selectedBooks.length > 0) params.set('books', selectedBooks.join(','))
    if (selectedTime.isHistorical) params.set('time', selectedTime.type)
    setSearchParams(params, { replace: true })
  }, [selectedBooks, selectedTime])

  // Time selection handlers (matching Riskboard)
  const selectTime = (preset: typeof TIME_PRESETS[0]) => {
    setSelectedTime(preset)
    setIsTimeSelectorOpen(false)
  }

  const returnToLive = () => {
    setSelectedTime(TIME_PRESETS[0])
  }

  const handleCalculate = () => {
    setIsCalculating(true)
    setTimeout(() => {
      setIsCalculating(false)
      setLastCalculated('Just now')
    }, 1500)
  }

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
    <div
      className={`h-full flex flex-col ${!isDarkMode ? 'accessibility-mode' : ''}`}
      style={{
        background: !isDarkMode ? '#D9D9D9' : undefined,
        color: !isDarkMode ? '#1e293b' : '#e2e8f0',
      }}
    >
      {/* Header - Matching Riskboard Style */}
      <header
        style={{
          background: !isDarkMode ? '#ECECEC' : 'rgba(15, 23, 42, 0.95)',
          borderBottom: !isDarkMode ? '1px solid #e2e8f0' : '1px solid rgba(255, 255, 255, 0.1)',
          padding: '10px 20px',
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center',
          position: 'sticky',
          top: 0,
          zIndex: 50,
        }}
      >
        <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
          <span style={{ fontSize: '18px', fontWeight: 600, color: !isDarkMode ? '#1e293b' : '#e2e8f0' }}>Trades</span>

          {/* Time Travel Controls */}
          <div className="time-travel-controls">
            {/* Time Selector */}
            <div className="time-selector">
              <button className="time-selector-btn" onClick={() => setIsTimeSelectorOpen(!isTimeSelectorOpen)}>
                <span className={`live-dot ${selectedTime.isHistorical ? 'historical' : ''}`} />
                <span>{selectedTime.label}</span>
                <span style={{ fontSize: '10px', color: '#94a3b8' }}>▼</span>
              </button>

              {isTimeSelectorOpen && (
                <>
                  <div
                    style={{ position: 'fixed', inset: 0, zIndex: 999 }}
                    onClick={() => setIsTimeSelectorOpen(false)}
                  />
                  <div className="time-selector-menu active">
                    <div className="time-menu-section">
                      <div className="time-menu-section-title">Presets</div>
                      {TIME_PRESETS.map((preset) => (
                        <div
                          key={preset.type}
                          className={`time-menu-item ${selectedTime.type === preset.type ? 'selected' : ''} ${preset.isHistorical ? 'historical' : ''}`}
                          onClick={() => selectTime(preset)}
                        >
                          <div className="radio" />
                          <div className="item-content">
                            <div className="item-label">{preset.label}</div>
                            {preset.sublabel && <div className="item-sublabel">{preset.sublabel}</div>}
                          </div>
                        </div>
                      ))}
                    </div>
                    <div className="time-menu-section">
                      <div className="time-menu-section-title">Custom Date & Time</div>
                      <div className="time-menu-custom">
                        <input
                          type="datetime-local"
                          value={customDateTime}
                          onChange={(e) => setCustomDateTime(e.target.value)}
                        />
                        <button
                          className="apply-btn"
                          onClick={() => {
                            selectTime({
                              type: 'custom',
                              label: new Date(customDateTime).toLocaleString(),
                              sublabel: '',
                              isHistorical: true,
                            })
                          }}
                        >
                          Apply
                        </button>
                      </div>
                    </div>
                  </div>
                </>
              )}
            </div>

            {/* Calculate Button */}
            <button
              className={`global-calculate-btn ${isCalculating ? 'calculating' : ''} ${selectedTime.isHistorical ? 'historical' : ''}`}
              onClick={handleCalculate}
            >
              <span className="icon">↻</span>
              <span>Calculate</span>
            </button>

            {/* Last Calculated */}
            <span className="last-calculated">Last: {lastCalculated}</span>
          </div>

          {/* Book Selector Pills */}
          <div
            style={{
              display: 'flex',
              alignItems: 'center',
              gap: '6px',
              padding: '6px 12px',
              background: !isDarkMode ? 'rgba(0, 0, 0, 0.05)' : 'rgba(255, 255, 255, 0.05)',
              border: !isDarkMode ? '1px solid rgba(0, 0, 0, 0.1)' : '1px solid rgba(255, 255, 255, 0.1)',
              borderRadius: '8px',
              marginLeft: '12px',
            }}
          >
            <span style={{ fontSize: '12px', color: '#64748b' }}>Books:</span>
            {books.slice(0, 5).map((book) => (
              <button
                key={book.book_id}
                onClick={() => handleBookToggle(book.book_id)}
                style={{
                  padding: '4px 10px',
                  fontSize: '12px',
                  borderRadius: '4px',
                  cursor: 'pointer',
                  transition: 'all 0.2s',
                  background: selectedBooks.includes(book.book_id) ? 'rgba(59, 130, 246, 0.2)' : 'transparent',
                  color: selectedBooks.includes(book.book_id) ? (!isDarkMode ? '#2563eb' : '#93c5fd') : '#64748b',
                  border: selectedBooks.includes(book.book_id) ? '1px solid rgba(59, 130, 246, 0.3)' : '1px solid transparent',
                }}
              >
                {book.name}
              </button>
            ))}
            {books.length > 5 && (
              <span style={{ fontSize: '12px', color: '#64748b' }}>+{books.length - 5}</span>
            )}
          </div>
        </div>
      </header>

      {/* Historical Banner */}
      {selectedTime.isHistorical && (
        <div className="historical-banner active" style={{ margin: '0 20px' }}>
          <span className="banner-icon">🕐</span>
          <div className="banner-text">
            <div className="banner-title">Viewing Historical Data</div>
            <div className="banner-subtitle">As of {selectedTime.sublabel || selectedTime.label}</div>
          </div>
          <button className="banner-close" onClick={returnToLive}>
            Return to Live
          </button>
        </div>
      )}


      {/* Main content - 6 RiskPod tables */}
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
            {/* Render tables for all 6 RiskPods */}
            {(['equity', 'rates', 'credit', 'fx', 'commodities', 'other'] as RiskPodType[]).map((pod) => {
              const podData = riskpodData?.[pod]
              const config = RISKPOD_CONFIG[pod]

              if (!podData || podData.position_count === 0) {
                return (
                  <motion.div
                    key={pod}
                    initial={{ opacity: 0, y: 20 }}
                    animate={{ opacity: 1, y: 0 }}
                    className="rounded-xl p-4"
                    style={{
                      background: !isDarkMode ? 'rgba(255, 255, 255, 0.8)' : 'rgba(15, 23, 42, 0.6)',
                      border: !isDarkMode ? '1px solid rgba(0, 0, 0, 0.1)' : '1px solid rgba(255, 255, 255, 0.05)',
                    }}
                  >
                    <div className="flex items-center justify-between mb-3">
                      <h3 className="text-lg font-semibold" style={{ color: config.color }}>{config.label}</h3>
                      <span className="text-sm" style={{ color: '#64748b' }}>0 positions</span>
                    </div>
                    <div className="text-center py-8" style={{ color: '#64748b' }}>
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
                  className="rounded-xl overflow-hidden"
                  style={{
                    background: !isDarkMode ? 'rgba(255, 255, 255, 0.8)' : 'rgba(15, 23, 42, 0.6)',
                    border: !isDarkMode ? '1px solid rgba(0, 0, 0, 0.1)' : '1px solid rgba(255, 255, 255, 0.05)',
                  }}
                >
                  {/* Table header */}
                  <div
                    className="px-4 py-3 flex items-center justify-between"
                    style={{
                      borderBottom: !isDarkMode ? '1px solid rgba(0, 0, 0, 0.1)' : '1px solid rgba(255, 255, 255, 0.05)',
                    }}
                  >
                    <div className="flex items-center gap-3">
                      <h3 className="text-lg font-semibold" style={{ color: config.color }}>{config.label}</h3>
                      <span className="text-sm" style={{ color: '#64748b' }}>
                        {podData.position_count} positions
                      </span>
                    </div>
                    <div className="flex items-center gap-4 text-sm">
                      <div>
                        <span style={{ color: '#64748b' }}>Gross: </span>
                        <span className="font-medium" style={{ color: !isDarkMode ? '#1e293b' : '#e2e8f0' }}>
                          {formatCurrency(podData.gross_exposure)}
                        </span>
                      </div>
                      <div>
                        <span style={{ color: '#64748b' }}>Net: </span>
                        <span
                          className="font-medium"
                          style={{ color: podData.net_exposure >= 0 ? '#10b981' : '#ef4444' }}
                        >
                          {formatCurrency(podData.net_exposure)}
                        </span>
                      </div>
                      <div>
                        <span style={{ color: '#64748b' }}>{config.primaryMetricLabel}: </span>
                        <span className="font-medium" style={{ color: !isDarkMode ? '#1e293b' : '#e2e8f0' }}>
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
                    isDarkMode={isDarkMode}
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
