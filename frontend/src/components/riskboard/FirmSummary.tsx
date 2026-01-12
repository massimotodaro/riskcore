import { useQuery } from '@tanstack/react-query'
import { motion } from 'framer-motion'
import RiskCard from './RiskCard'
import { aggregationApi, formatCurrency, formatPercent } from '../../services/api'

const containerVariants = {
  hidden: { opacity: 0 },
  visible: {
    opacity: 1,
    transition: {
      staggerChildren: 0.1,
    },
  },
}

const itemVariants = {
  hidden: { opacity: 0, y: 20 },
  visible: {
    opacity: 1,
    y: 0,
    transition: {
      duration: 0.4,
      ease: 'easeOut',
    },
  },
}

export default function FirmSummary() {
  const { data: firmSummary, isLoading, error } = useQuery({
    queryKey: ['firmSummary'],
    queryFn: () => aggregationApi.getFirmSummary(),
  })

  const { data: nettingSummary } = useQuery({
    queryKey: ['nettingSummary'],
    queryFn: () => aggregationApi.getNettingSummary(),
  })

  if (isLoading) {
    return (
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        {[...Array(4)].map((_, i) => (
          <div key={i} className="risk-card animate-pulse">
            <div className="space-y-4">
              <div className="h-3 bg-white/10 rounded w-1/3"></div>
              <div className="h-8 bg-white/10 rounded w-2/3"></div>
              <div className="h-3 bg-white/10 rounded w-1/2"></div>
            </div>
          </div>
        ))}
      </div>
    )
  }

  if (error) {
    return (
      <motion.div
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        className="glass p-4 border-rose-500/30"
      >
        <div className="flex items-center gap-3 text-rose-400">
          <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
          </svg>
          <span>Failed to load firm summary. Make sure the backend is running.</span>
        </div>
      </motion.div>
    )
  }

  // Calculate long bias percentage
  const longBias = firmSummary?.gross_exposure
    ? (firmSummary.long_exposure / firmSummary.gross_exposure) * 100
    : 50

  return (
    <motion.div
      variants={containerVariants}
      initial="hidden"
      animate="visible"
      className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6"
    >
      <motion.div variants={itemVariants}>
        <RiskCard
          title="Gross Exposure"
          value={formatCurrency(firmSummary?.gross_exposure || 0)}
          subtitle={`${firmSummary?.total_positions || 0} positions`}
          icon={
            <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M12 8c-1.657 0-3 .895-3 2s1.343 2 3 2 3 .895 3 2-1.343 2-3 2m0-8c1.11 0 2.08.402 2.599 1M12 8V7m0 1v8m0 0v1m0-1c-1.11 0-2.08-.402-2.599-1M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
            </svg>
          }
        />
      </motion.div>

      <motion.div variants={itemVariants}>
        <RiskCard
          title="Net Exposure"
          value={formatCurrency(firmSummary?.net_exposure || 0)}
          subtitle={`${longBias.toFixed(0)}% Long Bias`}
          color={longBias > 60 ? 'yellow' : 'neutral'}
          icon={
            <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M13 7h8m0 0v8m0-8l-8 8-4-4-6 6" />
            </svg>
          }
        />
      </motion.div>

      <motion.div variants={itemVariants}>
        <RiskCard
          title="Netting Efficiency"
          value={formatPercent(nettingSummary?.netting_efficiency || firmSummary?.netting_efficiency || 0)}
          subtitle={`${formatCurrency(nettingSummary?.netting_benefit || 0)} saved`}
          color="green"
          icon={
            <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M8 7h12m0 0l-4-4m4 4l-4 4m0 6H4m0 0l4 4m-4-4l4-4" />
            </svg>
          }
        />
      </motion.div>

      <motion.div variants={itemVariants}>
        <RiskCard
          title="Overlaps"
          value={firmSummary?.total_overlaps || 0}
          subtitle={`${firmSummary?.high_severity_overlaps || 0} high severity`}
          color={(firmSummary?.high_severity_overlaps || 0) > 5 ? 'red' : 'yellow'}
          icon={
            <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
            </svg>
          }
        />
      </motion.div>
    </motion.div>
  )
}
