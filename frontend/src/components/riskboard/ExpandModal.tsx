import { RiskCardData } from './RiskCardNew'
import './riskboard.css'

// Asset class configuration (duplicated for standalone use)
const ASSET_CLASS_CONFIG: Record<string, {
  color: string
  colorClass: string
  primaryMetric: string
  metrics: { label: string }[]
  tableHeaders: { label: string }[]
  regions: { key: string; label: string }[]
}> = {
  equity: {
    color: '#3b82f6',
    colorClass: 'blue',
    primaryMetric: 'Net Delta',
    metrics: [{ label: 'Beta' }, { label: 'Vega' }, { label: 'Gamma' }],
    tableHeaders: [
      { label: '%' }, { label: 'DELTA' }, { label: 'BETA' }, { label: 'VEGA' }, { label: 'CORR.' }, { label: '0HEDGE' },
    ],
    regions: [
      { key: 'us_can', label: 'US+CAN' },
      { key: 'europe', label: 'Europe' },
      { key: 'japan', label: 'Japan' },
      { key: 'se_asia', label: 'SE Asia' },
      { key: 'row', label: 'RoW' },
    ],
  },
  rates: {
    color: '#22c55e',
    colorClass: 'green',
    primaryMetric: 'Net DV01',
    metrics: [{ label: 'Dur' }, { label: 'Convex' }, { label: 'Carry' }],
    tableHeaders: [
      { label: '%' }, { label: 'DV01' }, { label: 'DUR' }, { label: 'CONV' }, { label: 'CORR.' }, { label: '0HEDGE' },
    ],
    regions: [
      { key: '0_2y', label: '0-2Y' },
      { key: '2_5y', label: '2-5Y' },
      { key: '5_10y', label: '5-10Y' },
      { key: '10_30y', label: '10-30Y' },
      { key: 'tips', label: 'TIPS' },
    ],
  },
  credit: {
    color: '#a855f7',
    colorClass: 'purple',
    primaryMetric: 'Net CS01',
    metrics: [{ label: 'Spread' }, { label: 'JTD' }, { label: 'Carry' }],
    tableHeaders: [
      { label: '%' }, { label: 'CS01' }, { label: 'SPR' }, { label: 'JTD' }, { label: 'CORR.' }, { label: '0HEDGE' },
    ],
    regions: [
      { key: 'ig', label: 'IG' },
      { key: 'hy', label: 'HY' },
      { key: 'em', label: 'EM' },
      { key: 'cds', label: 'CDS' },
    ],
  },
  fx: {
    color: '#06b6d4',
    colorClass: 'cyan',
    primaryMetric: 'Net FX Delta',
    metrics: [{ label: 'Vol' }, { label: 'Vega' }, { label: 'Carry' }],
    tableHeaders: [
      { label: '%' }, { label: 'DELTA' }, { label: 'VOL' }, { label: 'VEGA' }, { label: 'CORR.' }, { label: '0HEDGE' },
    ],
    regions: [
      { key: 'eur', label: 'EUR' },
      { key: 'jpy', label: 'JPY' },
      { key: 'gbp', label: 'GBP' },
      { key: 'em', label: 'EM' },
    ],
  },
  commodities: {
    color: '#f97316',
    colorClass: 'orange',
    primaryMetric: 'Net Delta',
    metrics: [{ label: 'Vol' }, { label: 'Vega' }, { label: 'Carry' }],
    tableHeaders: [
      { label: '%' }, { label: 'DELTA' }, { label: 'VOL' }, { label: 'VEGA' }, { label: 'CORR.' }, { label: '0HEDGE' },
    ],
    regions: [
      { key: 'energy', label: 'Energy' },
      { key: 'metals', label: 'Metals' },
      { key: 'agri', label: 'Agri' },
      { key: 'other', label: 'Other' },
    ],
  },
  other: {
    color: '#94a3b8',
    colorClass: 'gray',
    primaryMetric: 'Net Exposure',
    metrics: [{ label: 'Vol' }, { label: 'Vega' }, { label: 'Theta' }],
    tableHeaders: [
      { label: '%' }, { label: 'DELTA' }, { label: 'VOL' }, { label: 'VEGA' }, { label: 'CORR.' }, { label: '0HEDGE' },
    ],
    regions: [
      { key: 'crypto', label: 'Crypto' },
      { key: 'vol', label: 'Vol' },
      { key: 'struct', label: 'Struct' },
      { key: 'other', label: 'Other' },
    ],
  },
}

interface ExpandModalProps {
  isOpen: boolean
  onClose: () => void
  data: RiskCardData | null
}

export default function ExpandModal({ isOpen, onClose, data }: ExpandModalProps) {
  if (!isOpen || !data) return null

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
    <div className="expand-modal active" onClick={onClose}>
      <div className="expand-modal-content" onClick={(e) => e.stopPropagation()}>
        <button className="expand-modal-close" onClick={onClose}>×</button>

        <div className="riskcard expanded">
          {/* Card Header */}
          <div className="card-header">
            <span className={`card-title ${config.colorClass}`}>
              {data.assetClass.toUpperCase()}
            </span>
            <div className="header-right">
              <span className={`card-change ${data.changeDirection}`}>
                {data.changeDirection === 'up' ? '▲ +' : data.changeDirection === 'down' ? '▼ -' : ''}
                {Math.abs(data.change).toFixed(1)}%
              </span>
            </div>
          </div>

          {/* Primary Metric */}
          <div className="primary-metric">
            <div className="primary-label">{config.primaryMetric}</div>
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
              <div key={metric.label} className="metric-box">
                <div className="metric-label">{metric.label}</div>
                <div className="metric-value">{data.metrics[i]?.value || '-'}</div>
              </div>
            ))}
          </div>

          {/* Table */}
          <div className="table-container expanded">
            <div className="table-header">
              <span></span>
              {config.tableHeaders.map((header) => (
                <span key={header.label} className={`th-${config.colorClass}`}>
                  {header.label}
                </span>
              ))}
            </div>
            <div className="table-body expanded">
              {config.regions.map((region, rowIndex) => {
                const rowData = data.tableData[rowIndex] || { values: [] }
                return (
                  <div key={region.key} className="table-row">
                    <div className={`row-label ${config.colorClass}`}>
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
            <div className="bottom-metric">
              <div className="bottom-label">Positions</div>
              <div className="bottom-value">{data.positions.toLocaleString()}</div>
            </div>
            <div className="bottom-metric">
              <div className="bottom-label">VAR (95%)</div>
              <div className={`bottom-value ${data.var95 < 0 ? 'negative' : ''}`}>
                {formatValue(data.var95)}
              </div>
            </div>
            <div className="bottom-metric">
              <div className="bottom-label">CVAR (95%)</div>
              <div className={`bottom-value ${data.cvar95 < 0 ? 'negative' : ''}`}>
                {formatValue(data.cvar95)}
              </div>
            </div>
          </div>

          {/* Footer */}
          <div className="footer-row">
            <div className="footer-item">
              <div className="footer-label">Gross Exposure</div>
              <div className="footer-value">{formatValue(data.grossExposure)}</div>
            </div>
            <div className="footer-item">
              <div className="footer-label">Net Exposure</div>
              <div className="footer-value">{formatValue(data.netExposure)}</div>
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}
