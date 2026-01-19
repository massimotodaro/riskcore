import { useState } from 'react'
import { useSearchParams } from 'react-router-dom'
import { motion, AnimatePresence } from 'framer-motion'
import clsx from 'clsx'
import { useTheme } from '../context/ThemeContext'
import ImportModal from '../components/import/ImportModal'

// Types
export type ImportMode = 'trades' | 'portfolio' | 'delta' | 'google' | 'fix'

interface PendingItem {
  id: string
  type: 'unmatched' | 'reconciliation'
  title: string
  description: string
  count?: number
  date: string
}

// Mock pending items
const mockPendingItems: PendingItem[] = [
  {
    id: 'pend-1',
    type: 'unmatched',
    title: 'XYZ Corp Class A',
    description: 'Unknown security needs mapping',
    date: 'Jan 19, 2026',
  },
  {
    id: 'pend-2',
    type: 'unmatched',
    title: 'ABC Holdings Pfd B',
    description: 'Unknown security needs mapping',
    date: 'Jan 18, 2026',
  },
  {
    id: 'pend-3',
    type: 'reconciliation',
    title: 'Alpha Growth - Jan 19',
    description: '5 positions need review',
    count: 5,
    date: 'Jan 19, 2026',
  },
]

export default function Upload() {
  const { isDarkMode } = useTheme()
  const [searchParams] = useSearchParams()

  // Get initial mode from URL
  const initialMode = searchParams.get('mode') as ImportMode | null
  const showPending = searchParams.get('pending') === 'true'

  // State
  const [isModalOpen, setIsModalOpen] = useState(!!initialMode)
  const [selectedMode, setSelectedMode] = useState<ImportMode | null>(initialMode)
  const [activeTab, setActiveTab] = useState<'import' | 'pending'>(showPending ? 'pending' : 'import')

  // Theme colors
  const bgColor = isDarkMode ? undefined : '#D9D9D9'
  const cardBg = isDarkMode ? 'rgba(15, 23, 42, 0.6)' : 'rgba(255, 255, 255, 0.8)'
  const borderColor = isDarkMode ? 'rgba(255, 255, 255, 0.1)' : 'rgba(0, 0, 0, 0.1)'
  const textColor = isDarkMode ? '#e2e8f0' : '#1e293b'
  const mutedColor = '#64748b'

  const openImportModal = (mode: ImportMode) => {
    setSelectedMode(mode)
    setIsModalOpen(true)
  }

  const importOptions = [
    {
      mode: 'trades' as ImportMode,
      icon: (
        <svg className="w-6 h-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M15 13l-3-3m0 0l-3 3m3-3v12" />
        </svg>
      ),
      title: 'Upload Trades',
      description: 'Add new trades to existing portfolio. Won\'t affect existing positions.',
      color: '#3b82f6',
    },
    {
      mode: 'portfolio' as ImportMode,
      icon: (
        <svg className="w-6 h-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
        </svg>
      ),
      title: 'Portfolio Snapshot',
      description: 'Replace portfolio with this file. Compares against existing positions.',
      color: '#22c55e',
    },
    {
      mode: 'delta' as ImportMode,
      icon: (
        <svg className="w-6 h-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
        </svg>
      ),
      title: 'Position Updates',
      description: 'Update specific positions that changed. Matches by security identifier.',
      color: '#8b5cf6',
    },
    {
      mode: 'google' as ImportMode,
      icon: (
        <svg className="w-6 h-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M3 10h18M3 14h18m-9-4v8m-7 0h14a2 2 0 002-2V8a2 2 0 00-2-2H5a2 2 0 00-2 2v8a2 2 0 002 2z" />
        </svg>
      ),
      title: 'Connect Google Sheet',
      description: 'Link a Google Sheet for automatic syncing of positions or trades.',
      color: '#f59e0b',
    },
    {
      mode: 'fix' as ImportMode,
      icon: (
        <svg className="w-6 h-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M8 9l3 3-3 3m5 0h3M5 20h14a2 2 0 002-2V6a2 2 0 00-2-2H5a2 2 0 00-2 2v12a2 2 0 002 2z" />
        </svg>
      ),
      title: 'FIX Message',
      description: 'Parse FIX protocol message for trade execution data.',
      color: '#06b6d4',
    },
  ]

  return (
    <div
      className="h-full flex flex-col"
      style={{ background: bgColor, color: textColor }}
    >
      {/* Header */}
      <header
        className="px-6 py-4"
        style={{ borderBottom: `1px solid ${borderColor}` }}
      >
        <h1 className="text-xl font-semibold mb-4">Import Data</h1>

        {/* Tab Navigation */}
        <div className="flex gap-1">
          <button
            onClick={() => setActiveTab('import')}
            className={clsx(
              'px-4 py-2 rounded-lg text-sm font-medium transition-all',
              activeTab === 'import'
                ? 'bg-emerald-500/15 text-emerald-400 border border-emerald-500/30'
                : isDarkMode
                  ? 'text-slate-400 hover:text-white hover:bg-white/5'
                  : 'text-slate-600 hover:text-slate-900 hover:bg-black/5'
            )}
          >
            Import Options
          </button>
          <button
            onClick={() => setActiveTab('pending')}
            className={clsx(
              'px-4 py-2 rounded-lg text-sm font-medium transition-all flex items-center gap-2',
              activeTab === 'pending'
                ? 'bg-amber-500/15 text-amber-400 border border-amber-500/30'
                : isDarkMode
                  ? 'text-slate-400 hover:text-white hover:bg-white/5'
                  : 'text-slate-600 hover:text-slate-900 hover:bg-black/5'
            )}
          >
            Pending Actions
            {mockPendingItems.length > 0 && (
              <span className="px-1.5 py-0.5 text-xs font-bold rounded-full bg-amber-500 text-slate-900">
                {mockPendingItems.length}
              </span>
            )}
          </button>
        </div>
      </header>

      {/* Main Content */}
      <main className="flex-1 overflow-y-auto p-6">
        <AnimatePresence mode="wait">
          {activeTab === 'import' ? (
            <motion.div
              key="import"
              initial={{ opacity: 0, y: 10 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -10 }}
            >
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                {importOptions.map((option) => (
                  <motion.div
                    key={option.mode}
                    whileHover={{ scale: 1.02 }}
                    whileTap={{ scale: 0.98 }}
                    onClick={() => openImportModal(option.mode)}
                    className="cursor-pointer rounded-xl p-5 transition-all"
                    style={{
                      background: cardBg,
                      border: `1px solid ${borderColor}`,
                    }}
                  >
                    <div className="flex items-start gap-4">
                      <div
                        className="w-12 h-12 rounded-lg flex items-center justify-center"
                        style={{ background: `${option.color}20`, color: option.color }}
                      >
                        {option.icon}
                      </div>
                      <div className="flex-1">
                        <h3 className="font-semibold mb-1" style={{ color: option.color }}>
                          {option.title}
                        </h3>
                        <p className="text-sm" style={{ color: mutedColor }}>
                          {option.description}
                        </p>
                      </div>
                    </div>
                  </motion.div>
                ))}
              </div>

              {/* Recent Imports Section */}
              <div className="mt-8">
                <h2 className="text-lg font-semibold mb-4" style={{ color: textColor }}>
                  Recent Imports
                </h2>
                <div
                  className="rounded-xl p-4"
                  style={{ background: cardBg, border: `1px solid ${borderColor}` }}
                >
                  <div className="text-center py-8" style={{ color: mutedColor }}>
                    No recent imports
                  </div>
                </div>
              </div>
            </motion.div>
          ) : (
            <motion.div
              key="pending"
              initial={{ opacity: 0, y: 10 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -10 }}
            >
              {mockPendingItems.length === 0 ? (
                <div
                  className="rounded-xl p-8 text-center"
                  style={{ background: cardBg, border: `1px solid ${borderColor}` }}
                >
                  <div className="text-4xl mb-4">✓</div>
                  <h3 className="text-lg font-semibold mb-2" style={{ color: textColor }}>
                    All Caught Up!
                  </h3>
                  <p style={{ color: mutedColor }}>
                    No pending items require your attention
                  </p>
                </div>
              ) : (
                <div className="space-y-4">
                  {/* Unmatched Securities */}
                  {mockPendingItems.filter(i => i.type === 'unmatched').length > 0 && (
                    <div>
                      <h2 className="text-sm font-semibold uppercase tracking-wider mb-3" style={{ color: mutedColor }}>
                        Unmatched Securities
                      </h2>
                      <div className="space-y-2">
                        {mockPendingItems
                          .filter(i => i.type === 'unmatched')
                          .map((item) => (
                            <div
                              key={item.id}
                              className="flex items-center justify-between p-4 rounded-lg cursor-pointer transition-all hover:scale-[1.01]"
                              style={{
                                background: cardBg,
                                border: `1px solid ${borderColor}`,
                              }}
                            >
                              <div className="flex items-center gap-4">
                                <div
                                  className="w-10 h-10 rounded-lg flex items-center justify-center text-xl"
                                  style={{ background: 'rgba(239, 68, 68, 0.15)' }}
                                >
                                  ❓
                                </div>
                                <div>
                                  <h3 className="font-medium" style={{ color: textColor }}>
                                    {item.title}
                                  </h3>
                                  <p className="text-sm" style={{ color: mutedColor }}>
                                    {item.description}
                                  </p>
                                </div>
                              </div>
                              <div className="flex items-center gap-4">
                                <span className="text-sm" style={{ color: mutedColor }}>
                                  {item.date}
                                </span>
                                <button
                                  className="px-3 py-1.5 rounded-lg text-sm font-medium bg-blue-500/15 text-blue-400 border border-blue-500/30 hover:bg-blue-500/25"
                                >
                                  Resolve
                                </button>
                              </div>
                            </div>
                          ))}
                      </div>
                    </div>
                  )}

                  {/* Pending Reconciliations */}
                  {mockPendingItems.filter(i => i.type === 'reconciliation').length > 0 && (
                    <div className="mt-6">
                      <h2 className="text-sm font-semibold uppercase tracking-wider mb-3" style={{ color: mutedColor }}>
                        Pending Reconciliations
                      </h2>
                      <div className="space-y-2">
                        {mockPendingItems
                          .filter(i => i.type === 'reconciliation')
                          .map((item) => (
                            <div
                              key={item.id}
                              className="flex items-center justify-between p-4 rounded-lg cursor-pointer transition-all hover:scale-[1.01]"
                              style={{
                                background: cardBg,
                                border: `1px solid ${borderColor}`,
                              }}
                            >
                              <div className="flex items-center gap-4">
                                <div
                                  className="w-10 h-10 rounded-lg flex items-center justify-center text-xl"
                                  style={{ background: 'rgba(245, 158, 11, 0.15)' }}
                                >
                                  ⚠️
                                </div>
                                <div>
                                  <h3 className="font-medium" style={{ color: textColor }}>
                                    {item.title}
                                  </h3>
                                  <p className="text-sm" style={{ color: mutedColor }}>
                                    {item.description}
                                  </p>
                                </div>
                              </div>
                              <div className="flex items-center gap-4">
                                <span className="text-sm" style={{ color: mutedColor }}>
                                  {item.date}
                                </span>
                                <button
                                  className="px-3 py-1.5 rounded-lg text-sm font-medium bg-amber-500/15 text-amber-400 border border-amber-500/30 hover:bg-amber-500/25"
                                >
                                  Review
                                </button>
                              </div>
                            </div>
                          ))}
                      </div>
                    </div>
                  )}
                </div>
              )}
            </motion.div>
          )}
        </AnimatePresence>
      </main>

      {/* Import Modal */}
      <AnimatePresence>
        {isModalOpen && selectedMode && (
          <ImportModal
            mode={selectedMode}
            onClose={() => {
              setIsModalOpen(false)
              setSelectedMode(null)
            }}
          />
        )}
      </AnimatePresence>
    </div>
  )
}
