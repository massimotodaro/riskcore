import './riskboard.css'

interface MarketData {
  ticker: string
  price: string
  change: string
  direction: 'up' | 'down'
}

interface AnchorColumn {
  title: string
  colorClass: string
  data: MarketData[]
}

// Mock market data - in production this would come from API
const MARKET_ANCHORS: AnchorColumn[] = [
  {
    title: 'EQUITY',
    colorClass: 'equity',
    data: [
      { ticker: 'SPY', price: '584.20', change: '+0.8%', direction: 'up' },
      { ticker: 'QQQ', price: '498.50', change: '+1.2%', direction: 'up' },
      { ticker: 'VGK', price: '68.45', change: '-0.3%', direction: 'down' },
      { ticker: 'EWJ', price: '72.80', change: '+0.4%', direction: 'up' },
      { ticker: 'VWO', price: '44.25', change: '+0.6%', direction: 'up' },
    ],
  },
  {
    title: 'RATES',
    colorClass: 'rates',
    data: [
      { ticker: 'ZT (2Y)', price: '103.45', change: '-0.1%', direction: 'down' },
      { ticker: 'ZF (5Y)', price: '108.92', change: '-0.2%', direction: 'down' },
      { ticker: 'ZN (10Y)', price: '110.28', change: '-0.4%', direction: 'down' },
      { ticker: 'ZB (30Y)', price: '118.56', change: '-0.6%', direction: 'down' },
    ],
  },
  {
    title: 'CREDIT',
    colorClass: 'credit',
    data: [
      { ticker: 'CDX.IG', price: '52.8', change: '+1.2bp', direction: 'down' },
      { ticker: 'CDX.HY', price: '342.5', change: '+3.5bp', direction: 'down' },
      { ticker: 'LQD', price: '108.42', change: '-0.3%', direction: 'down' },
      { ticker: 'HYG', price: '78.25', change: '+0.2%', direction: 'up' },
    ],
  },
  {
    title: 'FX',
    colorClass: 'fx',
    data: [
      { ticker: 'DXY', price: '104.25', change: '+0.2%', direction: 'up' },
      { ticker: 'EUR/USD', price: '1.0842', change: '-0.2%', direction: 'down' },
      { ticker: 'USD/JPY', price: '157.85', change: '+0.3%', direction: 'up' },
      { ticker: 'GBP/USD', price: '1.2685', change: '+0.1%', direction: 'up' },
    ],
  },
  {
    title: 'COMMODITIES',
    colorClass: 'commodities',
    data: [
      { ticker: 'CL (Oil)', price: '78.45', change: '+1.8%', direction: 'up' },
      { ticker: 'GC (Gold)', price: '2,658', change: '+0.4%', direction: 'up' },
      { ticker: 'NG (Gas)', price: '2.85', change: '-2.1%', direction: 'down' },
      { ticker: 'HG (Copper)', price: '4.25', change: '+0.8%', direction: 'up' },
    ],
  },
  {
    title: 'OTHER',
    colorClass: 'other',
    data: [
      { ticker: 'VIX', price: '14.20', change: '-3.2%', direction: 'down' },
      { ticker: 'VVIX', price: '82.5', change: '-1.8%', direction: 'down' },
      { ticker: 'MOVE', price: '98.4', change: '-1.2%', direction: 'down' },
    ],
  },
]

export default function MarketAnchors() {
  return (
    <div className="market-anchors-section">
      <div className="market-anchors-title">Market Anchors</div>
      <div className="anchors-grid">
        {MARKET_ANCHORS.map((column) => (
          <div key={column.title} className="anchor-column">
            <div className={`anchor-column-title ${column.colorClass}`}>{column.title}</div>
            {column.data.map((item) => (
              <div key={item.ticker} className="anchor-row">
                <span className="ticker">{item.ticker}</span>
                <span className="price">{item.price}</span>
                <span className={`change ${item.direction}`}>{item.change}</span>
              </div>
            ))}
          </div>
        ))}
      </div>
    </div>
  )
}
