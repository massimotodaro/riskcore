import { useState, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import { useQuery } from '@tanstack/react-query'
import { motion } from 'framer-motion'
import RiskPodRow from '../components/riskboard/RiskPodRow'
import PortfolioSelector from '../components/riskboard/PortfolioSelector'
import BookCorrelation from '../components/riskboard/BookCorrelation'
import {
  riskByAssetClassApi,
  booksApi,
  bookCorrelationApi,
  formatCurrency,
} from '../services/api'
import type { Book } from '../types'

export default function CIODashboard() {
  const navigate = useNavigate()

  // Portfolio selection state
  const [portfolioA, setPortfolioA] = useState<Book | null>(null)
  const [portfolioB, setPortfolioB] = useState<Book | null>(null)

  // Fetch firm-wide risk
  const {
    data: firmRisk,
    isLoading: firmLoading,
  } = useQuery({
    queryKey: ['firmRisk'],
    queryFn: () => riskByAssetClassApi.getFirmRisk(),
  })

  // Fetch overlay risk
  const {
    data: overlayRisk,
    isLoading: overlayLoading,
  } = useQuery({
    queryKey: ['overlayRisk'],
    queryFn: () => riskByAssetClassApi.getOverlayRisk(),
  })

  // Fetch all trading books for selectors
  const {
    data: tradingBooks,
  } = useQuery({
    queryKey: ['tradingBooks'],
    queryFn: () => booksApi.getTradingBooks(),
  })

  // Fetch Portfolio A risk (when selected)
  const {
    data: portfolioARisk,
    isLoading: portfolioALoading,
  } = useQuery({
    queryKey: ['portfolioARisk', portfolioA?.book_id],
    queryFn: () => riskByAssetClassApi.getBookRisk(portfolioA!.book_id),
    enabled: !!portfolioA,
  })

  // Fetch Portfolio B risk (when selected)
  const {
    data: portfolioBRisk,
    isLoading: portfolioBLoading,
  } = useQuery({
    queryKey: ['portfolioBRisk', portfolioB?.book_id],
    queryFn: () => riskByAssetClassApi.getBookRisk(portfolioB!.book_id),
    enabled: !!portfolioB,
  })

  // Fetch correlation between portfolios (when both selected)
  const {
    data: correlation,
    isLoading: correlationLoading,
  } = useQuery({
    queryKey: ['bookCorrelation', portfolioA?.book_id, portfolioB?.book_id],
    queryFn: () => bookCorrelationApi.getCorrelation(portfolioA!.book_id, portfolioB!.book_id),
    enabled: !!portfolioA && !!portfolioB,
  })

  // Auto-select first two books when loaded
  useEffect(() => {
    if (tradingBooks && tradingBooks.length >= 2) {
      if (!portfolioA) setPortfolioA(tradingBooks[0])
      if (!portfolioB) setPortfolioB(tradingBooks[1])
    }
  }, [tradingBooks, portfolioA, portfolioB])

  // Handle trades click - navigate to underlying trades page
  const handleTradesClick = (bookId: string | undefined, assetClass: string) => {
    if (bookId) {
      navigate(`/trades/${bookId}/${assetClass}`)
    } else {
      // Firm-wide: navigate to firm trades with asset class filter
      navigate(`/trades/firm/${assetClass}`)
    }
  }

  // Calculate summary metrics
  const firmNetExposure = firmRisk?.reduce((sum, r) => sum + r.net_exposure, 0) ?? 0
  const overlayNetExposure = overlayRisk?.reduce((sum, r) => sum + r.net_exposure, 0) ?? 0
  const totalPositions = firmRisk?.reduce((sum, r) => sum + r.position_count, 0) ?? 0

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-950 via-slate-900 to-slate-950">
      <div className="max-w-[1800px] mx-auto px-6 py-8">
        {/* Header */}
        <motion.div
          initial={{ opacity: 0, y: -20 }}
          animate={{ opacity: 1, y: 0 }}
          className="mb-8"
        >
          <h1 className="text-2xl font-bold text-slate-100">CIO Risk Dashboard</h1>
          <p className="text-slate-500 mt-1">
            Firm-wide risk view with overlay management and portfolio comparison
          </p>
        </motion.div>

        {/* Summary Cards */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.1 }}
          className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-8"
        >
          <div className="glass p-4">
            <p className="text-xs text-slate-500 uppercase tracking-wider">Firm Net Exposure</p>
            <p className={`text-2xl font-bold font-mono ${firmNetExposure >= 0 ? 'text-emerald-400' : 'text-rose-400'}`}>
              {formatCurrency(firmNetExposure)}
            </p>
          </div>
          <div className="glass p-4">
            <p className="text-xs text-slate-500 uppercase tracking-wider">Overlay Hedges</p>
            <p className={`text-2xl font-bold font-mono ${overlayNetExposure <= 0 ? 'text-purple-400' : 'text-amber-400'}`}>
              {formatCurrency(overlayNetExposure)}
            </p>
          </div>
          <div className="glass p-4">
            <p className="text-xs text-slate-500 uppercase tracking-wider">Net After Overlay</p>
            <p className={`text-2xl font-bold font-mono ${(firmNetExposure + overlayNetExposure) >= 0 ? 'text-emerald-400' : 'text-rose-400'}`}>
              {formatCurrency(firmNetExposure + overlayNetExposure)}
            </p>
          </div>
          <div className="glass p-4">
            <p className="text-xs text-slate-500 uppercase tracking-wider">Total Positions</p>
            <p className="text-2xl font-bold font-mono text-slate-100">{totalPositions.toLocaleString()}</p>
          </div>
        </motion.div>

        {/* Row 1: Firm-Wide RiskPods */}
        <motion.section
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.2 }}
          className="mb-10"
        >
          <RiskPodRow
            data={firmRisk ?? []}
            title="Firm-Wide Exposure"
            subtitle="Aggregate risk across all portfolios"
            bookType="firm"
            isLoading={firmLoading}
            onTradesClick={(assetClass) => handleTradesClick(undefined, assetClass)}
          />
        </motion.section>

        {/* Row 2: Overlay Portfolio RiskPods */}
        <motion.section
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.3 }}
          className="mb-10"
        >
          <RiskPodRow
            data={overlayRisk ?? []}
            title="Overlay Portfolio"
            subtitle="CIO-managed hedge positions to offset firm risk"
            bookType="overlay"
            isLoading={overlayLoading}
            onTradesClick={(assetClass) => handleTradesClick('overlay', assetClass)}
            showEmptyState={!overlayLoading}
          />
        </motion.section>

        {/* Divider */}
        <div className="border-t border-white/5 my-8" />

        {/* Portfolio Comparison Header */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.4 }}
          className="mb-6"
        >
          <h2 className="text-lg font-semibold text-slate-100">Portfolio Comparison</h2>
          <p className="text-sm text-slate-500">
            Select two portfolios to compare risk profiles and correlation
          </p>
        </motion.div>

        {/* Row 3: Portfolio A */}
        <motion.section
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.5 }}
          className="mb-8"
        >
          <div className="flex items-center gap-4 mb-4">
            <PortfolioSelector
              books={tradingBooks ?? []}
              selectedBook={portfolioA}
              onSelect={setPortfolioA}
              label="Portfolio A"
              excludeBookIds={portfolioB ? [portfolioB.book_id] : []}
              className="w-72"
            />
          </div>
          {portfolioA && (
            <RiskPodRow
              data={portfolioARisk ?? []}
              title={portfolioA.name}
              subtitle={portfolioA.pm_name ? `PM: ${portfolioA.pm_name}` : portfolioA.strategy}
              bookId={portfolioA.book_id}
              bookType="trading"
              isLoading={portfolioALoading}
              onTradesClick={(assetClass) => handleTradesClick(portfolioA.book_id, assetClass)}
            />
          )}
        </motion.section>

        {/* Row 4: Portfolio B */}
        <motion.section
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.6 }}
          className="mb-8"
        >
          <div className="flex items-center gap-4 mb-4">
            <PortfolioSelector
              books={tradingBooks ?? []}
              selectedBook={portfolioB}
              onSelect={setPortfolioB}
              label="Portfolio B"
              excludeBookIds={portfolioA ? [portfolioA.book_id] : []}
              className="w-72"
            />
          </div>
          {portfolioB && (
            <RiskPodRow
              data={portfolioBRisk ?? []}
              title={portfolioB.name}
              subtitle={portfolioB.pm_name ? `PM: ${portfolioB.pm_name}` : portfolioB.strategy}
              bookId={portfolioB.book_id}
              bookType="trading"
              isLoading={portfolioBLoading}
              onTradesClick={(assetClass) => handleTradesClick(portfolioB.book_id, assetClass)}
            />
          )}
        </motion.section>

        {/* Row 5: Correlation View */}
        <motion.section
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.7 }}
          className="mb-10"
        >
          <h2 className="text-lg font-semibold text-slate-100 mb-4">
            {portfolioA && portfolioB
              ? `Correlation: ${portfolioA.name} vs ${portfolioB.name}`
              : 'Portfolio Correlation'}
          </h2>
          <BookCorrelation
            data={correlation ?? null}
            isLoading={correlationLoading && !!portfolioA && !!portfolioB}
            book1Name={portfolioA?.name}
            book2Name={portfolioB?.name}
          />
        </motion.section>
      </div>
    </div>
  )
}
