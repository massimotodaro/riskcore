import { Routes, Route, Navigate } from 'react-router-dom'
import Layout from './components/layout/Layout'
import Dashboard from './pages/Dashboard'
import CIODashboard from './pages/CIODashboard'
import Riskboard from './pages/Riskboard'
import UnderlyingTrades from './pages/UnderlyingTrades'

function App() {
  return (
    <Routes>
      <Route path="/" element={<Layout />}>
        <Route index element={<Navigate to="/riskboard" replace />} />
        <Route path="dashboard" element={<Dashboard />} />
        {/* New Unified Riskboard - Main Dashboard */}
        <Route path="riskboard" element={<Riskboard />} />
        {/* Legacy CIO Dashboard */}
        <Route path="cio" element={<CIODashboard />} />
        {/* Underlying Trades Drill-down */}
        <Route path="trades/:bookIds/:assetClass" element={<UnderlyingTrades />} />
        {/* Future routes */}
        {/* <Route path="positions" element={<Positions />} /> */}
        {/* <Route path="overlaps" element={<Overlaps />} /> */}
        {/* <Route path="correlation" element={<Correlation />} /> */}
        {/* <Route path="upload" element={<Upload />} /> */}
      </Route>
    </Routes>
  )
}

export default App
