import './riskboard.css'

interface Override {
  ticker: string
  field: string
  originalValue: string
  overrideValue: string
  setBy: string
  setAt: string
}

// Sample overrides data
const SAMPLE_OVERRIDES: Record<string, Override[]> = {
  equity: [
    { ticker: 'NVDA', field: 'Price', originalValue: '$485.20', overrideValue: '$495.20', setBy: 'J. Smith', setAt: '14:25' },
    { ticker: 'TSLA', field: 'Vol', originalValue: '52%', overrideValue: '58%', setBy: 'J. Smith', setAt: '14:18' },
  ],
  rates: [
    { ticker: 'ZN', field: 'DV01', originalValue: '$95.20', overrideValue: '$98.50', setBy: 'M. Chen', setAt: '09:45' },
    { ticker: 'TLT', field: 'Duration', originalValue: '16.8', overrideValue: '17.2', setBy: 'M. Chen', setAt: '09:42' },
    { ticker: 'ZB', field: 'Price', originalValue: '117.25', overrideValue: '118.56', setBy: 'S. Johnson', setAt: '11:30' },
  ],
  credit: [],
  fx: [],
  commodities: [],
  other: [],
}

interface OverridesModalProps {
  isOpen: boolean
  onClose: () => void
  assetClass: string | null
  onClearOverride?: (ticker: string, field: string) => void
  onClearAll?: () => void
}

export default function OverridesModal({ isOpen, onClose, assetClass, onClearOverride, onClearAll }: OverridesModalProps) {
  if (!isOpen || !assetClass) return null

  const overrides = SAMPLE_OVERRIDES[assetClass] || []

  const colorClass = {
    equity: 'blue',
    rates: 'green',
    credit: 'purple',
    fx: 'cyan',
    commodities: 'orange',
    other: 'gray',
  }[assetClass] || 'blue'

  return (
    <div className="overrides-modal active" onClick={onClose}>
      <div className="overrides-modal-content" onClick={(e) => e.stopPropagation()}>
        <div className="overrides-modal-header">
          <div>
            <div className={`overrides-modal-title ${colorClass}`}>
              {assetClass.toUpperCase()} Price Overrides
            </div>
            <div className="overrides-modal-subtitle">
              {overrides.length} active override{overrides.length !== 1 ? 's' : ''}
            </div>
          </div>
          <button className="overrides-modal-close" onClick={onClose}>×</button>
        </div>

        {overrides.length === 0 ? (
          <div className="overrides-empty">
            <div className="overrides-empty-icon">✓</div>
            <div className="overrides-empty-text">No manual overrides active</div>
            <div className="overrides-empty-subtext">All prices are from market feeds</div>
          </div>
        ) : (
          <>
            <div className="overrides-list">
              {overrides.map((override, index) => (
                <div key={index} className="override-item">
                  <div className="override-info">
                    <div className="override-ticker">{override.ticker}</div>
                    <div className="override-field">{override.field}</div>
                  </div>
                  <div className="override-values">
                    <div className="override-original">
                      <span className="label">Original:</span>
                      <span className="value">{override.originalValue}</span>
                    </div>
                    <div className="override-arrow">→</div>
                    <div className="override-new">
                      <span className="label">Override:</span>
                      <span className="value">{override.overrideValue}</span>
                    </div>
                  </div>
                  <div className="override-meta">
                    Set by {override.setBy} at {override.setAt}
                  </div>
                  <button
                    className="override-clear-btn"
                    onClick={() => onClearOverride?.(override.ticker, override.field)}
                  >
                    Clear
                  </button>
                </div>
              ))}
            </div>

            <div className="overrides-footer">
              <button className="overrides-clear-all" onClick={onClearAll}>
                Clear All Overrides
              </button>
            </div>
          </>
        )}
      </div>
    </div>
  )
}
