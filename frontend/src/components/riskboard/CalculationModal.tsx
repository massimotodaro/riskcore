import './riskboard.css'

// Calculation definitions for each metric
const CALCULATIONS: Record<string, {
  title: string
  lines: { label: string; value: string }[]
}> = {
  'Beta': {
    title: 'Portfolio Beta Calculation',
    lines: [
      { label: 'Methodology', value: 'Weighted Average Beta' },
      { label: 'Benchmark', value: 'S&P 500 (SPY)' },
      { label: 'Lookback Period', value: '252 trading days' },
      { label: 'Position 1 (AAPL)', value: '$12.5M × 1.25 = $15.6M beta-adj' },
      { label: 'Position 2 (MSFT)', value: '$8.2M × 1.15 = $9.4M beta-adj' },
      { label: 'Position 3 (GOOGL)', value: '$6.8M × 1.08 = $7.3M beta-adj' },
      { label: '... (339 more positions)', value: '' },
      { label: 'Total Beta-Adj Exposure', value: '$48.8M' },
      { label: 'Total Notional', value: '$42.5M' },
      { label: 'Portfolio Beta', value: '1.15' },
    ],
  },
  'Vega': {
    title: 'Portfolio Vega Calculation',
    lines: [
      { label: 'Methodology', value: 'Sum of Option Vegas' },
      { label: 'Vol Surface', value: 'SABR interpolated' },
      { label: 'SPY Calls (Mar 580)', value: '+$125K vega' },
      { label: 'QQQ Puts (Mar 480)', value: '-$45K vega' },
      { label: 'AAPL Calls (Feb 185)', value: '+$82K vega' },
      { label: '... (45 more options)', value: '' },
      { label: 'Gross Vega', value: '$420K' },
      { label: 'Net Vega', value: '$280K' },
    ],
  },
  'Gamma': {
    title: 'Portfolio Gamma Calculation',
    lines: [
      { label: 'Methodology', value: 'Sum of Dollar Gamma' },
      { label: 'SPY Calls (Mar 580)', value: '+$18K gamma' },
      { label: 'QQQ Puts (Mar 480)', value: '+$12K gamma' },
      { label: 'AAPL Calls (Feb 185)', value: '+$8K gamma' },
      { label: '... (45 more options)', value: '' },
      { label: 'Total Gamma', value: '$42K' },
      { label: '1% Move Impact', value: '±$420K' },
    ],
  },
  'Dur': {
    title: 'Portfolio Duration Calculation',
    lines: [
      { label: 'Methodology', value: 'DV01-Weighted Duration' },
      { label: '2Y Treasuries', value: '$28K DV01 × 1.9y = 53.2K' },
      { label: '5Y Treasuries', value: '$46K DV01 × 4.6y = 211.6K' },
      { label: '10Y Treasuries', value: '$65K DV01 × 8.2y = 533K' },
      { label: '30Y Treasuries', value: '$37K DV01 × 18.5y = 684.5K' },
      { label: 'Total Weighted', value: '1,482.3K' },
      { label: 'Total DV01', value: '$185K' },
      { label: 'Portfolio Duration', value: '4.2 years' },
    ],
  },
  'Convex': {
    title: 'Portfolio Convexity Calculation',
    lines: [
      { label: 'Methodology', value: 'DV01-Weighted Convexity' },
      { label: '2Y Bucket', value: '0.02' },
      { label: '5Y Bucket', value: '0.15' },
      { label: '10Y Bucket', value: '0.45' },
      { label: '30Y Bucket', value: '2.10' },
      { label: 'Weighted Average', value: '0.85' },
    ],
  },
  'Carry': {
    title: 'Portfolio Carry Calculation',
    lines: [
      { label: 'Methodology', value: 'Yield - Funding Cost' },
      { label: 'Portfolio Yield', value: '5.45%' },
      { label: 'Funding Rate', value: '5.13%' },
      { label: 'Net Carry', value: '32 bps' },
      { label: 'Annual Carry ($)', value: '$592K' },
    ],
  },
  'Spread': {
    title: 'Weighted Average Spread',
    lines: [
      { label: 'Methodology', value: 'CS01-Weighted Spread' },
      { label: 'IG Bucket (55%)', value: '85 bps' },
      { label: 'HY Bucket (25%)', value: '380 bps' },
      { label: 'EM Bucket (15%)', value: '220 bps' },
      { label: 'CDS Bucket (5%)', value: '95 bps' },
      { label: 'Weighted Average', value: '142 bps' },
    ],
  },
  'JTD': {
    title: 'Jump-to-Default Exposure',
    lines: [
      { label: 'Methodology', value: 'Sum of (1-Recovery) × Notional' },
      { label: 'Assumed Recovery', value: '40%' },
      { label: 'IG Exposure', value: '$1.2M JTD' },
      { label: 'HY Exposure', value: '$1.1M JTD' },
      { label: 'EM Exposure', value: '$0.4M JTD' },
      { label: 'CDS Exposure', value: '$0.1M JTD' },
      { label: 'Total JTD', value: '$2.8M' },
    ],
  },
  'Vol': {
    title: 'Implied Volatility',
    lines: [
      { label: 'Methodology', value: 'Position-Weighted IV' },
      { label: 'Source', value: 'Market mid quotes' },
      { label: 'Weighted Average IV', value: '12.5%' },
    ],
  },
  'Theta': {
    title: 'Portfolio Theta',
    lines: [
      { label: 'Methodology', value: 'Sum of daily decay' },
      { label: 'Long Options', value: '-$18K/day' },
      { label: 'Short Options', value: '+$6K/day' },
      { label: 'Net Theta', value: '-$12K/day' },
      { label: 'Monthly Decay', value: '-$252K' },
    ],
  },
  'Positions': {
    title: 'Position Count Breakdown',
    lines: [
      { label: 'Equities', value: '245 positions' },
      { label: 'Options', value: '48 positions' },
      { label: 'ETFs', value: '32 positions' },
      { label: 'Futures', value: '17 positions' },
      { label: 'Total', value: '342 positions' },
    ],
  },
  'VAR (95%)': {
    title: 'Value at Risk Calculation',
    lines: [
      { label: 'Methodology', value: 'Historical Simulation' },
      { label: 'Confidence Level', value: '95%' },
      { label: 'Holding Period', value: '1 day' },
      { label: 'Lookback Window', value: '252 days' },
      { label: 'Decay Factor', value: '0.94 (EWMA)' },
      { label: '5th Percentile Loss', value: '-$2.1M' },
      { label: 'As % of NAV', value: '-0.66%' },
    ],
  },
  'CVAR (95%)': {
    title: 'Conditional VAR Calculation',
    lines: [
      { label: 'Methodology', value: 'Expected Shortfall' },
      { label: 'Confidence Level', value: '95%' },
      { label: 'Definition', value: 'Avg loss when VAR exceeded' },
      { label: 'Worst 5% Scenarios', value: '13 days' },
      { label: 'Average Loss', value: '-$3.4M' },
      { label: 'As % of NAV', value: '-1.06%' },
    ],
  },
  'Gross Exposure': {
    title: 'Gross Exposure Calculation',
    lines: [
      { label: 'Methodology', value: 'Sum of |Long| + |Short|' },
      { label: 'Long Positions', value: '$185M' },
      { label: 'Short Positions', value: '$135M' },
      { label: 'Gross Exposure', value: '$320M' },
      { label: 'As % of NAV', value: '100%' },
    ],
  },
  'Net Exposure': {
    title: 'Net Exposure Calculation',
    lines: [
      { label: 'Methodology', value: 'Long - Short' },
      { label: 'Long Positions', value: '$185M' },
      { label: 'Short Positions', value: '$135M' },
      { label: 'Net Exposure', value: '$42.5M' },
      { label: 'As % of NAV', value: '13.3%' },
      { label: 'Net Long/Short', value: 'Net Long' },
    ],
  },
}

interface CalculationModalProps {
  isOpen: boolean
  onClose: () => void
  metricName: string | null
}

export default function CalculationModal({ isOpen, onClose, metricName }: CalculationModalProps) {
  if (!isOpen || !metricName) return null

  const calc = CALCULATIONS[metricName]

  if (!calc) {
    return (
      <div className="calc-modal active" onClick={onClose}>
        <div className="calc-modal-content" onClick={(e) => e.stopPropagation()}>
          <button className="expand-modal-close" onClick={onClose}>×</button>
          <div className="calc-modal-title">{metricName}</div>
          <div className="calc-formula">
            <div className="calc-line">
              <span className="label">Details</span>
              <span className="value">Calculation details not available</span>
            </div>
          </div>
        </div>
      </div>
    )
  }

  return (
    <div className="calc-modal active" onClick={onClose}>
      <div className="calc-modal-content" onClick={(e) => e.stopPropagation()}>
        <button className="expand-modal-close" onClick={onClose}>×</button>
        <div className="calc-modal-title">{calc.title}</div>
        <div className="calc-formula">
          {calc.lines.map((line, index) => (
            <div key={index} className="calc-line">
              <span className="label">{line.label}</span>
              <span className="value">{line.value}</span>
            </div>
          ))}
        </div>
      </div>
    </div>
  )
}
