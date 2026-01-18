import { useState } from 'react'
import './riskboard.css'

interface Trade {
  ticker: string
  name: string
  position: string
  qty: number
  price: string
  marketValue: string
  pnl: string
  pnlPercent: string
  direction: 'up' | 'down'
}

// Sample trades data per asset class
const SAMPLE_TRADES: Record<string, Trade[]> = {
  equity: [
    { ticker: 'AAPL', name: 'Apple Inc', position: 'Long', qty: 45000, price: '$185.42', marketValue: '$8.34M', pnl: '+$542K', pnlPercent: '+6.9%', direction: 'up' },
    { ticker: 'MSFT', name: 'Microsoft Corp', position: 'Long', qty: 28000, price: '$378.91', marketValue: '$10.61M', pnl: '+$892K', pnlPercent: '+9.2%', direction: 'up' },
    { ticker: 'GOOGL', name: 'Alphabet Inc', position: 'Long', qty: 15000, price: '$141.25', marketValue: '$2.12M', pnl: '+$156K', pnlPercent: '+7.9%', direction: 'up' },
    { ticker: 'TSLA', name: 'Tesla Inc', position: 'Short', qty: -12000, price: '$248.50', marketValue: '-$2.98M', pnl: '+$185K', pnlPercent: '+6.6%', direction: 'up' },
    { ticker: 'NVDA', name: 'NVIDIA Corp', position: 'Long', qty: 8500, price: '$495.20', marketValue: '$4.21M', pnl: '-$124K', pnlPercent: '-2.9%', direction: 'down' },
    { ticker: 'META', name: 'Meta Platforms', position: 'Long', qty: 18000, price: '$485.30', marketValue: '$8.74M', pnl: '+$1.2M', pnlPercent: '+15.9%', direction: 'up' },
    { ticker: 'AMZN', name: 'Amazon.com', position: 'Long', qty: 22000, price: '$178.25', marketValue: '$3.92M', pnl: '+$245K', pnlPercent: '+6.7%', direction: 'up' },
    { ticker: 'JPM', name: 'JPMorgan Chase', position: 'Short', qty: -15000, price: '$195.80', marketValue: '-$2.94M', pnl: '-$82K', pnlPercent: '-2.7%', direction: 'down' },
  ],
  rates: [
    { ticker: 'ZT', name: '2Y Treasury Future', position: 'Short', qty: -250, price: '103.45', marketValue: '-$25.9M', pnl: '+$125K', pnlPercent: '+0.5%', direction: 'up' },
    { ticker: 'ZF', name: '5Y Treasury Future', position: 'Short', qty: -180, price: '108.92', marketValue: '-$19.6M', pnl: '+$85K', pnlPercent: '+0.4%', direction: 'up' },
    { ticker: 'ZN', name: '10Y Treasury Future', position: 'Long', qty: 320, price: '110.28', marketValue: '$35.3M', pnl: '-$220K', pnlPercent: '-0.6%', direction: 'down' },
    { ticker: 'ZB', name: '30Y Treasury Future', position: 'Long', qty: 85, price: '118.56', marketValue: '$10.1M', pnl: '-$95K', pnlPercent: '-0.9%', direction: 'down' },
    { ticker: 'TLT', name: '20+ Year Treasury ETF', position: 'Long', qty: 45000, price: '$92.50', marketValue: '$4.16M', pnl: '-$180K', pnlPercent: '-4.1%', direction: 'down' },
  ],
  credit: [
    { ticker: 'LQD', name: 'iShares IG Corp Bond', position: 'Long', qty: 85000, price: '$108.42', marketValue: '$9.22M', pnl: '+$245K', pnlPercent: '+2.7%', direction: 'up' },
    { ticker: 'HYG', name: 'iShares High Yield', position: 'Long', qty: 65000, price: '$78.25', marketValue: '$5.09M', pnl: '+$182K', pnlPercent: '+3.7%', direction: 'up' },
    { ticker: 'CDX.IG', name: 'CDX IG Index', position: 'Short', qty: -50, price: '52.8', marketValue: '-$2.64M', pnl: '+$45K', pnlPercent: '+1.7%', direction: 'up' },
    { ticker: 'CDX.HY', name: 'CDX HY Index', position: 'Long', qty: 25, price: '342.5', marketValue: '$8.56M', pnl: '-$125K', pnlPercent: '-1.4%', direction: 'down' },
  ],
  fx: [
    { ticker: 'EUR/USD', name: 'Euro vs Dollar', position: 'Short', qty: -15000000, price: '1.0842', marketValue: '-$16.3M', pnl: '+$285K', pnlPercent: '+1.8%', direction: 'up' },
    { ticker: 'USD/JPY', name: 'Dollar vs Yen', position: 'Long', qty: 2500000000, price: '157.85', marketValue: '$15.8M', pnl: '+$420K', pnlPercent: '+2.7%', direction: 'up' },
    { ticker: 'GBP/USD', name: 'Pound vs Dollar', position: 'Long', qty: 8000000, price: '1.2685', marketValue: '$10.1M', pnl: '-$95K', pnlPercent: '-0.9%', direction: 'down' },
    { ticker: 'EUR/JPY', name: 'Euro vs Yen', position: 'Short', qty: -1200000000, price: '171.15', marketValue: '-$7.0M', pnl: '+$156K', pnlPercent: '+2.3%', direction: 'up' },
  ],
  commodities: [
    { ticker: 'CL', name: 'WTI Crude Oil', position: 'Long', qty: 450, price: '$78.45', marketValue: '$35.3M', pnl: '+$1.8M', pnlPercent: '+5.4%', direction: 'up' },
    { ticker: 'GC', name: 'Gold Future', position: 'Long', qty: 180, price: '$2,658', marketValue: '$47.8M', pnl: '+$2.1M', pnlPercent: '+4.6%', direction: 'up' },
    { ticker: 'NG', name: 'Natural Gas', position: 'Short', qty: -320, price: '$2.85', marketValue: '-$9.1M', pnl: '+$845K', pnlPercent: '+10.2%', direction: 'up' },
    { ticker: 'HG', name: 'Copper Future', position: 'Long', qty: 85, price: '$4.25', marketValue: '$9.0M', pnl: '-$185K', pnlPercent: '-2.0%', direction: 'down' },
  ],
  other: [
    { ticker: 'VIX', name: 'VIX Future', position: 'Short', qty: -250, price: '$14.20', marketValue: '-$3.55M', pnl: '+$485K', pnlPercent: '+15.8%', direction: 'up' },
    { ticker: 'UVXY', name: 'Ultra VIX ETF', position: 'Short', qty: -45000, price: '$28.50', marketValue: '-$1.28M', pnl: '+$320K', pnlPercent: '+33.3%', direction: 'up' },
    { ticker: 'SVXY', name: 'Short VIX ETF', position: 'Long', qty: 32000, price: '$52.80', marketValue: '$1.69M', pnl: '+$142K', pnlPercent: '+9.2%', direction: 'up' },
  ],
}

interface TradesModalProps {
  isOpen: boolean
  onClose: () => void
  assetClass: string | null
}

export default function TradesModal({ isOpen, onClose, assetClass }: TradesModalProps) {
  const [sortColumn, setSortColumn] = useState<string>('ticker')
  const [sortDirection, setSortDirection] = useState<'asc' | 'desc'>('asc')

  if (!isOpen || !assetClass) return null

  const trades = SAMPLE_TRADES[assetClass] || []

  const handleSort = (column: string) => {
    if (sortColumn === column) {
      setSortDirection(sortDirection === 'asc' ? 'desc' : 'asc')
    } else {
      setSortColumn(column)
      setSortDirection('asc')
    }
  }

  const sortedTrades = [...trades].sort((a, b) => {
    let aVal: string | number = a[sortColumn as keyof Trade] as string | number
    let bVal: string | number = b[sortColumn as keyof Trade] as string | number

    if (typeof aVal === 'string') aVal = aVal.toLowerCase()
    if (typeof bVal === 'string') bVal = bVal.toLowerCase()

    if (aVal < bVal) return sortDirection === 'asc' ? -1 : 1
    if (aVal > bVal) return sortDirection === 'asc' ? 1 : -1
    return 0
  })

  const colorClass = {
    equity: 'blue',
    rates: 'green',
    credit: 'purple',
    fx: 'cyan',
    commodities: 'orange',
    other: 'gray',
  }[assetClass] || 'blue'

  return (
    <div className="trades-modal active" onClick={onClose}>
      <div className="trades-modal-content" onClick={(e) => e.stopPropagation()}>
        <div className="trades-modal-header">
          <div>
            <div className={`trades-modal-title ${colorClass}`}>{assetClass.toUpperCase()} Positions</div>
            <div className="trades-modal-subtitle">{trades.length} positions</div>
          </div>
          <button className="trades-modal-close" onClick={onClose}>×</button>
        </div>

        <div className="trades-table-container">
          <table className="trades-table">
            <thead>
              <tr>
                <th onClick={() => handleSort('ticker')} className={sortColumn === 'ticker' ? 'sorted' : ''}>
                  Ticker {sortColumn === 'ticker' && (sortDirection === 'asc' ? '▲' : '▼')}
                </th>
                <th onClick={() => handleSort('name')} className={sortColumn === 'name' ? 'sorted' : ''}>
                  Name {sortColumn === 'name' && (sortDirection === 'asc' ? '▲' : '▼')}
                </th>
                <th onClick={() => handleSort('position')} className={sortColumn === 'position' ? 'sorted' : ''}>
                  Position {sortColumn === 'position' && (sortDirection === 'asc' ? '▲' : '▼')}
                </th>
                <th onClick={() => handleSort('qty')} className={sortColumn === 'qty' ? 'sorted' : ''}>
                  Qty {sortColumn === 'qty' && (sortDirection === 'asc' ? '▲' : '▼')}
                </th>
                <th>Price</th>
                <th>Mkt Value</th>
                <th onClick={() => handleSort('pnl')} className={sortColumn === 'pnl' ? 'sorted' : ''}>
                  P&L {sortColumn === 'pnl' && (sortDirection === 'asc' ? '▲' : '▼')}
                </th>
                <th>P&L %</th>
              </tr>
            </thead>
            <tbody>
              {sortedTrades.map((trade) => (
                <tr key={trade.ticker}>
                  <td className="ticker">{trade.ticker}</td>
                  <td className="name">{trade.name}</td>
                  <td className={`position ${trade.position.toLowerCase()}`}>{trade.position}</td>
                  <td className="qty">{trade.qty.toLocaleString()}</td>
                  <td className="price">{trade.price}</td>
                  <td className="market-value">{trade.marketValue}</td>
                  <td className={`pnl ${trade.direction}`}>{trade.pnl}</td>
                  <td className={`pnl-percent ${trade.direction}`}>{trade.pnlPercent}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  )
}
