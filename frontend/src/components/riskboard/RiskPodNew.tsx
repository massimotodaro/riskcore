import { useState } from 'react'
import RiskCardNew, { RiskCardData } from './RiskCardNew'
import './riskboard.css'

interface Book {
  book_id: string
  name: string
  pm_name?: string
}

interface RiskPodProps {
  podNumber: number
  books: Book[]
  selectedBookIds: string[]
  onBookSelectionChange: (bookIds: string[]) => void
  onDelete?: () => void
  canDelete?: boolean
  riskData: RiskCardData[]
  grossExposure: number
  netExposure: number
  positions: number
  lastCalculated?: string
  isStale?: boolean
  onCalculate?: () => void
  onTradesClick?: (assetClass: string) => void
  onExpandClick?: (data: RiskCardData) => void
  onMetricClick?: (metricName: string) => void
  onOverridesClick?: (assetClass: string) => void
}

export default function RiskPodNew({
  podNumber,
  books,
  selectedBookIds,
  onBookSelectionChange,
  onDelete,
  canDelete = true,
  riskData,
  grossExposure,
  netExposure,
  positions,
  lastCalculated = '09:42:15',
  isStale = false,
  onCalculate,
  onTradesClick,
  onExpandClick,
  onMetricClick,
  onOverridesClick,
}: RiskPodProps) {
  const [isDropdownOpen, setIsDropdownOpen] = useState(false)
  const [isCalculating, setIsCalculating] = useState(false)

  const isAllSelected = selectedBookIds.length === books.length

  const formatValue = (value: number): string => {
    const absValue = Math.abs(value)
    if (absValue >= 1_000_000_000) {
      return `$${(value / 1_000_000_000).toFixed(2)}B`
    }
    if (absValue >= 1_000_000) {
      return `$${(value / 1_000_000).toFixed(0)}M`
    }
    if (absValue >= 1_000) {
      return `$${(value / 1_000).toFixed(0)}K`
    }
    return `$${value.toFixed(0)}`
  }

  const toggleBook = (bookId: string) => {
    if (selectedBookIds.includes(bookId)) {
      onBookSelectionChange(selectedBookIds.filter((id) => id !== bookId))
    } else {
      onBookSelectionChange([...selectedBookIds, bookId])
    }
  }

  const selectAll = () => {
    onBookSelectionChange(books.map((b) => b.book_id))
  }

  const handleCalculate = async () => {
    setIsCalculating(true)
    onCalculate?.()
    // Simulate calculation
    setTimeout(() => setIsCalculating(false), 1500)
  }

  return (
    <section className="riskpod">
      {/* Delete Button */}
      {canDelete && (
        <button className="pod-delete" onClick={onDelete} title="Delete RiskPod">
          &#10005;
        </button>
      )}

      {/* Pod Header */}
      <div className="pod-header">
        <div className="pod-left">
          <span className="pod-number">Pod {podNumber}</span>

          {/* Portfolio Dropdown */}
          <div className="portfolio-dropdown">
            <button className="portfolio-btn" onClick={() => setIsDropdownOpen(!isDropdownOpen)}>
              Portfolios <span className="arrow">{isDropdownOpen ? '▲' : '▼'}</span>
            </button>

            {isDropdownOpen && (
              <>
                <div
                  style={{ position: 'fixed', inset: 0, zIndex: 999 }}
                  onClick={() => setIsDropdownOpen(false)}
                />
                <div className="portfolio-menu active">
                  <div className="portfolio-menu-header">
                    <span>Select Portfolios</span>
                    <button className="select-all-btn" onClick={selectAll}>
                      Select All
                    </button>
                  </div>
                  {books.map((book) => (
                    <div key={book.book_id} className="portfolio-item">
                      <input
                        type="checkbox"
                        id={`${podNumber}-${book.book_id}`}
                        checked={selectedBookIds.includes(book.book_id)}
                        onChange={() => toggleBook(book.book_id)}
                      />
                      <label htmlFor={`${podNumber}-${book.book_id}`}>{book.name}</label>
                    </div>
                  ))}
                </div>
              </>
            )}
          </div>

          {/* Selection Summary */}
          <span className={`selected-portfolios ${isAllSelected ? 'all' : ''}`}>
            {isAllSelected ? 'All' : `${selectedBookIds.length} selected`}
          </span>

          {/* Calculate Button */}
          <button
            className={`pod-calculate-btn ${isCalculating ? 'calculating' : ''} ${isStale ? 'stale' : ''}`}
            onClick={handleCalculate}
            title="Recalculate this pod"
          >
            <span className="icon">&#8635;</span> Calculate
          </button>

          {/* Summary */}
          <div className="pod-summary">
            <div className="pod-summary-item">
              <span className="label">Gross:</span>
              <span className="value">{formatValue(grossExposure)}</span>
            </div>
            <div className="pod-summary-item">
              <span className="label">Net:</span>
              <span className="value">{formatValue(netExposure)}</span>
            </div>
            <div className="pod-summary-item">
              <span className="label">Positions:</span>
              <span className="value">{positions.toLocaleString()}</span>
            </div>
          </div>

          {/* Timestamp */}
          <span className={`pod-timestamp ${isStale ? 'stale' : ''}`}>
            Last: <span className="time">{lastCalculated}</span>
            {isStale && <span className="stale-indicator"> STALE</span>}
          </span>
        </div>
      </div>

      {/* Cards Row */}
      <div className="cards-row">
        {riskData.map((cardData) => (
          <RiskCardNew
            key={cardData.assetClass}
            data={cardData}
            onTradesClick={() => onTradesClick?.(cardData.assetClass)}
            onExpandClick={() => onExpandClick?.(cardData)}
            onMetricClick={onMetricClick}
            onOverridesClick={() => onOverridesClick?.(cardData.assetClass)}
          />
        ))}
      </div>
    </section>
  )
}
