import { Routes, Route, Navigate } from 'react-router-dom'
import Layout from './components/layout/Layout'
import Dashboard from './pages/Dashboard'
import CIODashboard from './pages/CIODashboard'
import RiskboardNew from './pages/RiskboardNew'
import Trades from './pages/Trades'
import TradesNew from './pages/TradesNew'
import Upload from './pages/Upload'
import UnderlyingTrades from './pages/UnderlyingTrades'

function App() {
  return (
    <Routes>
      <Route path="/" element={<Layout />}>
        <Route index element={<Navigate to="/riskboard" replace />} />
        <Route path="dashboard" element={<Dashboard />} />
        {/* New Unified Riskboard - Main Dashboard (Matching HTML Design) */}
        <Route path="riskboard" element={<RiskboardNew />} />
        {/* Positions & Trades Page - RiskPod tables with drill-down (Matching HTML Design) */}
        <Route path="trades" element={<TradesNew />} />
        {/* Import Data Page - File upload and reconciliation workflow */}
        <Route path="upload" element={<Upload />} />
        {/* Legacy CIO Dashboard */}
        <Route path="cio" element={<CIODashboard />} />
        {/* Legacy Trades Page */}
        <Route path="trades-legacy" element={<Trades />} />
        {/* Legacy Underlying Trades Drill-down (from RiskCard) */}
        <Route path="trades/:bookIds/:assetClass" element={<UnderlyingTrades />} />
        {/* Future routes */}
        {/* <Route path="overlaps" element={<Overlaps />} /> */}
        {/* <Route path="correlation" element={<Correlation />} /> */}
        {/* <Route path="reports" element={<Reports />} /> */}
        {/* <Route path="settings" element={<Settings />} /> */}
        {/* <Route path="help" element={<Help />} /> */}
      </Route>
    </Routes>
  )
}

export default App
