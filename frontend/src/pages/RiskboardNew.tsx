import { useState } from 'react'
import MarketAnchors from '../components/riskboard/MarketAnchors'
import RiskPodNew from '../components/riskboard/RiskPodNew'
import { RiskCardData } from '../components/riskboard/RiskCardNew'
import ExpandModal from '../components/riskboard/ExpandModal'
import CalculationModal from '../components/riskboard/CalculationModal'
import TradesModal from '../components/riskboard/TradesModal'
import OverridesModal from '../components/riskboard/OverridesModal'
import { useTheme } from '../context/ThemeContext'
import '../components/riskboard/riskboard.css'

// Mock books data
const MOCK_BOOKS = [
  { book_id: '1', name: 'Alpha Fund', pm_name: 'John Smith' },
  { book_id: '2', name: 'Beta Fund', pm_name: 'Sarah Johnson' },
  { book_id: '3', name: 'Gamma Strategies', pm_name: 'Mike Chen' },
  { book_id: '4', name: 'Delta Partners', pm_name: 'Lisa Wong' },
  { book_id: '5', name: 'Epsilon Capital', pm_name: 'Tom Brown' },
  { book_id: '6', name: 'Zeta Macro', pm_name: 'Emma Davis' },
  { book_id: '7', name: 'Eta Quant', pm_name: 'James Wilson' },
  { book_id: '8', name: 'Theta Arbitrage', pm_name: 'Amy Lee' },
]

// Mock risk data for each asset class
const MOCK_EQUITY_DATA: RiskCardData = {
  assetClass: 'equity',
  primaryValue: 42_500_000,
  change: 1.2,
  changeDirection: 'up',
  barPercent: 65,
  metrics: [{ value: '1.15' }, { value: '$280K' }, { value: '$42K' }],
  tableData: [
    { region: 'US+CAN', values: ['48%', '$20.4M', '1.08', '$134K', '0.96', '-$19.6M'] },
    { region: 'Europe', values: ['22%', '$9.4M', '0.95', '$62K', '0.88', '-$8.3M'] },
    { region: 'Japan', values: ['15%', '$6.4M', '0.82', '$42K', '0.85', '-$5.4M'] },
    { region: 'SE Asia', values: ['10%', '$4.3M', '1.15', '$28K', '0.78', '-$3.4M'] },
    { region: 'RoW', values: ['5%', '$2.0M', '0.92', '$14K', '0.72', '-$1.4M'] },
  ],
  positions: 342,
  var95: -2_100_000,
  cvar95: -3_400_000,
  grossExposure: 320_000_000,
  netExposure: 42_500_000,
  hasOverrides: false,
}

const MOCK_RATES_DATA: RiskCardData = {
  assetClass: 'rates',
  primaryValue: -185_000,
  change: 0.4,
  changeDirection: 'down',
  barPercent: 45,
  metrics: [{ value: '4.2y' }, { value: '0.85' }, { value: '32bp' }],
  tableData: [
    { region: '0-2Y', values: ['15%', '-$28K', '1.8', '0.02', '0.92', '+$15M'] },
    { region: '2-5Y', values: ['25%', '-$46K', '3.5', '0.15', '0.95', '+$13M'] },
    { region: '5-10Y', values: ['35%', '-$65K', '6.2', '0.45', '0.98', '+$10M'] },
    { region: '10-30Y', values: ['20%', '-$37K', '15.8', '2.10', '0.88', '+$2M'] },
    { region: 'TIPS', values: ['5%', '-$9K', '4.5', '0.20', '0.75', '+$1M'] },
  ],
  positions: 128,
  var95: -850_000,
  cvar95: -1_200_000,
  grossExposure: 450_000_000,
  netExposure: -185_000,
  hasOverrides: true,
}

const MOCK_CREDIT_DATA: RiskCardData = {
  assetClass: 'credit',
  primaryValue: 125_000,
  change: 0.8,
  changeDirection: 'up',
  barPercent: 55,
  metrics: [{ value: '142bp' }, { value: '$2.8M' }, { value: '45bp' }],
  tableData: [
    { region: 'IG', values: ['55%', '$69K', '85', '$1.2M', '0.92', '-$45M'] },
    { region: 'HY', values: ['25%', '$31K', '380', '$1.1M', '0.85', '-$18M'] },
    { region: 'EM', values: ['15%', '$19K', '220', '$0.4M', '0.78', '-$12M'] },
    { region: 'CDS', values: ['5%', '$6K', '95', '$0.1M', '0.88', '-$5M'] },
  ],
  positions: 89,
  var95: -650_000,
  cvar95: -980_000,
  grossExposure: 180_000_000,
  netExposure: 125_000,
  hasOverrides: false,
}

const MOCK_FX_DATA: RiskCardData = {
  assetClass: 'fx',
  primaryValue: 8_200_000,
  change: 0.3,
  changeDirection: 'up',
  barPercent: 40,
  metrics: [{ value: '12.5%' }, { value: '$95K' }, { value: '28bp' }],
  tableData: [
    { region: 'EUR', values: ['35%', '$2.9M', '8.2%', '$33K', '0.85', '-$2.5M'] },
    { region: 'JPY', values: ['25%', '$2.1M', '11.5%', '$24K', '0.72', '-$1.8M'] },
    { region: 'GBP', values: ['20%', '$1.6M', '9.8%', '$19K', '0.88', '-$1.4M'] },
    { region: 'EM', values: ['20%', '$1.6M', '18.2%', '$19K', '0.65', '-$1.2M'] },
  ],
  positions: 156,
  var95: -420_000,
  cvar95: -680_000,
  grossExposure: 95_000_000,
  netExposure: 8_200_000,
  hasOverrides: false,
}

const MOCK_COMMODITIES_DATA: RiskCardData = {
  assetClass: 'commodities',
  primaryValue: 12_500_000,
  change: 1.8,
  changeDirection: 'up',
  barPercent: 48,
  metrics: [{ value: '28.5%' }, { value: '$125K' }, { value: '12bp' }],
  tableData: [
    { region: 'Energy', values: ['55%', '$6.9M', '32%', '$68K', '0.85', '-$5.8M'] },
    { region: 'Metals', values: ['25%', '$3.1M', '22%', '$31K', '0.72', '-$2.6M'] },
    { region: 'Agri', values: ['15%', '$1.9M', '28%', '$19K', '0.65', '-$1.5M'] },
    { region: 'Other', values: ['5%', '$0.6M', '18%', '$7K', '0.55', '-$0.5M'] },
  ],
  positions: 89,
  var95: -520_000,
  cvar95: -780_000,
  grossExposure: 85_000_000,
  netExposure: 12_500_000,
  hasOverrides: false,
}

const MOCK_OTHER_DATA: RiskCardData = {
  assetClass: 'other',
  primaryValue: 3_500_000,
  change: 0.5,
  changeDirection: 'down',
  barPercent: 30,
  metrics: [{ value: '18.2%' }, { value: '$45K' }, { value: '-$12K' }],
  tableData: [
    { region: 'Crypto', values: ['40%', '$1.4M', '65%', '$18K', '0.25', '-$0.8M'] },
    { region: 'Vol', values: ['30%', '$1.1M', '85%', '$14K', '0.55', '-$0.6M'] },
    { region: 'Struct', values: ['20%', '$0.7M', '15%', '$9K', '0.45', '-$0.4M'] },
    { region: 'Other', values: ['10%', '$0.3M', '20%', '$4K', '0.35', '-$0.2M'] },
  ],
  positions: 45,
  var95: -180_000,
  cvar95: -280_000,
  grossExposure: 35_000_000,
  netExposure: 3_500_000,
  hasOverrides: false,
}

interface RiskPodState {
  id: string
  selectedBookIds: string[]
}

interface TimeSelection {
  type: 'latest' | 'yesterday' | 'lastweek' | 'monthend' | 'quarterend' | 'custom'
  label: string
  sublabel?: string
  isHistorical: boolean
}

const TIME_PRESETS: TimeSelection[] = [
  { type: 'latest', label: 'Latest (Now)', sublabel: 'Real-time data', isHistorical: false },
  { type: 'yesterday', label: 'Yesterday Close', sublabel: 'Jan 17, 2026 16:00 UTC', isHistorical: true },
  { type: 'lastweek', label: 'Last Week', sublabel: 'Jan 11, 2026 16:00 UTC', isHistorical: true },
  { type: 'monthend', label: 'Month End', sublabel: 'Dec 31, 2025 16:00 UTC', isHistorical: true },
  { type: 'quarterend', label: 'Quarter End', sublabel: 'Dec 31, 2025 16:00 UTC', isHistorical: true },
]

export default function RiskboardNew() {
  // Theme context
  const { isDarkMode, toggleTheme } = useTheme()

  // RiskPod states
  const [riskPods, setRiskPods] = useState<RiskPodState[]>([
    { id: 'pod-1', selectedBookIds: MOCK_BOOKS.map((b) => b.book_id) },
  ])

  // Time selector state
  const [selectedTime, setSelectedTime] = useState<TimeSelection>(TIME_PRESETS[0])
  const [isTimeSelectorOpen, setIsTimeSelectorOpen] = useState(false)
  const [customDateTime, setCustomDateTime] = useState('2026-01-18T14:30')

  // Last calculated
  const [lastCalculated, setLastCalculated] = useState('14:32:15')
  const [isCalculating, setIsCalculating] = useState(false)

  // Modal states
  const [expandModalOpen, setExpandModalOpen] = useState(false)
  const [expandModalData, setExpandModalData] = useState<RiskCardData | null>(null)
  const [calcModalOpen, setCalcModalOpen] = useState(false)
  const [calcModalMetric, setCalcModalMetric] = useState<string | null>(null)
  const [tradesModalOpen, setTradesModalOpen] = useState(false)
  const [tradesModalAsset, setTradesModalAsset] = useState<string | null>(null)
  const [overridesModalOpen, setOverridesModalOpen] = useState(false)
  const [overridesModalAsset, setOverridesModalAsset] = useState<string | null>(null)

  // Format value helper
  const formatValue = (value: number): string => {
    const absValue = Math.abs(value)
    if (absValue >= 1_000_000_000) {
      return `$${(value / 1_000_000_000).toFixed(2)}B`
    }
    if (absValue >= 1_000_000) {
      return `$${(value / 1_000_000).toFixed(0)}M`
    }
    return `$${value.toFixed(0)}`
  }

  // Add a new RiskPod
  const addRiskPod = () => {
    setRiskPods((prev) => [...prev, { id: `pod-${Date.now()}`, selectedBookIds: [] }])
  }

  // Delete a RiskPod
  const deleteRiskPod = (podId: string) => {
    if (riskPods.length > 1) {
      setRiskPods((prev) => prev.filter((p) => p.id !== podId))
    }
  }

  // Update selected books for a RiskPod
  const updatePodBooks = (podId: string, bookIds: string[]) => {
    setRiskPods((prev) => prev.map((p) => (p.id === podId ? { ...p, selectedBookIds: bookIds } : p)))
  }

  // Modal handlers
  const handleExpandClick = (data: RiskCardData) => {
    setExpandModalData(data)
    setExpandModalOpen(true)
  }

  const handleMetricClick = (metricName: string) => {
    setCalcModalMetric(metricName)
    setCalcModalOpen(true)
  }

  const handleTradesClick = (assetClass: string) => {
    setTradesModalAsset(assetClass)
    setTradesModalOpen(true)
  }

  const handleOverridesClick = (assetClass: string) => {
    setOverridesModalAsset(assetClass)
    setOverridesModalOpen(true)
  }

  const handleClearOverride = (ticker: string, field: string) => {
    console.log(`Clearing override for ${ticker} ${field}`)
    // TODO: Implement actual override clearing
  }

  const handleClearAllOverrides = () => {
    console.log('Clearing all overrides')
    // TODO: Implement actual clear all
    setOverridesModalOpen(false)
  }

  // Handle time selection
  const selectTime = (time: TimeSelection) => {
    setSelectedTime(time)
    setIsTimeSelectorOpen(false)
  }

  // Handle calculate
  const handleCalculate = () => {
    setIsCalculating(true)
    setTimeout(() => {
      setIsCalculating(false)
      const now = new Date()
      setLastCalculated(now.toLocaleTimeString('en-US', { hour12: false }))
    }, 1500)
  }

  // Return to live
  const returnToLive = () => {
    setSelectedTime(TIME_PRESETS[0])
  }

  // Calculate totals (6 RiskCards: Equity, Rates, Credit, FX, Commodities, Other)
  const firmGross =
    MOCK_EQUITY_DATA.grossExposure +
    MOCK_RATES_DATA.grossExposure +
    MOCK_CREDIT_DATA.grossExposure +
    MOCK_FX_DATA.grossExposure +
    MOCK_COMMODITIES_DATA.grossExposure +
    MOCK_OTHER_DATA.grossExposure
  const firmNet =
    MOCK_EQUITY_DATA.netExposure +
    MOCK_RATES_DATA.netExposure +
    MOCK_CREDIT_DATA.netExposure +
    MOCK_FX_DATA.netExposure +
    MOCK_COMMODITIES_DATA.netExposure +
    MOCK_OTHER_DATA.netExposure
  const totalPositions =
    MOCK_EQUITY_DATA.positions +
    MOCK_RATES_DATA.positions +
    MOCK_CREDIT_DATA.positions +
    MOCK_FX_DATA.positions +
    MOCK_COMMODITIES_DATA.positions +
    MOCK_OTHER_DATA.positions

  // 6 RiskCards: Equity, Rates, Credit, FX, Commodities, Other
  const allRiskData = [MOCK_EQUITY_DATA, MOCK_RATES_DATA, MOCK_CREDIT_DATA, MOCK_FX_DATA, MOCK_COMMODITIES_DATA, MOCK_OTHER_DATA]

  return (
    <div
      className={`min-h-screen ${!isDarkMode ? 'accessibility-mode' : ''}`}
      style={{
        background: !isDarkMode ? '#D9D9D9' : 'linear-gradient(180deg, #0f172a 0%, #1e293b 100%)',
        color: !isDarkMode ? '#1e293b' : '#e2e8f0',
        fontFamily: "-apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif",
      }}
    >
      {/* Header */}
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
          <span style={{ fontSize: '18px', fontWeight: 600, color: !isDarkMode ? '#1e293b' : '#e2e8f0' }}>Riskboard</span>

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
        </div>

        {/* Right side - Theme Toggle */}
        <div className="accessibility-toggle">
          <span className="label">{isDarkMode ? 'Dark' : 'Light'}</span>
          <label className="toggle-switch" title="Toggle dark/light mode">
            <input
              type="checkbox"
              checked={!isDarkMode}
              onChange={toggleTheme}
            />
            <span className="toggle-slider" />
          </label>
        </div>
      </header>

      {/* Main Content */}
      <main style={{ padding: '16px' }}>
        {/* Historical Banner */}
        {selectedTime.isHistorical && (
          <div className="historical-banner active">
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

        {/* Market Anchors */}
        <MarketAnchors />

        {/* Summary Strip */}
        <div className="summary-strip">
          <div className="summary-strip-item">
            <span className="label">Firm Gross:</span>
            <span className="value">{formatValue(firmGross)}</span>
          </div>
          <div className="summary-strip-item">
            <span className="label">Firm Net:</span>
            <span className="value">{formatValue(firmNet)}</span>
          </div>
          <div className="summary-strip-item">
            <span className="label">Total Positions:</span>
            <span className="value">{totalPositions.toLocaleString()}</span>
          </div>
          <div className="summary-strip-right">
            <button className="refresh-all-btn" onClick={handleCalculate} title="Recalculate all pods">
              <span className="icon">↻</span> Refresh All Pods
            </button>
          </div>
        </div>

        {/* RiskPods */}
        {riskPods.map((pod, index) => (
          <RiskPodNew
            key={pod.id}
            podNumber={index + 1}
            books={MOCK_BOOKS}
            selectedBookIds={pod.selectedBookIds}
            onBookSelectionChange={(bookIds) => updatePodBooks(pod.id, bookIds)}
            onDelete={() => deleteRiskPod(pod.id)}
            canDelete={index > 0}
            riskData={allRiskData}
            grossExposure={firmGross}
            netExposure={firmNet}
            positions={totalPositions}
            lastCalculated={lastCalculated}
            isStale={false}
            onCalculate={handleCalculate}
            onTradesClick={handleTradesClick}
            onExpandClick={handleExpandClick}
            onMetricClick={handleMetricClick}
            onOverridesClick={handleOverridesClick}
          />
        ))}

        {/* Add Pod Button */}
        <div className="add-pod-container">
          <button className="add-pod-btn" onClick={addRiskPod}>
            <span className="plus">+</span> Add RiskPod
          </button>
        </div>
      </main>

      {/* Modals */}
      <ExpandModal
        isOpen={expandModalOpen}
        onClose={() => setExpandModalOpen(false)}
        data={expandModalData}
      />

      <CalculationModal
        isOpen={calcModalOpen}
        onClose={() => setCalcModalOpen(false)}
        metricName={calcModalMetric}
      />

      <TradesModal
        isOpen={tradesModalOpen}
        onClose={() => setTradesModalOpen(false)}
        assetClass={tradesModalAsset}
      />

      <OverridesModal
        isOpen={overridesModalOpen}
        onClose={() => setOverridesModalOpen(false)}
        assetClass={overridesModalAsset}
        onClearOverride={handleClearOverride}
        onClearAll={handleClearAllOverrides}
      />
    </div>
  )
}
