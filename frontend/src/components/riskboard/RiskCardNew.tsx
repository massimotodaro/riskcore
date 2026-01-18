import { useState } from 'react'
import './riskboard.css'

// Asset class configuration
const ASSET_CLASS_CONFIG: Record<string, {
  color: string
  colorClass: string
  primaryMetric: string
  primaryMetricTooltip: string
  metrics: { label: string; tooltip: string }[]
  tableHeaders: { label: string; tooltip: string }[]
  regions: { key: string; label: string; tooltip: string }[]
}> = {
  equity: {
    color: '#3b82f6',
    colorClass: 'blue',
    primaryMetric: 'Net Delta',
    primaryMetricTooltip: 'Net delta exposure to equity markets',
    metrics: [
      { label: 'Beta', tooltip: 'Portfolio beta to S&P 500' },
      { label: 'Vega', tooltip: 'Option vega exposure' },
      { label: 'Gamma', tooltip: 'Option gamma exposure' },
    ],
    tableHeaders: [
      { label: '%', tooltip: '% of total equity exposure' },
      { label: 'DELTA', tooltip: 'Net delta by region' },
      { label: 'BETA', tooltip: 'Regional beta vs SPX' },
      { label: 'VEGA', tooltip: 'Option vega by region' },
      { label: 'CORR.', tooltip: 'Correlation to regional anchor' },
      { label: '0HEDGE', tooltip: 'Notional to zero exposure' },
    ],
    regions: [
      { key: 'us_can', label: 'US+CAN', tooltip: 'US & Canada equities. Anchor: SPY' },
      { key: 'europe', label: 'Europe', tooltip: 'European equities. Anchor: VGK' },
      { key: 'japan', label: 'Japan', tooltip: 'Japanese equities. Anchor: EWJ' },
      { key: 'se_asia', label: 'SE Asia', tooltip: 'Southeast Asia equities. Anchor: VWO' },
      { key: 'row', label: 'RoW', tooltip: 'Rest of World equities' },
    ],
  },
  rates: {
    color: '#22c55e',
    colorClass: 'green',
    primaryMetric: 'Net DV01',
    primaryMetricTooltip: 'Net dollar value of 1bp rate move',
    metrics: [
      { label: 'Dur', tooltip: 'Portfolio duration in years' },
      { label: 'Convex', tooltip: 'Portfolio convexity' },
      { label: 'Carry', tooltip: 'Annual carry in bps' },
    ],
    tableHeaders: [
      { label: '%', tooltip: '% of total rates exposure' },
      { label: 'DV01', tooltip: 'DV01 by tenor bucket' },
      { label: 'DUR', tooltip: 'Duration by bucket' },
      { label: 'CONV', tooltip: 'Convexity by bucket' },
      { label: 'CORR.', tooltip: 'Correlation to ZN (10Y)' },
      { label: '0HEDGE', tooltip: 'Notional to zero exposure' },
    ],
    regions: [
      { key: '0_2y', label: '0-2Y', tooltip: 'Short-end rates. Anchor: ZT' },
      { key: '2_5y', label: '2-5Y', tooltip: 'Intermediate rates. Anchor: ZF' },
      { key: '5_10y', label: '5-10Y', tooltip: 'Long rates. Anchor: ZN' },
      { key: '10_30y', label: '10-30Y', tooltip: 'Ultra-long rates. Anchor: ZB' },
      { key: 'tips', label: 'TIPS', tooltip: 'Inflation-linked bonds' },
    ],
  },
  credit: {
    color: '#a855f7',
    colorClass: 'purple',
    primaryMetric: 'Net CS01',
    primaryMetricTooltip: 'Net dollar value of 1bp spread move',
    metrics: [
      { label: 'Spread', tooltip: 'Weighted avg spread in bps' },
      { label: 'JTD', tooltip: 'Jump to default exposure' },
      { label: 'Carry', tooltip: 'Annual carry in bps' },
    ],
    tableHeaders: [
      { label: '%', tooltip: '% of total credit exposure' },
      { label: 'CS01', tooltip: 'CS01 by rating bucket' },
      { label: 'SPR', tooltip: 'Average spread by bucket' },
      { label: 'JTD', tooltip: 'Jump-to-default by bucket' },
      { label: 'CORR.', tooltip: 'Correlation to CDX index' },
      { label: '0HEDGE', tooltip: 'Notional to zero exposure' },
    ],
    regions: [
      { key: 'ig', label: 'IG', tooltip: 'Investment Grade (AAA-BBB). Anchor: CDX.IG' },
      { key: 'hy', label: 'HY', tooltip: 'High Yield (BB-CCC). Anchor: CDX.HY' },
      { key: 'em', label: 'EM', tooltip: 'Emerging Market credit' },
      { key: 'cds', label: 'CDS', tooltip: 'Credit Default Swaps' },
    ],
  },
  fx: {
    color: '#06b6d4',
    colorClass: 'cyan',
    primaryMetric: 'Net FX Delta',
    primaryMetricTooltip: 'Net FX exposure across all currency pairs',
    metrics: [
      { label: 'Vol', tooltip: 'Implied volatility' },
      { label: 'Vega', tooltip: 'FX option vega' },
      { label: 'Carry', tooltip: 'Net carry in bps' },
    ],
    tableHeaders: [
      { label: '%', tooltip: '% of total FX exposure' },
      { label: 'DELTA', tooltip: 'Net delta by currency' },
      { label: 'VOL', tooltip: 'Implied vol' },
      { label: 'VEGA', tooltip: 'Option vega' },
      { label: 'CORR.', tooltip: 'Correlation to DXY' },
      { label: '0HEDGE', tooltip: 'Notional to zero exposure' },
    ],
    regions: [
      { key: 'eur', label: 'EUR', tooltip: 'Euro exposure. Anchor: EUR/USD' },
      { key: 'jpy', label: 'JPY', tooltip: 'Japanese Yen. Anchor: USD/JPY' },
      { key: 'gbp', label: 'GBP', tooltip: 'British Pound. Anchor: GBP/USD' },
      { key: 'em', label: 'EM', tooltip: 'Emerging Market currencies' },
    ],
  },
  commodities: {
    color: '#f97316',
    colorClass: 'orange',
    primaryMetric: 'Net Delta',
    primaryMetricTooltip: 'Net commodity exposure across all positions',
    metrics: [
      { label: 'Vol', tooltip: 'Implied volatility' },
      { label: 'Vega', tooltip: 'Option vega' },
      { label: 'Carry', tooltip: 'Roll yield / contango' },
    ],
    tableHeaders: [
      { label: '%', tooltip: '% of total commodity exposure' },
      { label: 'DELTA', tooltip: 'Net delta by sector' },
      { label: 'VOL', tooltip: 'Implied volatility' },
      { label: 'VEGA', tooltip: 'Option vega' },
      { label: 'CORR.', tooltip: 'Correlation to benchmark' },
      { label: '0HEDGE', tooltip: 'Notional to zero exposure' },
    ],
    regions: [
      { key: 'energy', label: 'Energy', tooltip: 'Oil, Gas, Coal. Anchor: CL' },
      { key: 'metals', label: 'Metals', tooltip: 'Gold, Silver, Copper. Anchor: GC' },
      { key: 'agri', label: 'Agri', tooltip: 'Grains, Softs, Livestock' },
      { key: 'other', label: 'Other', tooltip: 'Other commodities' },
    ],
  },
  other: {
    color: '#94a3b8',
    colorClass: 'gray',
    primaryMetric: 'Net Exposure',
    primaryMetricTooltip: 'Net exposure to other asset classes (crypto, vol, etc.)',
    metrics: [
      { label: 'Vol', tooltip: 'Portfolio volatility' },
      { label: 'Vega', tooltip: 'Option vega' },
      { label: 'Theta', tooltip: 'Time decay' },
    ],
    tableHeaders: [
      { label: '%', tooltip: '% of total exposure' },
      { label: 'DELTA', tooltip: 'Net delta' },
      { label: 'VOL', tooltip: 'Implied volatility' },
      { label: 'VEGA', tooltip: 'Option vega' },
      { label: 'CORR.', tooltip: 'Cross-correlation' },
      { label: '0HEDGE', tooltip: 'Notional to zero exposure' },
    ],
    regions: [
      { key: 'crypto', label: 'Crypto', tooltip: 'Cryptocurrency' },
      { key: 'vol', label: 'Vol', tooltip: 'Volatility products' },
      { key: 'struct', label: 'Struct', tooltip: 'Structured notes' },
      { key: 'other', label: 'Other', tooltip: 'Other instruments' },
    ],
  },
}

export interface RiskCardData {
  assetClass: string
  primaryValue: number
  change: number
  changeDirection: 'up' | 'down' | 'flat'
  metrics: { value: string }[]
  tableData: {
    region: string
    values: (string | number)[]
  }[]
  positions: number
  var95: number
  cvar95: number
  grossExposure: number
  netExposure: number
  hasOverrides?: boolean
  barPercent?: number
}

interface RiskCardProps {
  data: RiskCardData
  onTradesClick?: () => void
  onExpandClick?: () => void
  onOverridesClick?: () => void
  onMetricClick?: (metricName: string) => void
}

export default function RiskCardNew({ data, onTradesClick, onExpandClick, onOverridesClick, onMetricClick }: RiskCardProps) {
  const [isHovered, setIsHovered] = useState(false)
  const config = ASSET_CLASS_CONFIG[data.assetClass] || ASSET_CLASS_CONFIG.other

  const formatValue = (value: number, prefix = '$'): string => {
    const absValue = Math.abs(value)
    if (absValue >= 1_000_000_000) {
      return `${prefix}${(value / 1_000_000_000).toFixed(2)}B`
    }
    if (absValue >= 1_000_000) {
      return `${prefix}${(value / 1_000_000).toFixed(1)}M`
    }
    if (absValue >= 1_000) {
      return `${prefix}${(value / 1_000).toFixed(0)}K`
    }
    return `${prefix}${value.toFixed(0)}`
  }

  return (
    <div
      className="riskcard"
      onMouseEnter={() => setIsHovered(true)}
      onMouseLeave={() => setIsHovered(false)}
      style={{
        transform: isHovered ? 'translateY(-2px)' : 'none',
        boxShadow: isHovered ? '0 8px 24px rgba(0, 0, 0, 0.3)' : 'none',
        borderColor: isHovered ? 'rgba(255, 255, 255, 0.2)' : 'rgba(255, 255, 255, 0.1)',
      }}
    >
      {/* Card Header */}
      <div className="card-header">
        <span className={`card-title ${config.colorClass}`} title={`${data.assetClass} exposure`}>
          {data.assetClass.toUpperCase()}
        </span>
        <div className="header-right">
          {data.hasOverrides && (
            <button
              className="card-warning visible"
              onClick={onOverridesClick}
              title="Manual price overrides active"
            >
              <span>!</span>
            </button>
          )}
          <span className={`card-change ${data.changeDirection}`}>
            {data.changeDirection === 'up' ? '▲ +' : data.changeDirection === 'down' ? '▼ -' : ''}
            {Math.abs(data.change).toFixed(1)}%
          </span>
          <button className="btn-icon" title="Enlarge" onClick={onExpandClick}>
            <span style={{ fontSize: '14px' }}>&#x26F6;</span>
          </button>
          <button className={`btn-icon btn-trades ${config.colorClass}`} title="View Trades" onClick={onTradesClick}>
            Trades
          </button>
        </div>
      </div>

      {/* Primary Metric */}
      <div className="primary-metric" style={{ background: `rgba(30, 60, 50, 0.5)` }}>
        <div className="primary-label" title={config.primaryMetricTooltip}>
          {config.primaryMetric}
        </div>
        <div className="primary-value">{formatValue(data.primaryValue)}</div>
        <div className="primary-bar">
          <div
            className={`primary-bar-fill ${data.assetClass}`}
            style={{ width: `${data.barPercent || 50}%` }}
          />
        </div>
      </div>

      {/* Metrics Row */}
      <div className="metrics-row">
        {config.metrics.map((metric, i) => (
          <div
            key={metric.label}
            className="metric-box clickable-metric"
            onClick={(e) => {
              e.stopPropagation()
              onMetricClick?.(metric.label)
            }}
          >
            <div className="metric-label" title={metric.tooltip}>
              {metric.label}
            </div>
            <div className="metric-value">{data.metrics[i]?.value || '-'}</div>
          </div>
        ))}
      </div>

      {/* Table */}
      <div className="table-container">
        <div className="table-header">
          <span></span>
          {config.tableHeaders.map((header) => (
            <span key={header.label} className={`th-${config.colorClass}`} title={header.tooltip}>
              {header.label}
            </span>
          ))}
        </div>
        <div className="table-body">
          {config.regions.map((region, rowIndex) => {
            const rowData = data.tableData[rowIndex] || { values: [] }
            return (
              <div key={region.key} className="table-row">
                <div className={`row-label ${config.colorClass}`} title={region.tooltip}>
                  {region.label}
                </div>
                {rowData.values.map((val, i) => (
                  <span key={i}>{val}</span>
                ))}
              </div>
            )
          })}
        </div>
      </div>

      {/* Bottom Metrics */}
      <div className="bottom-metrics">
        <div
          className="bottom-metric clickable-metric"
          onClick={(e) => {
            e.stopPropagation()
            onMetricClick?.('Positions')
          }}
        >
          <div className="bottom-label" title="Total positions">
            Positions
          </div>
          <div className="bottom-value">{data.positions.toLocaleString()}</div>
        </div>
        <div
          className="bottom-metric clickable-metric"
          onClick={(e) => {
            e.stopPropagation()
            onMetricClick?.('VAR (95%)')
          }}
        >
          <div className="bottom-label" title="Value at Risk 95%">
            VAR (95%)
          </div>
          <div className={`bottom-value ${data.var95 < 0 ? 'negative' : ''}`}>
            {formatValue(data.var95)}
          </div>
        </div>
        <div
          className="bottom-metric clickable-metric"
          onClick={(e) => {
            e.stopPropagation()
            onMetricClick?.('CVAR (95%)')
          }}
        >
          <div className="bottom-label" title="Conditional VAR 95%">
            CVAR (95%)
          </div>
          <div className={`bottom-value ${data.cvar95 < 0 ? 'negative' : ''}`}>
            {formatValue(data.cvar95)}
          </div>
        </div>
      </div>

      {/* Footer */}
      <div className="footer-row">
        <div
          className="footer-item clickable-metric"
          onClick={(e) => {
            e.stopPropagation()
            onMetricClick?.('Gross Exposure')
          }}
        >
          <div className="footer-label">Gross Exposure</div>
          <div className="footer-value">{formatValue(data.grossExposure)}</div>
        </div>
        <div
          className="footer-item clickable-metric"
          onClick={(e) => {
            e.stopPropagation()
            onMetricClick?.('Net Exposure')
          }}
        >
          <div className="footer-label">Net Exposure</div>
          <div className="footer-value">{formatValue(data.netExposure)}</div>
        </div>
      </div>
    </div>
  )
}
