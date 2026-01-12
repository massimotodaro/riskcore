import { motion } from 'framer-motion'
import FirmSummary from '../components/riskboard/FirmSummary'
import CorrelationHeatmap from '../components/charts/CorrelationHeatmap'
import OverlapsSummary from '../components/charts/OverlapsSummary'

export default function Dashboard() {
  const today = new Date().toLocaleDateString('en-US', {
    weekday: 'long',
    year: 'numeric',
    month: 'long',
    day: 'numeric',
  })

  return (
    <div className="space-y-8">
      {/* Page header */}
      <motion.div
        initial={{ opacity: 0, y: -10 }}
        animate={{ opacity: 1, y: 0 }}
        className="flex items-end justify-between"
      >
        <div>
          <h2 className="text-3xl font-bold text-slate-100 tracking-tight">Firm Overview</h2>
          <p className="mt-1 text-slate-400">
            Aggregated risk metrics across all portfolio managers
          </p>
        </div>
        <div className="text-sm text-slate-500">
          {today}
        </div>
      </motion.div>

      {/* Risk summary cards */}
      <FirmSummary />

      {/* Main content grid */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Correlation heatmap */}
        <CorrelationHeatmap />

        {/* Overlaps summary */}
        <OverlapsSummary />
      </div>

      {/* Additional info row */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Long/Short breakdown */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.2 }}
          className="glass p-6"
        >
          <h3 className="section-title mb-4">Exposure Breakdown</h3>
          <div className="space-y-4">
            <div>
              <div className="flex justify-between text-sm mb-2">
                <span className="text-slate-400">Long Exposure</span>
                <span className="font-mono font-medium text-emerald-400">65%</span>
              </div>
              <div className="progress-bar">
                <motion.div
                  initial={{ width: 0 }}
                  animate={{ width: '65%' }}
                  transition={{ duration: 0.8, delay: 0.3 }}
                  className="progress-fill bg-gradient-to-r from-emerald-500 to-emerald-400"
                />
              </div>
            </div>
            <div>
              <div className="flex justify-between text-sm mb-2">
                <span className="text-slate-400">Short Exposure</span>
                <span className="font-mono font-medium text-rose-400">35%</span>
              </div>
              <div className="progress-bar">
                <motion.div
                  initial={{ width: 0 }}
                  animate={{ width: '35%' }}
                  transition={{ duration: 0.8, delay: 0.4 }}
                  className="progress-fill bg-gradient-to-r from-rose-500 to-rose-400"
                />
              </div>
            </div>
          </div>
        </motion.div>

        {/* Top PMs by exposure */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.3 }}
          className="glass p-6"
        >
          <h3 className="section-title mb-4">Top PMs by Exposure</h3>
          <div className="space-y-3">
            {['Smith', 'Jones', 'Davis', 'Wilson', 'Chen'].map((pm, i) => (
              <motion.div
                key={pm}
                initial={{ opacity: 0, x: -10 }}
                animate={{ opacity: 1, x: 0 }}
                transition={{ delay: 0.4 + i * 0.05 }}
                className="flex items-center justify-between"
              >
                <div className="flex items-center gap-2">
                  <span className="text-xs text-slate-500 w-4">{i + 1}.</span>
                  <span className="text-sm font-medium text-slate-200">{pm}</span>
                </div>
                <div className="flex items-center gap-3">
                  <div className="w-20 progress-bar">
                    <motion.div
                      initial={{ width: 0 }}
                      animate={{ width: `${100 - i * 15}%` }}
                      transition={{ duration: 0.5, delay: 0.5 + i * 0.05 }}
                      className="progress-fill bg-gradient-to-r from-blue-500 to-cyan-500"
                    />
                  </div>
                  <span className="text-sm font-mono text-slate-400 w-10 text-right">
                    {25 - i * 3}%
                  </span>
                </div>
              </motion.div>
            ))}
          </div>
        </motion.div>

        {/* Quick actions */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.4 }}
          className="glass p-6"
        >
          <h3 className="section-title mb-4">Quick Actions</h3>
          <div className="space-y-2">
            {[
              {
                icon: (
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M15 13l-3-3m0 0l-3 3m3-3v12" />
                ),
                label: 'Upload Positions',
              },
              {
                icon: (
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M9 17v-2m3 2v-4m3 4v-6m2 10H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                ),
                label: 'Generate Report',
              },
              {
                icon: (
                  <>
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M10.325 4.317c.426-1.756 2.924-1.756 3.35 0a1.724 1.724 0 002.573 1.066c1.543-.94 3.31.826 2.37 2.37a1.724 1.724 0 001.065 2.572c1.756.426 1.756 2.924 0 3.35a1.724 1.724 0 00-1.066 2.573c.94 1.543-.826 3.31-2.37 2.37a1.724 1.724 0 00-2.572 1.065c-.426 1.756-2.924 1.756-3.35 0a1.724 1.724 0 00-2.573-1.066c-1.543.94-3.31-.826-2.37-2.37a1.724 1.724 0 00-1.065-2.572c-1.756-.426-1.756-2.924 0-3.35a1.724 1.724 0 001.066-2.573c-.94-1.543.826-3.31 2.37-2.37.996.608 2.296.07 2.572-1.065z" />
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
                  </>
                ),
                label: 'Configure Limits',
              },
            ].map((action, i) => (
              <motion.button
                key={action.label}
                initial={{ opacity: 0, x: -10 }}
                animate={{ opacity: 1, x: 0 }}
                transition={{ delay: 0.5 + i * 0.05 }}
                whileHover={{ x: 4 }}
                className="w-full flex items-center gap-3 px-4 py-3 text-left text-sm text-slate-300
                           hover:text-slate-100 hover:bg-white/5 rounded-xl transition-all duration-200
                           border border-white/5 hover:border-white/10"
              >
                <svg className="w-5 h-5 text-slate-500" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  {action.icon}
                </svg>
                {action.label}
              </motion.button>
            ))}
          </div>
        </motion.div>
      </div>
    </div>
  )
}
