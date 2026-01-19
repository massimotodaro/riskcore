import { useState, useEffect, useMemo } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import clsx from 'clsx'
import { useTheme } from '../context/ThemeContext'
import { PortfolioSelector, TimeSelector, CalculateButton, DEFAULT_TIME_PRESETS } from '../components/common'

// Types
interface Position {
  id: string
  ticker: string
  name: string
  type: 'common' | 'preferred' | 'option' | 'future' | 'etf' | 'adr' | 'bond' | 'swap' | 'cds' | 'spot' | 'forward' | 'structured' | 'fund'
  currency: string
  quantity: number
  portfolio: string
  portfolioColor: string
  pm: string
  tradeId?: string
  tradeDate?: string
  entryPrice: number
  entryPriceNote?: string
  lastPrice: number
  pricingType: 'market' | 'model' | 'manual'
  pnl: number
  marketValue: number
  delta?: number
  gamma?: number
  vega?: number
  dv01?: number
  convexity?: number
  duration?: string
  cs01?: number
  spread?: string
  jtd?: number
  fxDelta?: number
  correlation: number
  isHedged: boolean
  sector?: string
  // Override tracking
  hasManualOverride?: boolean
  overrideType?: 'price' | 'model'
}

interface RiskPodData {
  name: string
  color: string
  positionCount: number
  grossExposure: number
  netExposure: number
  primaryMetric: { label: string; value: string }
  secondaryMetric?: { label: string; value: string }
  positions: Position[]
}

// Mock data for demonstration
const mockEquityPositions: Position[] = [
  {
    id: 'eq-1',
    ticker: 'MSFT',
    name: 'Microsoft Corp',
    type: 'common',
    currency: 'USD',
    quantity: 12000,
    portfolio: 'Alpha Growth',
    portfolioColor: '#3b82f6',
    pm: 'M. Davis',
    tradeId: 'TRD-6C1D',
    tradeDate: 'Jan 5, 2026',
    entryPrice: 415.20,
    entryPriceNote: 'Weighted avg. entry price of 4 trades',
    lastPrice: 420.80,
    pricingType: 'market',
    pnl: 67200,
    marketValue: 5050000,
    delta: 11880,
    gamma: 198,
    correlation: 0.91,
    isHedged: false,
    sector: 'Technology',
  },
  {
    id: 'eq-2',
    ticker: 'NVDA',
    name: 'NVIDIA Corporation',
    type: 'common',
    currency: 'USD',
    quantity: 15000,
    portfolio: 'Alpha Growth',
    portfolioColor: '#3b82f6',
    pm: 'M. Davis',
    tradeId: 'TRD-8A3F',
    tradeDate: 'Jan 10, 2026',
    entryPrice: 825.50,
    entryPriceNote: 'Weighted avg. entry price of 3 trades',
    lastPrice: 830.00,
    pricingType: 'market',
    pnl: 67500,
    marketValue: 12450000,
    delta: 14850,
    gamma: 245,
    correlation: 0.85,
    isHedged: false,
    sector: 'Technology',
  },
  {
    id: 'eq-3',
    ticker: 'AAPL',
    name: 'Apple Inc.',
    type: 'common',
    currency: 'USD',
    quantity: -8500,
    portfolio: 'Beta Momentum',
    portfolioColor: '#8b5cf6',
    pm: 'E. Chen',
    tradeId: 'TRD-7B2E',
    tradeDate: 'Jan 8, 2026',
    entryPrice: 182.30,
    entryPriceNote: 'Weighted avg. entry price of 2 trades',
    lastPrice: 180.50,
    pricingType: 'market',
    pnl: 15300,
    marketValue: -1534250,
    delta: -8415,
    gamma: -142,
    correlation: 0.72,
    isHedged: true,
    sector: 'Technology',
  },
  {
    id: 'eq-4',
    ticker: 'ES Jun26',
    name: 'S&P 500 E-mini Jun26',
    type: 'future',
    currency: 'USD',
    quantity: -25,
    portfolio: 'Beta Momentum',
    portfolioColor: '#8b5cf6',
    pm: 'E. Chen',
    tradeId: 'TRD-4E8B',
    tradeDate: 'Jan 2, 2026',
    entryPrice: 4825.00,
    lastPrice: 4892.50,
    pricingType: 'market',
    pnl: -168750,
    marketValue: -6120000,
    delta: -125000,
    correlation: 0.98,
    isHedged: true,
  },
  {
    id: 'eq-5',
    ticker: 'SPY Call',
    name: 'SPY Mar 480 Call',
    type: 'option',
    currency: 'USD',
    quantity: 500,
    portfolio: 'Delta Quant',
    portfolioColor: '#06b6d4',
    pm: 'A. Thompson',
    tradeId: 'TRD-5D9A',
    tradeDate: 'Jan 3, 2026',
    entryPrice: 12.50,
    lastPrice: 14.20,
    pricingType: 'model',
    pnl: 85000,
    marketValue: 710000,
    delta: 32500,
    gamma: 1850,
    vega: 45200,
    correlation: 0.88,
    isHedged: false,
  },
  {
    id: 'eq-6',
    ticker: 'BAC Pfd C',
    name: 'Bank of America Pfd C',
    type: 'preferred',
    currency: 'USD',
    quantity: 10000,
    portfolio: 'Gamma Value',
    portfolioColor: '#f59e0b',
    pm: 'S. Park',
    tradeId: 'TRD-3F7C',
    tradeDate: 'Dec 28, 2025',
    entryPrice: 24.50,
    lastPrice: 24.85,
    pricingType: 'market',
    pnl: 3500,
    marketValue: 248500,
    delta: 9900,
    gamma: 165,
    correlation: 0.65,
    isHedged: false,
    sector: 'Financials',
  },
]

const mockRatesPositions: Position[] = [
  {
    id: 'rt-1',
    ticker: 'TY Mar26',
    name: '10Y Treasury Future Mar26',
    type: 'future',
    currency: 'USD',
    quantity: -150,
    portfolio: 'Epsilon Macro',
    portfolioColor: '#ec4899',
    pm: 'J. Mueller',
    tradeId: 'TRD-9I4F',
    tradeDate: 'Jan 7, 2026',
    entryPrice: 110.25,
    entryPriceNote: 'Weighted avg. entry price of 3 trades',
    lastPrice: 111.50,
    pricingType: 'market',
    pnl: -187500,
    marketValue: -16725000,
    dv01: -68250,
    correlation: 0.95,
    isHedged: true,
  },
  {
    id: 'rt-2',
    ticker: 'BUND 2.75%',
    name: 'EUR Bund 10Y 2.75%',
    type: 'bond',
    currency: 'EUR',
    quantity: 25000000,
    portfolio: 'Epsilon Macro',
    portfolioColor: '#ec4899',
    pm: 'J. Mueller',
    tradeId: 'TRD-2G6D',
    tradeDate: 'Jan 9, 2026',
    entryPrice: 102.35,
    lastPrice: 103.15,
    pricingType: 'model',
    pnl: 200000,
    marketValue: 27800000,
    dv01: 22150,
    convexity: 0.95,
    duration: '9.2Y',
    correlation: 0.35,
    isHedged: false,
  },
  {
    id: 'rt-3',
    ticker: '5Y/10Y SS',
    name: '5Y/10Y Swap Spread',
    type: 'swap',
    currency: 'USD',
    quantity: 100000000,
    portfolio: 'Eta Rates',
    portfolioColor: '#f97316',
    pm: 'S. Kim',
    tradeId: 'TRD-1H5E',
    tradeDate: 'Jan 8, 2026',
    entryPrice: -12,
    lastPrice: -8,
    pricingType: 'model',
    pnl: 400000,
    marketValue: 4200000,
    dv01: 28500,
    convexity: 0.42,
    duration: '7.5Y',
    correlation: 0.58,
    isHedged: false,
  },
]

const mockCreditPositions: Position[] = [
  {
    id: 'cr-1',
    ticker: 'AAPL 5.25%',
    name: 'Apple Corp 5.25% 2030',
    type: 'bond',
    currency: 'USD',
    quantity: 20000000,
    portfolio: 'Zeta Credit',
    portfolioColor: '#10b981',
    pm: 'J. Wilson',
    tradeId: 'TRD-8J3G',
    tradeDate: 'Jan 12, 2026',
    entryPrice: 101.25,
    entryPriceNote: 'Weighted avg. entry price of 3 trades',
    lastPrice: 102.50,
    pricingType: 'market',
    pnl: 250000,
    marketValue: 20500000,
    cs01: 8200,
    spread: '45 bps',
    jtd: 2000000,
    correlation: 0.32,
    isHedged: false,
  },
  {
    id: 'cr-2',
    ticker: 'F CDS 3Y',
    name: 'Ford Motor 3Y CDS',
    type: 'cds',
    currency: 'USD',
    quantity: 10000000,
    portfolio: 'Zeta Credit',
    portfolioColor: '#10b981',
    pm: 'J. Wilson',
    tradeId: 'TRD-9I4F',
    tradeDate: 'Jan 13, 2026',
    entryPrice: 145,
    lastPrice: 138,
    pricingType: 'market',
    pnl: 70000,
    marketValue: 1420000,
    cs01: -4200,
    spread: '138 bps',
    jtd: 1000000,
    correlation: 0.82,
    isHedged: true,
  },
]

const mockFxPositions: Position[] = [
  {
    id: 'fx-1',
    ticker: 'EUR/USD Call',
    name: 'EUR/USD 3M Call 1.10',
    type: 'option',
    currency: 'EUR',
    quantity: 10000000,
    portfolio: 'Epsilon Macro',
    portfolioColor: '#ec4899',
    pm: 'K. Tanaka',
    tradeId: 'TRD-6L1I',
    tradeDate: 'Jan 14, 2026',
    entryPrice: 0.0185,
    lastPrice: 0.0210,
    pricingType: 'model',
    pnl: 25000,
    marketValue: 210000,
    fxDelta: 5200000,
    gamma: 85000,
    vega: 32000,
    correlation: 0.45,
    isHedged: false,
  },
  {
    id: 'fx-2',
    ticker: 'USD/JPY Fwd',
    name: 'USD/JPY 6M Forward',
    type: 'forward',
    currency: 'JPY',
    quantity: -5000000,
    portfolio: 'Epsilon Macro',
    portfolioColor: '#ec4899',
    pm: 'K. Tanaka',
    tradeId: 'TRD-7M2J',
    tradeDate: 'Jan 10, 2026',
    entryPrice: 148.50,
    lastPrice: 149.20,
    pricingType: 'market',
    pnl: -35000,
    marketValue: -33520,
    fxDelta: -5000000,
    correlation: 0.62,
    isHedged: true,
  },
]

// RiskPod configurations
const riskPodConfigs: Record<string, RiskPodData> = {
  equity: {
    name: 'Equity',
    color: '#3b82f6',
    positionCount: mockEquityPositions.length,
    grossExposure: 25830000,
    netExposure: 10804250,
    primaryMetric: { label: 'Beta', value: '1.12' },
    secondaryMetric: { label: 'Delta', value: '$10.8M' },
    positions: mockEquityPositions,
  },
  rates: {
    name: 'Rates',
    color: '#22c55e',
    positionCount: mockRatesPositions.length,
    grossExposure: 320500000,
    netExposure: 85200000,
    primaryMetric: { label: 'DV01', value: '125.8K' },
    secondaryMetric: { label: 'Convexity', value: '3.42' },
    positions: mockRatesPositions,
  },
  credit: {
    name: 'Credit',
    color: '#a855f7',
    positionCount: mockCreditPositions.length,
    grossExposure: 85200000,
    netExposure: -12500000,
    primaryMetric: { label: 'CS01', value: '42.5K' },
    secondaryMetric: { label: 'JTD', value: '$8.2M' },
    positions: mockCreditPositions,
  },
  fx: {
    name: 'FX',
    color: '#06b6d4',
    positionCount: mockFxPositions.length,
    grossExposure: 45200000,
    netExposure: 12800000,
    primaryMetric: { label: 'FX Delta', value: '$12.8M' },
    secondaryMetric: { label: 'Vega', value: '85K' },
    positions: mockFxPositions,
  },
  commodities: {
    name: 'Commodities',
    color: '#f97316',
    positionCount: 0,
    grossExposure: 0,
    netExposure: 0,
    primaryMetric: { label: 'Delta', value: '-' },
    positions: [],
  },
  other: {
    name: 'Other',
    color: '#94a3b8',
    positionCount: 0,
    grossExposure: 0,
    netExposure: 0,
    primaryMetric: { label: 'Notional', value: '-' },
    positions: [],
  },
}

// Instrument type styles
const instTypeStyles: Record<string, { bg: string; text: string }> = {
  common: { bg: 'rgba(100, 116, 139, 0.15)', text: '#94a3b8' },
  preferred: { bg: 'rgba(168, 85, 247, 0.15)', text: '#a855f7' },
  option: { bg: 'rgba(59, 130, 246, 0.15)', text: '#3b82f6' },
  future: { bg: 'rgba(245, 158, 11, 0.15)', text: '#f59e0b' },
  etf: { bg: 'rgba(6, 182, 212, 0.15)', text: '#06b6d4' },
  adr: { bg: 'rgba(236, 72, 153, 0.15)', text: '#ec4899' },
  bond: { bg: 'rgba(34, 197, 94, 0.15)', text: '#22c55e' },
  swap: { bg: 'rgba(139, 92, 246, 0.15)', text: '#8b5cf6' },
  cds: { bg: 'rgba(239, 68, 68, 0.15)', text: '#ef4444' },
  spot: { bg: 'rgba(20, 184, 166, 0.15)', text: '#14b8a6' },
  forward: { bg: 'rgba(251, 146, 60, 0.15)', text: '#fb923c' },
  structured: { bg: 'rgba(156, 163, 175, 0.15)', text: '#9ca3af' },
  fund: { bg: 'rgba(34, 211, 238, 0.15)', text: '#22d3ee' },
}

// Currency styles
const currencyStyles: Record<string, { bg: string; text: string }> = {
  USD: { bg: 'rgba(34, 197, 94, 0.15)', text: '#22c55e' },
  EUR: { bg: 'rgba(59, 130, 246, 0.15)', text: '#3b82f6' },
  GBP: { bg: 'rgba(168, 85, 247, 0.15)', text: '#a855f7' },
  JPY: { bg: 'rgba(239, 68, 68, 0.15)', text: '#ef4444' },
  CHF: { bg: 'rgba(245, 158, 11, 0.15)', text: '#f59e0b' },
}

// Helper functions
function formatCurrency(value: number): string {
  const absValue = Math.abs(value)
  if (absValue >= 1_000_000_000) return `$${(value / 1_000_000_000).toFixed(2)}B`
  if (absValue >= 1_000_000) return `$${(value / 1_000_000).toFixed(2)}M`
  if (absValue >= 1_000) return `$${(value / 1_000).toFixed(1)}K`
  return `$${value.toFixed(0)}`
}

function formatQuantity(value: number): string {
  const formatted = Math.abs(value).toLocaleString()
  return value < 0 ? `-${formatted}` : formatted
}

function formatPrice(value: number, type: string): string {
  if (type === 'swap' || type === 'cds') return `${value} bps`
  if (Math.abs(value) < 1) return `$${value.toFixed(4)}`
  return `$${value.toFixed(2)}`
}

// Model names by instrument type
const modelNames: Record<string, string> = {
  option: 'Black-Scholes Model',
  bond: 'Discounted Cash Flow Model',
  swap: 'Multi-Curve SOFR Model',
  cds: 'ISDA CDS Standard Model',
  forward: 'Interest Rate Parity Model',
  future: 'Cost of Carry Model',
}

// Model input configurations by instrument type
const modelInputConfigs: Record<string, { label: string; key: string; defaultValue: string; unit?: string }[]> = {
  option: [
    { label: 'Implied Volatility', key: 'impliedVol', defaultValue: '25.5', unit: '%' },
    { label: 'Risk-Free Rate', key: 'riskFreeRate', defaultValue: '4.25', unit: '%' },
    { label: 'Dividend Yield', key: 'divYield', defaultValue: '0.50', unit: '%' },
    { label: 'Days to Expiry', key: 'daysToExpiry', defaultValue: '45', unit: 'days' },
  ],
  bond: [
    { label: 'Yield to Maturity', key: 'ytm', defaultValue: '4.85', unit: '%' },
    { label: 'Credit Spread', key: 'creditSpread', defaultValue: '125', unit: 'bps' },
    { label: 'Recovery Rate', key: 'recoveryRate', defaultValue: '40', unit: '%' },
    { label: 'OAS', key: 'oas', defaultValue: '85', unit: 'bps' },
  ],
  swap: [
    { label: 'Fixed Rate', key: 'fixedRate', defaultValue: '4.15', unit: '%' },
    { label: 'Floating Spread', key: 'floatingSpread', defaultValue: '25', unit: 'bps' },
    { label: 'Discount Curve', key: 'discountCurve', defaultValue: 'SOFR', unit: '' },
  ],
  cds: [
    { label: 'Credit Spread', key: 'creditSpread', defaultValue: '138', unit: 'bps' },
    { label: 'Recovery Rate', key: 'recoveryRate', defaultValue: '40', unit: '%' },
    { label: 'Hazard Rate', key: 'hazardRate', defaultValue: '2.3', unit: '%' },
  ],
  forward: [
    { label: 'Forward Rate', key: 'forwardRate', defaultValue: '1.0850', unit: '' },
    { label: 'Spot Rate', key: 'spotRate', defaultValue: '1.0825', unit: '' },
    { label: 'Interest Differential', key: 'intDiff', defaultValue: '0.25', unit: '%' },
  ],
  future: [
    { label: 'Basis', key: 'basis', defaultValue: '-0.125', unit: '' },
    { label: 'Cost of Carry', key: 'costOfCarry', defaultValue: '0.35', unit: '%' },
    { label: 'Conversion Factor', key: 'conversionFactor', defaultValue: '0.8542', unit: '' },
  ],
}

// PositionDrilldownPanel Component
function PositionDrilldownPanel({
  position,
  onClose,
  isDarkMode,
  onUpdatePosition,
}: {
  position: Position
  onClose: () => void
  isDarkMode: boolean
  onUpdatePosition?: (updatedPosition: Position) => void
}) {
  const [activeTab, setActiveTab] = useState<'market' | 'model' | 'manual'>('market')
  const [manualPrice, setManualPrice] = useState('')

  // Track override state locally (would be persisted in real app)
  const [hasOverride, setHasOverride] = useState(position.hasManualOverride || false)
  const [overrideType, setOverrideType] = useState<'price' | 'model' | null>(position.overrideType || null)

  // Model inputs state - initialize with defaults based on instrument type
  const getDefaultModelInputs = () => {
    const config = modelInputConfigs[position.type] || []
    const defaults: Record<string, string> = {}
    config.forEach(input => {
      defaults[input.key] = input.defaultValue
    })
    return defaults
  }
  const [modelInputs, setModelInputs] = useState<Record<string, string>>(getDefaultModelInputs)
  const [modelInputsModified, setModelInputsModified] = useState(false)
  const [manualPriceModified, setManualPriceModified] = useState(false)

  const bgColor = isDarkMode ? '#1e293b' : '#f8fafc'
  const borderColor = isDarkMode ? '#334155' : '#e2e8f0'
  const textColor = isDarkMode ? '#f8fafc' : '#1e293b'
  const mutedColor = isDarkMode ? '#64748b' : '#94a3b8'
  const cardBg = isDarkMode ? '#334155' : '#e2e8f0'

  const handleModelInputChange = (key: string, value: string) => {
    setModelInputs(prev => ({ ...prev, [key]: value }))
    setModelInputsModified(true)
  }

  const handleManualPriceChange = (value: string) => {
    setManualPrice(value)
    setManualPriceModified(value !== '')
  }

  const handleSaveAndRecalculate = (type: 'model' | 'price') => {
    if (type === 'model') {
      console.log('Saving model inputs:', modelInputs)
      setModelInputsModified(false)
    } else {
      console.log('Saving manual price:', manualPrice)
      setManualPriceModified(false)
    }
    setHasOverride(true)
    setOverrideType(type)

    // Update the position with override flag
    if (onUpdatePosition) {
      onUpdatePosition({
        ...position,
        hasManualOverride: true,
        overrideType: type,
      })
    }
  }

  const handleReset = () => {
    if (overrideType === 'model') {
      // Reset model inputs to defaults
      setModelInputs(getDefaultModelInputs())
      setModelInputsModified(false)
    } else {
      // Reset manual price
      setManualPrice('')
      setManualPriceModified(false)
    }
    setHasOverride(false)
    setOverrideType(null)

    // Update the position to remove override flag
    if (onUpdatePosition) {
      onUpdatePosition({
        ...position,
        hasManualOverride: false,
        overrideType: undefined,
      })
    }
  }

  return (
    <>
      {/* Overlay */}
      <motion.div
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        exit={{ opacity: 0 }}
        className="fixed inset-0 bg-black/50 z-[1000]"
        onClick={onClose}
      />

      {/* Panel */}
      <motion.div
        initial={{ x: 600 }}
        animate={{ x: 0 }}
        exit={{ x: 600 }}
        transition={{ type: 'spring', damping: 30, stiffness: 300 }}
        className="fixed top-0 right-0 w-[600px] h-screen z-[1001] flex flex-col overflow-hidden"
        style={{ background: bgColor, borderLeft: `1px solid ${borderColor}` }}
      >
        {/* Header */}
        <div className="p-5 border-b flex justify-between items-start" style={{ borderColor }}>
          <div>
            <div className="flex items-center gap-3">
              <h2 className="text-lg font-semibold" style={{ color: textColor }}>
                {position.name}
              </h2>
              <span
                className="px-2.5 py-1 rounded text-xs font-semibold"
                style={{
                  background: instTypeStyles[position.type]?.bg,
                  color: instTypeStyles[position.type]?.text,
                }}
              >
                {position.type.toUpperCase()}
              </span>
            </div>
            <div className="text-sm mt-1" style={{ color: mutedColor }}>
              {position.ticker} | {position.portfolio} | {position.pm}
            </div>
          </div>
          <button
            onClick={onClose}
            className="w-8 h-8 rounded-lg flex items-center justify-center text-lg transition-colors"
            style={{
              border: `1px solid ${borderColor}`,
              color: mutedColor,
            }}
          >
            ×
          </button>
        </div>

        {/* Body */}
        <div className="flex-1 overflow-y-auto p-6">
          {/* Override Warning Banner */}
          {hasOverride && (
            <div
              className="flex items-center gap-3 p-4 rounded-lg mb-5"
              style={{
                background: 'linear-gradient(135deg, rgba(245, 158, 11, 0.1) 0%, rgba(245, 158, 11, 0.05) 100%)',
                border: '1px solid rgba(245, 158, 11, 0.3)',
              }}
            >
              <div className="w-9 h-9 rounded-full bg-amber-500 flex items-center justify-center text-black font-bold text-lg">
                !
              </div>
              <div className="flex-1">
                <div className="text-sm font-semibold text-amber-400">
                  {overrideType === 'model' ? 'Model Inputs Modified' : 'Manual Price Override Active'}
                </div>
                <div className="text-xs text-amber-300/80">
                  {overrideType === 'model'
                    ? 'Using custom model inputs instead of defaults'
                    : 'Using manual price instead of market/model'}
                </div>
              </div>
              <button
                onClick={handleReset}
                className="px-4 py-2 rounded border border-amber-500/50 text-amber-400 text-xs font-semibold hover:bg-amber-500/20 transition-colors"
              >
                {overrideType === 'model' ? 'Reset to Defaults' : 'Reset to Market'}
              </button>
            </div>
          )}

          {/* Metrics Grid */}
          <div className="mb-6">
            <div className="text-xs font-semibold uppercase tracking-wider mb-3" style={{ color: mutedColor }}>
              Position Metrics
            </div>
            <div className="grid grid-cols-3 gap-3">
              <div className="p-3 rounded-lg" style={{ background: cardBg }}>
                <div className="text-xs mb-1" style={{ color: mutedColor }}>Quantity</div>
                <div className="text-base font-semibold font-mono" style={{ color: position.quantity >= 0 ? '#34d399' : '#f87171' }}>
                  {formatQuantity(position.quantity)}
                </div>
              </div>
              <div className="p-3 rounded-lg" style={{ background: cardBg }}>
                <div className="text-xs mb-1" style={{ color: mutedColor }}>Market Value</div>
                <div className="text-base font-semibold font-mono" style={{ color: position.marketValue >= 0 ? '#34d399' : '#f87171' }}>
                  {formatCurrency(position.marketValue)}
                </div>
              </div>
              <div className="p-3 rounded-lg" style={{ background: cardBg }}>
                <div className="text-xs mb-1" style={{ color: mutedColor }}>P&L</div>
                <div className="text-base font-semibold font-mono" style={{ color: position.pnl >= 0 ? '#34d399' : '#f87171' }}>
                  {position.pnl >= 0 ? '+' : ''}{formatCurrency(position.pnl)}
                </div>
              </div>
              {position.delta !== undefined && (
                <div className="p-3 rounded-lg" style={{ background: cardBg }}>
                  <div className="text-xs mb-1" style={{ color: mutedColor }}>Delta</div>
                  <div className="text-base font-semibold font-mono" style={{ color: textColor }}>
                    {formatQuantity(position.delta)}
                  </div>
                </div>
              )}
              {position.gamma !== undefined && (
                <div className="p-3 rounded-lg" style={{ background: cardBg }}>
                  <div className="text-xs mb-1" style={{ color: mutedColor }}>Gamma</div>
                  <div className="text-base font-semibold font-mono" style={{ color: textColor }}>
                    {formatQuantity(position.gamma)}
                  </div>
                </div>
              )}
              {position.vega !== undefined && (
                <div className="p-3 rounded-lg" style={{ background: cardBg }}>
                  <div className="text-xs mb-1" style={{ color: mutedColor }}>Vega</div>
                  <div className="text-base font-semibold font-mono" style={{ color: textColor }}>
                    {formatQuantity(position.vega)}
                  </div>
                </div>
              )}
              {position.dv01 !== undefined && (
                <div className="p-3 rounded-lg" style={{ background: cardBg }}>
                  <div className="text-xs mb-1" style={{ color: mutedColor }}>DV01</div>
                  <div className="text-base font-semibold font-mono" style={{ color: textColor }}>
                    {formatQuantity(position.dv01)}
                  </div>
                </div>
              )}
              {position.duration && (
                <div className="p-3 rounded-lg" style={{ background: cardBg }}>
                  <div className="text-xs mb-1" style={{ color: mutedColor }}>Duration</div>
                  <div className="text-base font-semibold font-mono" style={{ color: textColor }}>
                    {position.duration}
                  </div>
                </div>
              )}
              <div className="p-3 rounded-lg" style={{ background: cardBg }}>
                <div className="text-xs mb-1" style={{ color: mutedColor }}>Correlation</div>
                <div
                  className="text-base font-semibold font-mono"
                  style={{ color: position.correlation > 0.8 ? '#f87171' : position.correlation > 0.5 ? '#fbbf24' : '#22c55e' }}
                >
                  {position.correlation.toFixed(2)}
                </div>
              </div>
            </div>
          </div>

          {/* Pricing Section */}
          <div
            className="rounded-xl p-5"
            style={{
              background: isDarkMode ? '#0f172a' : '#f1f5f9',
              border: `1px solid ${borderColor}`,
            }}
          >
            <div className="flex justify-between items-center mb-4">
              <div className="flex items-center gap-2">
                <span className="text-sm font-semibold" style={{ color: textColor }}>Pricing</span>
                <span
                  className="px-2 py-0.5 rounded text-xs font-semibold"
                  style={{
                    background: position.pricingType === 'market' ? 'rgba(59, 130, 246, 0.2)' : position.pricingType === 'model' ? 'rgba(139, 92, 246, 0.2)' : 'rgba(245, 158, 11, 0.2)',
                    color: position.pricingType === 'market' ? '#60a5fa' : position.pricingType === 'model' ? '#a78bfa' : '#fbbf24',
                  }}
                >
                  {position.pricingType.toUpperCase()}
                </span>
              </div>
            </div>

            {/* Pricing Tabs */}
            <div
              className="flex gap-1 p-1 rounded-lg mb-4"
              style={{ background: isDarkMode ? '#1e293b' : '#e2e8f0' }}
            >
              {['market', 'model', 'manual'].map((tab) => (
                <button
                  key={tab}
                  onClick={() => setActiveTab(tab as typeof activeTab)}
                  className={clsx(
                    'flex-1 py-2.5 px-4 rounded-md text-xs font-semibold transition-all',
                    activeTab === tab
                      ? 'bg-slate-600 text-white'
                      : 'text-slate-500 hover:text-slate-300'
                  )}
                >
                  {tab.charAt(0).toUpperCase() + tab.slice(1)}
                </button>
              ))}
            </div>

            {/* Current Price Display */}
            <div
              className="flex justify-between items-center p-3 rounded-lg mb-4"
              style={{ background: isDarkMode ? '#1e293b' : '#e2e8f0' }}
            >
              <span className="text-xs" style={{ color: mutedColor }}>Current Price</span>
              <span className="text-lg font-semibold font-mono" style={{ color: textColor }}>
                {formatPrice(position.lastPrice, position.type)}
              </span>
            </div>

            {/* Entry Price */}
            <div className="flex justify-between items-center mb-4">
              <span className="text-xs" style={{ color: mutedColor }}>Entry Price</span>
              <div className="text-right">
                <span className="text-sm font-mono" style={{ color: textColor }}>
                  {formatPrice(position.entryPrice, position.type)}
                </span>
                {position.entryPriceNote && (
                  <div className="text-xs" style={{ color: mutedColor }}>{position.entryPriceNote}</div>
                )}
              </div>
            </div>

            {/* Model Inputs Section */}
            {activeTab === 'model' && (
              <div className="mt-4 pt-4 border-t" style={{ borderColor }}>
                {/* Model Name */}
                {modelNames[position.type] && (
                  <div className="text-sm font-semibold mb-1" style={{ color: instTypeStyles[position.type]?.text || '#fff' }}>
                    {modelNames[position.type]}
                  </div>
                )}

                <div className="flex justify-between items-center mb-4">
                  <div className="text-xs font-medium" style={{ color: '#e2e8f0' }}>Model Inputs</div>
                  {modelInputsModified && (
                    <span className="text-[10px] px-2 py-0.5 rounded bg-amber-500/20 text-amber-400">Modified</span>
                  )}
                </div>

                {modelInputConfigs[position.type] ? (
                  <div className="space-y-3">
                    {modelInputConfigs[position.type].map((input) => (
                      <div key={input.key} className="flex items-center justify-between gap-3">
                        <label className="text-sm flex-shrink-0" style={{ color: '#fff' }}>
                          {input.label}
                        </label>
                        <div
                          className="w-28 px-2 py-1.5 rounded text-sm flex items-center justify-end gap-1"
                          style={{
                            background: isDarkMode ? '#0f172a' : '#fff',
                            border: `1px solid ${borderColor}`,
                          }}
                        >
                          <input
                            type="text"
                            value={modelInputs[input.key] || ''}
                            onChange={(e) => handleModelInputChange(input.key, e.target.value)}
                            className="w-full bg-transparent text-right font-mono outline-none"
                            style={{ color: '#fff' }}
                          />
                          {input.unit && (
                            <span className="text-xs flex-shrink-0" style={{ color: '#94a3b8' }}>{input.unit}</span>
                          )}
                        </div>
                      </div>
                    ))}

                    <button
                      onClick={() => handleSaveAndRecalculate('model')}
                      disabled={!modelInputsModified}
                      className={clsx(
                        'w-full mt-4 py-2.5 rounded-lg text-sm font-semibold transition-all flex items-center justify-center gap-2',
                        modelInputsModified
                          ? 'bg-emerald-500 text-white hover:bg-emerald-400'
                          : 'bg-slate-600/50 text-slate-400 cursor-not-allowed'
                      )}
                    >
                      <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
                      </svg>
                      Save & Recalculate
                    </button>
                  </div>
                ) : (
                  <div className="text-center py-6" style={{ color: mutedColor }}>
                    <div className="text-sm mb-1">Market Priced</div>
                    <div className="text-xs">This instrument type uses market prices directly</div>
                  </div>
                )}
              </div>
            )}

            {/* Manual Override Input */}
            {activeTab === 'manual' && (
              <div className="mt-4 pt-4 border-t" style={{ borderColor }}>
                <div className="flex justify-between items-center mb-3">
                  <div className="text-xs font-semibold" style={{ color: mutedColor }}>Override Price</div>
                  {manualPriceModified && (
                    <span className="text-[10px] px-2 py-0.5 rounded bg-amber-500/20 text-amber-400">Modified</span>
                  )}
                </div>
                <div className="space-y-3">
                  <input
                    type="number"
                    value={manualPrice}
                    onChange={(e) => handleManualPriceChange(e.target.value)}
                    placeholder={`Current: ${position.lastPrice}`}
                    className="w-full px-3 py-2.5 rounded-lg text-sm font-mono"
                    style={{
                      background: isDarkMode ? '#0f172a' : '#fff',
                      border: `1px solid ${borderColor}`,
                      color: textColor,
                    }}
                  />
                  <button
                    onClick={() => handleSaveAndRecalculate('price')}
                    disabled={!manualPriceModified}
                    className={clsx(
                      'w-full py-2.5 rounded-lg text-sm font-semibold transition-all flex items-center justify-center gap-2',
                      manualPriceModified
                        ? 'bg-emerald-500 text-white hover:bg-emerald-400'
                        : 'bg-slate-600/50 text-slate-400 cursor-not-allowed'
                    )}
                  >
                    <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
                    </svg>
                    Save & Recalculate
                  </button>
                </div>
              </div>
            )}
          </div>

          {/* Trade History */}
          {position.tradeId && (
            <div className="mt-6">
              <div className="text-xs font-semibold uppercase tracking-wider mb-3" style={{ color: mutedColor }}>
                Recent Trades
              </div>
              <div
                className="rounded-lg p-3"
                style={{
                  background: isDarkMode ? '#0f172a' : '#f1f5f9',
                  border: `1px solid ${borderColor}`,
                }}
              >
                <div className="flex justify-between items-center">
                  <span className="text-xs font-mono" style={{ color: mutedColor }}>{position.tradeId}</span>
                  <span className="text-xs" style={{ color: mutedColor }}>{position.tradeDate}</span>
                </div>
              </div>
            </div>
          )}
        </div>
      </motion.div>
    </>
  )
}

// RiskPodTable Component
function RiskPodTable({
  data,
  showTradeColumns,
  onPositionClick,
  isDarkMode,
}: {
  data: RiskPodData
  showTradeColumns: boolean
  onPositionClick: (position: Position) => void
  isDarkMode: boolean
}) {
  const bgColor = isDarkMode ? 'rgba(15, 23, 42, 0.6)' : 'rgba(255, 255, 255, 0.8)'
  const borderColor = isDarkMode ? 'rgba(255, 255, 255, 0.05)' : 'rgba(0, 0, 0, 0.1)'
  const headerBg = isDarkMode ? 'rgba(255, 255, 255, 0.02)' : 'rgba(0, 0, 0, 0.02)'
  const textColor = isDarkMode ? '#e2e8f0' : '#1e293b'
  const mutedColor = '#64748b'

  if (data.positions.length === 0) {
    return (
      <div
        className="rounded-xl p-4 mb-6"
        style={{ background: bgColor, border: `1px solid ${borderColor}` }}
      >
        <div className="flex items-center justify-between mb-3">
          <h3 className="text-xl font-bold" style={{ color: data.color }}>{data.name}</h3>
          <span className="text-sm" style={{ color: mutedColor }}>0 positions</span>
        </div>
        <div className="text-center py-8" style={{ color: mutedColor }}>
          No {data.name.toLowerCase()} positions
        </div>
      </div>
    )
  }

  return (
    <div
      className="rounded-xl overflow-hidden mb-6"
      style={{ background: bgColor, border: `1px solid ${borderColor}` }}
    >
      {/* Table Header */}
      <div className="px-5 py-4" style={{ borderBottom: `1px solid ${borderColor}` }}>
        <div className="flex items-center gap-4 flex-wrap">
          <h3 className="text-xl font-bold" style={{ color: data.color }}>{data.name}</h3>
          <span className="text-sm" style={{ color: mutedColor }}>{data.positionCount} positions</span>
          <div className="flex items-center gap-5 ml-2 pl-4" style={{ borderLeft: `1px solid ${borderColor}` }}>
            <div>
              <span className="text-sm" style={{ color: mutedColor }}>Gross: </span>
              <span className="text-sm font-medium" style={{ color: textColor }}>{formatCurrency(data.grossExposure)}</span>
            </div>
            <div>
              <span className="text-sm" style={{ color: mutedColor }}>Net: </span>
              <span className="text-sm font-medium" style={{ color: data.netExposure >= 0 ? '#34d399' : '#f87171' }}>
                {formatCurrency(data.netExposure)}
              </span>
            </div>
            <div>
              <span className="text-sm" style={{ color: mutedColor }}>{data.primaryMetric.label}: </span>
              <span className="text-sm font-medium" style={{ color: textColor }}>{data.primaryMetric.value}</span>
            </div>
            {data.secondaryMetric && (
              <div>
                <span className="text-sm" style={{ color: mutedColor }}>{data.secondaryMetric.label}: </span>
                <span className="text-sm font-medium" style={{ color: textColor }}>{data.secondaryMetric.value}</span>
              </div>
            )}
          </div>
        </div>
      </div>

      {/* Table */}
      <div className="overflow-x-auto">
        <table className="w-full min-w-[1400px]">
          <thead style={{ background: headerBg }}>
            <tr>
              <th className="px-3 py-2.5 text-left text-[10px] font-semibold uppercase tracking-wider" style={{ color: mutedColor, width: '180px' }}>Name</th>
              <th className="px-3 py-2.5 text-left text-[10px] font-semibold uppercase tracking-wider" style={{ color: mutedColor, width: '80px' }}>Type</th>
              <th className="px-3 py-2.5 text-left text-[10px] font-semibold uppercase tracking-wider" style={{ color: mutedColor, width: '50px' }}>Ccy</th>
              <th className="px-3 py-2.5 text-right text-[10px] font-semibold uppercase tracking-wider" style={{ color: mutedColor, width: '100px' }}>Quantity</th>
              <th className="px-3 py-2.5 text-left text-[10px] font-semibold uppercase tracking-wider" style={{ color: mutedColor, width: '120px' }}>Portfolio</th>
              <th className="px-3 py-2.5 text-left text-[10px] font-semibold uppercase tracking-wider" style={{ color: mutedColor, width: '90px' }}>PM</th>
              {showTradeColumns && (
                <>
                  <th className="px-3 py-2.5 text-left text-[10px] font-semibold uppercase tracking-wider" style={{ color: mutedColor, width: '90px' }}>Trade ID</th>
                  <th className="px-3 py-2.5 text-left text-[10px] font-semibold uppercase tracking-wider" style={{ color: mutedColor, width: '100px' }}>Trade Date</th>
                </>
              )}
              <th className="px-3 py-2.5 text-right text-[10px] font-semibold uppercase tracking-wider" style={{ color: mutedColor, width: '90px' }}>Entry</th>
              <th className="px-3 py-2.5 text-right text-[10px] font-semibold uppercase tracking-wider" style={{ color: mutedColor, width: '90px' }}>Last</th>
              <th className="px-3 py-2.5 text-center text-[10px] font-semibold uppercase tracking-wider" style={{ color: mutedColor, width: '70px' }}>Pricing</th>
              <th className="px-3 py-2.5 text-right text-[10px] font-semibold uppercase tracking-wider" style={{ color: mutedColor, width: '90px' }}>PNL</th>
              <th className="px-3 py-2.5 text-right text-[10px] font-semibold uppercase tracking-wider" style={{ color: mutedColor, width: '100px' }}>Mkt Value</th>
              <th className="px-3 py-2.5 text-right text-[10px] font-semibold uppercase tracking-wider" style={{ color: mutedColor, width: '70px' }}>Correl</th>
              <th className="px-3 py-2.5 text-center text-[10px] font-semibold uppercase tracking-wider" style={{ color: mutedColor, width: '60px' }}>Hedge</th>
            </tr>
          </thead>
          <tbody>
            {data.positions.map((position) => (
              <tr
                key={position.id}
                onClick={() => onPositionClick(position)}
                className="cursor-pointer transition-colors"
                style={{ borderTop: `1px solid ${isDarkMode ? 'rgba(255, 255, 255, 0.03)' : 'rgba(0, 0, 0, 0.05)'}` }}
                onMouseEnter={(e) => e.currentTarget.style.background = isDarkMode ? 'rgba(255, 255, 255, 0.02)' : 'rgba(0, 0, 0, 0.02)'}
                onMouseLeave={(e) => e.currentTarget.style.background = 'transparent'}
              >
                <td className="px-3 py-3">
                  <div className="flex items-center gap-2">
                    {position.hasManualOverride && (
                      <div
                        className="w-5 h-5 rounded-full bg-amber-500 flex items-center justify-center text-black font-bold text-xs flex-shrink-0"
                        title={position.overrideType === 'model' ? 'Model inputs modified' : 'Manual price override'}
                      >
                        !
                      </div>
                    )}
                    <div className="font-medium text-sm hover:text-blue-400 transition-colors" style={{ color: textColor }}>
                      {position.name}
                    </div>
                  </div>
                </td>
                <td className="px-3 py-3">
                  <span
                    className="inline-block px-1.5 py-0.5 rounded text-[10px] font-semibold uppercase"
                    style={{
                      background: instTypeStyles[position.type]?.bg,
                      color: instTypeStyles[position.type]?.text,
                    }}
                  >
                    {position.type}
                  </span>
                </td>
                <td className="px-3 py-3">
                  <span
                    className="inline-block px-1.5 py-0.5 rounded text-[10px] font-semibold"
                    style={{
                      background: currencyStyles[position.currency]?.bg || 'rgba(100, 116, 139, 0.15)',
                      color: currencyStyles[position.currency]?.text || '#94a3b8',
                    }}
                  >
                    {position.currency}
                  </span>
                </td>
                <td className="px-3 py-3 text-right">
                  <span
                    className="font-mono text-sm"
                    style={{ color: position.quantity >= 0 ? '#34d399' : '#f87171' }}
                  >
                    {formatQuantity(position.quantity)}
                  </span>
                </td>
                <td className="px-3 py-3">
                  <span
                    className="inline-block px-2 py-1 rounded text-[11px] font-semibold text-white"
                    style={{ background: position.portfolioColor, border: `1px solid ${position.portfolioColor}80` }}
                  >
                    {position.portfolio}
                  </span>
                </td>
                <td className="px-3 py-3 text-sm" style={{ color: mutedColor }}>
                  {position.pm}
                </td>
                {showTradeColumns && (
                  <>
                    <td className="px-3 py-3 text-sm font-mono" style={{ color: mutedColor }}>
                      {position.tradeId || '-'}
                    </td>
                    <td className="px-3 py-3 text-sm" style={{ color: mutedColor }}>
                      {position.tradeDate || '-'}
                    </td>
                  </>
                )}
                <td className="px-3 py-3 text-right">
                  <span className="font-mono text-sm" style={{ color: textColor }}>
                    {formatPrice(position.entryPrice, position.type)}
                  </span>
                </td>
                <td className="px-3 py-3 text-right">
                  <span className="font-mono text-sm" style={{ color: textColor }}>
                    {formatPrice(position.lastPrice, position.type)}
                  </span>
                </td>
                <td className="px-3 py-3 text-center">
                  <span
                    className="inline-block px-2 py-0.5 rounded text-[10px] font-semibold"
                    style={{
                      background: position.pricingType === 'market' ? 'rgba(34, 197, 94, 0.15)' : 'rgba(245, 158, 11, 0.15)',
                      color: position.pricingType === 'market' ? '#22c55e' : '#f59e0b',
                    }}
                  >
                    {position.pricingType.charAt(0).toUpperCase() + position.pricingType.slice(1)}
                  </span>
                </td>
                <td className="px-3 py-3 text-right">
                  <span
                    className="font-mono text-sm"
                    style={{ color: position.pnl >= 0 ? '#34d399' : '#f87171' }}
                  >
                    {position.pnl >= 0 ? '+' : ''}{formatCurrency(position.pnl)}
                  </span>
                </td>
                <td className="px-3 py-3 text-right">
                  <span
                    className="font-mono text-sm"
                    style={{ color: position.marketValue >= 0 ? '#34d399' : '#f87171' }}
                  >
                    {formatCurrency(position.marketValue)}
                  </span>
                </td>
                <td className="px-3 py-3 text-right">
                  <span
                    className="font-mono text-sm"
                    style={{ color: position.correlation > 0.8 ? '#f87171' : position.correlation > 0.5 ? '#fbbf24' : '#22c55e' }}
                  >
                    {position.correlation.toFixed(2)}
                  </span>
                </td>
                <td className="px-3 py-3 text-center">
                  <span
                    className="inline-flex items-center justify-center w-6 h-6 rounded text-[11px] font-bold"
                    style={{
                      background: position.isHedged ? 'rgba(59, 130, 246, 0.15)' : 'rgba(100, 116, 139, 0.1)',
                      color: position.isHedged ? '#3b82f6' : mutedColor,
                    }}
                  >
                    {position.isHedged ? 'H' : '-'}
                  </span>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  )
}

// Main Component
export default function TradesNew() {
  const { isDarkMode } = useTheme()

  // State
  const [viewMode, setViewMode] = useState<'positions' | 'trades'>('positions')
  const [selectedPortfolios, setSelectedPortfolios] = useState<string[]>([])
  const [selectedTime, setSelectedTime] = useState(DEFAULT_TIME_PRESETS[0])
  const [lastCalculated, setLastCalculated] = useState('Just now')
  const [selectedPosition, setSelectedPosition] = useState<Position | null>(null)

  // All portfolios
  const allPortfolios = useMemo(() => [
    { id: 'alpha', name: 'Alpha Growth', color: '#3b82f6' },
    { id: 'beta', name: 'Beta Momentum', color: '#8b5cf6' },
    { id: 'gamma', name: 'Gamma Value', color: '#f59e0b' },
    { id: 'delta', name: 'Delta Quant', color: '#06b6d4' },
    { id: 'epsilon', name: 'Epsilon Macro', color: '#ec4899' },
    { id: 'zeta', name: 'Zeta Credit', color: '#10b981' },
    { id: 'eta', name: 'Eta Rates', color: '#f97316' },
    { id: 'theta', name: 'Theta Vol', color: '#6366f1' },
  ], [])

  // Initialize selected portfolios
  useEffect(() => {
    if (selectedPortfolios.length === 0) {
      setSelectedPortfolios(allPortfolios.map(p => p.id))
    }
  }, [allPortfolios])

  // Track position overrides
  const [positionOverrides, setPositionOverrides] = useState<Record<string, { hasManualOverride: boolean; overrideType?: 'price' | 'model' }>>({})

  // Handlers
  const handleCalculate = async () => {
    // Simulate calculation
    await new Promise(resolve => setTimeout(resolve, 1500))
    setLastCalculated('Just now')
  }

  const handleTimeSelect = (preset: typeof DEFAULT_TIME_PRESETS[0]) => {
    setSelectedTime(preset)
  }

  const handleUpdatePosition = (updatedPosition: Position) => {
    // Update the overrides tracking
    setPositionOverrides(prev => ({
      ...prev,
      [updatedPosition.id]: {
        hasManualOverride: updatedPosition.hasManualOverride || false,
        overrideType: updatedPosition.overrideType,
      }
    }))

    // Update selected position if it's the one being modified
    if (selectedPosition?.id === updatedPosition.id) {
      setSelectedPosition(updatedPosition)
    }
  }

  // Helper to get position with override status
  const getPositionWithOverrides = (position: Position): Position => {
    const override = positionOverrides[position.id]
    if (override) {
      return {
        ...position,
        hasManualOverride: override.hasManualOverride,
        overrideType: override.overrideType,
      }
    }
    return position
  }

  // Colors based on theme
  const bgColor = isDarkMode ? undefined : '#D9D9D9'
  const headerBg = isDarkMode ? 'rgba(15, 23, 42, 0.95)' : '#ECECEC'
  const textColor = isDarkMode ? '#e2e8f0' : '#1e293b'
  const borderColor = isDarkMode ? 'rgba(255, 255, 255, 0.1)' : '#e2e8f0'

  return (
    <div
      className="h-full flex flex-col"
      style={{ background: bgColor, color: textColor }}
    >
      {/* Page Header */}
      <header
        className="sticky top-0 z-50"
        style={{
          background: headerBg,
          borderBottom: `1px solid ${borderColor}`,
          padding: '12px 20px',
        }}
      >
        <div className="flex justify-between items-center mb-3">
          <h1 className="text-xl font-semibold" style={{ color: textColor }}>Positions & Trades</h1>
        </div>

        <div className="flex items-center gap-4 flex-wrap">
          {/* View Toggle */}
          <div
            className="flex rounded-lg p-0.5 gap-0.5"
            style={{
              background: isDarkMode ? 'rgba(30, 41, 59, 0.8)' : 'rgba(0, 0, 0, 0.1)',
              border: `1px solid ${isDarkMode ? 'rgba(255, 255, 255, 0.15)' : 'rgba(0, 0, 0, 0.1)'}`,
            }}
          >
            {['positions', 'trades'].map((mode) => (
              <button
                key={mode}
                onClick={() => setViewMode(mode as typeof viewMode)}
                className={clsx(
                  'px-4 py-1.5 rounded-md text-sm font-medium transition-all',
                  viewMode === mode
                    ? 'bg-blue-500 text-white shadow-md'
                    : isDarkMode
                      ? 'text-slate-400 hover:text-white hover:bg-white/5'
                      : 'text-slate-600 hover:text-slate-900 hover:bg-black/5'
                )}
              >
                {mode.charAt(0).toUpperCase() + mode.slice(1)}
              </button>
            ))}
          </div>

          {/* Time Selector */}
          <TimeSelector
            selectedPreset={selectedTime}
            onSelect={handleTimeSelect}
            presets={DEFAULT_TIME_PRESETS}
          />

          {/* Calculate Button */}
          <CalculateButton
            onCalculate={handleCalculate}
            timestamp={lastCalculated}
            isHistorical={selectedTime.isHistorical}
          />

          {/* Portfolio Selector */}
          <PortfolioSelector
            portfolios={allPortfolios}
            selectedIds={selectedPortfolios}
            onChange={setSelectedPortfolios}
          />
        </div>
      </header>

      {/* Historical Banner */}
      <AnimatePresence>
        {selectedTime.isHistorical && (
          <motion.div
            initial={{ height: 0, opacity: 0 }}
            animate={{ height: 'auto', opacity: 1 }}
            exit={{ height: 0, opacity: 0 }}
            className="mx-5 mt-4"
          >
            <div
              className="flex items-center gap-3 px-4 py-3 rounded-lg"
              style={{
                background: 'linear-gradient(135deg, rgba(245, 158, 11, 0.1) 0%, rgba(245, 158, 11, 0.05) 100%)',
                border: '1px solid rgba(245, 158, 11, 0.3)',
              }}
            >
              <span className="text-xl">🕐</span>
              <div className="flex-1">
                <div className="text-sm font-semibold text-amber-400">Viewing Historical Data</div>
                <div className="text-xs text-amber-300/80">As of {selectedTime.sublabel || selectedTime.label}</div>
              </div>
              <button
                onClick={() => setSelectedTime(DEFAULT_TIME_PRESETS[0])}
                className="px-3 py-1.5 rounded-lg border border-amber-500/50 text-amber-400 text-xs font-semibold hover:bg-amber-500/20"
              >
                Return to Live
              </button>
            </div>
          </motion.div>
        )}
      </AnimatePresence>

      {/* Main Content - RiskPod Tables */}
      <main className="flex-1 overflow-y-auto p-6">
        {Object.entries(riskPodConfigs).map(([key, data]) => (
          <RiskPodTable
            key={key}
            data={{
              ...data,
              positions: data.positions.map(p => getPositionWithOverrides(p))
            }}
            showTradeColumns={viewMode === 'trades'}
            onPositionClick={setSelectedPosition}
            isDarkMode={isDarkMode}
          />
        ))}
      </main>

      {/* Position Drilldown Panel */}
      <AnimatePresence>
        {selectedPosition && (
          <PositionDrilldownPanel
            position={getPositionWithOverrides(selectedPosition)}
            onClose={() => setSelectedPosition(null)}
            isDarkMode={isDarkMode}
            onUpdatePosition={handleUpdatePosition}
          />
        )}
      </AnimatePresence>
    </div>
  )
}
