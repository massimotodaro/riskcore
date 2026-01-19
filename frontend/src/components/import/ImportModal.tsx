import { useState } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import clsx from 'clsx'
import { useTheme } from '../../context/ThemeContext'
import type { ImportMode } from '../../pages/Upload'

interface ImportModalProps {
  mode: ImportMode
  onClose: () => void
}

// Types
interface MappedColumn {
  fileColumn: string
  mapsTo: string
  sampleValue: string
}

interface ReconciliationItem {
  id: string
  security: string
  type: 'matched' | 'mismatch' | 'stale' | 'new'
  systemQty?: number
  importQty?: number
  systemValue?: number
  importValue?: number
  action?: 'update' | 'keep' | 'delete' | 'add'
  status?: 'ready' | 'pending' | 'unmatched'
}

// Mock data
const mockMappedColumns: MappedColumn[] = [
  { fileColumn: 'Symbol', mapsTo: 'Ticker', sampleValue: 'AAPL' },
  { fileColumn: 'Shares', mapsTo: 'Quantity', sampleValue: '1,000' },
  { fileColumn: 'Last Price', mapsTo: 'Price', sampleValue: '195.50' },
  { fileColumn: 'Cost', mapsTo: 'Cost Basis', sampleValue: '150.25' },
  { fileColumn: 'Type', mapsTo: 'Instr Type', sampleValue: 'Stock' },
  { fileColumn: 'Account', mapsTo: '-- Skip --', sampleValue: '12345' },
]

const mockReconciliationItems: ReconciliationItem[] = [
  // Matched
  { id: 'r1', security: 'AAPL', type: 'matched', systemQty: 1000, importQty: 1000, systemValue: 195500, importValue: 195500 },
  { id: 'r2', security: 'MSFT', type: 'matched', systemQty: 500, importQty: 500, systemValue: 210000, importValue: 210000 },
  // Mismatches
  { id: 'r3', security: 'NVDA', type: 'mismatch', systemQty: 200, importQty: 250, action: undefined },
  { id: 'r4', security: 'GOOGL', type: 'mismatch', systemQty: 100, importQty: 80, action: undefined },
  { id: 'r5', security: 'AMZN', type: 'mismatch', systemQty: 150, importQty: 175, action: undefined },
  // Stale
  { id: 'r6', security: 'IBM', type: 'stale', systemQty: 100, systemValue: 17500, action: undefined },
  { id: 'r7', security: 'GE', type: 'stale', systemQty: 50, systemValue: 8200, action: undefined },
  // New
  { id: 'r8', security: 'PLTR', type: 'new', importQty: 400, importValue: 10000, status: 'ready' },
  { id: 'r9', security: 'SNOW', type: 'new', importQty: 100, importValue: 15000, status: 'ready' },
  { id: 'r10', security: 'XYZ Corp', type: 'new', importQty: 200, importValue: 20000, status: 'unmatched' },
]

const modeLabels: Record<ImportMode, string> = {
  trades: 'Add Trades',
  portfolio: 'Portfolio Snapshot',
  delta: 'Position Updates',
  google: 'Google Sheet',
  fix: 'FIX Message',
}

export default function ImportModal({ mode, onClose }: ImportModalProps) {
  const { isDarkMode } = useTheme()

  // State
  const [currentStep, setCurrentStep] = useState(1)
  const [selectedFile, setSelectedFile] = useState<File | null>(null)
  const [selectedPortfolio, setSelectedPortfolio] = useState('alpha-growth')
  const [mappedColumns, setMappedColumns] = useState(mockMappedColumns)
  const [reconciliationItems, setReconciliationItems] = useState(mockReconciliationItems)
  const [isProcessing, setIsProcessing] = useState(false)

  // Theme colors
  const modalBg = isDarkMode ? '#1e293b' : '#f8fafc'
  const headerBg = isDarkMode ? 'rgba(15, 23, 42, 0.5)' : 'rgba(0, 0, 0, 0.02)'
  const borderColor = isDarkMode ? 'rgba(255, 255, 255, 0.1)' : 'rgba(0, 0, 0, 0.1)'
  const textColor = isDarkMode ? '#e2e8f0' : '#1e293b'
  const mutedColor = '#64748b'
  const cardBg = isDarkMode ? '#334155' : '#e2e8f0'

  // Step labels
  const steps = [
    { number: 1, label: 'Select File' },
    { number: 2, label: 'Map Columns' },
    { number: 3, label: 'Review & Apply' },
  ]

  // Handle file drop/select
  const handleFileDrop = (e: React.DragEvent) => {
    e.preventDefault()
    const file = e.dataTransfer.files[0]
    if (file) {
      setSelectedFile(file)
    }
  }

  const handleFileSelect = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0]
    if (file) {
      setSelectedFile(file)
    }
  }

  // Handle reconciliation actions
  const handleReconciliationAction = (id: string, action: 'update' | 'keep' | 'delete' | 'add') => {
    setReconciliationItems(items =>
      items.map(item =>
        item.id === id ? { ...item, action } : item
      )
    )
  }

  const handleSelectAll = (type: 'mismatch' | 'stale', action: 'update' | 'keep' | 'delete') => {
    setReconciliationItems(items =>
      items.map(item =>
        item.type === type ? { ...item, action } : item
      )
    )
  }

  // Calculate summary
  const matchedCount = reconciliationItems.filter(i => i.type === 'matched').length
  const mismatchCount = reconciliationItems.filter(i => i.type === 'mismatch').length
  const staleCount = reconciliationItems.filter(i => i.type === 'stale').length
  const newCount = reconciliationItems.filter(i => i.type === 'new').length
  const unmatchedCount = reconciliationItems.filter(i => i.status === 'unmatched').length

  const updatesSelected = reconciliationItems.filter(i => i.action === 'update').length
  const deletesSelected = reconciliationItems.filter(i => i.action === 'delete').length
  const addsReady = reconciliationItems.filter(i => i.type === 'new' && i.status === 'ready').length

  // Can proceed to next step?
  const canProceed = () => {
    if (currentStep === 1) return selectedFile !== null
    if (currentStep === 2) return true
    if (currentStep === 3) {
      // All mismatches and stales must have actions
      const allMismatchesResolved = reconciliationItems
        .filter(i => i.type === 'mismatch')
        .every(i => i.action)
      const allStalesResolved = reconciliationItems
        .filter(i => i.type === 'stale')
        .every(i => i.action)
      const noUnmatched = unmatchedCount === 0
      return allMismatchesResolved && allStalesResolved && noUnmatched
    }
    return false
  }

  const handleApply = async () => {
    setIsProcessing(true)
    await new Promise(resolve => setTimeout(resolve, 2000))
    setIsProcessing(false)
    onClose()
  }

  return (
    <motion.div
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      exit={{ opacity: 0 }}
      className="fixed inset-0 z-[1000] flex items-center justify-center"
      style={{ background: 'rgba(0, 0, 0, 0.7)' }}
      onClick={(e) => e.target === e.currentTarget && onClose()}
    >
      <motion.div
        initial={{ scale: 0.95, opacity: 0 }}
        animate={{ scale: 1, opacity: 1 }}
        exit={{ scale: 0.95, opacity: 0 }}
        className="w-[90%] max-w-[900px] max-h-[90vh] rounded-xl overflow-hidden flex flex-col"
        style={{ background: modalBg, border: `1px solid ${borderColor}` }}
        onClick={(e) => e.stopPropagation()}
      >
        {/* Header */}
        <div
          className="flex justify-between items-center px-5 py-4"
          style={{ background: headerBg, borderBottom: `1px solid ${borderColor}` }}
        >
          <h2 className="text-lg font-semibold" style={{ color: textColor }}>
            Import Data - {modeLabels[mode]}
          </h2>
          <button
            onClick={onClose}
            className="w-8 h-8 rounded-md flex items-center justify-center text-lg transition-colors"
            style={{
              background: 'rgba(239, 68, 68, 0.15)',
              border: '1px solid rgba(239, 68, 68, 0.3)',
              color: '#ef4444',
            }}
          >
            ×
          </button>
        </div>

        {/* Body */}
        <div className="flex-1 overflow-y-auto p-5">
          {/* Progress Steps */}
          <div className="flex items-center justify-center gap-2 mb-6">
            {steps.map((step, index) => (
              <div key={step.number} className="flex items-center gap-2">
                <div className="flex items-center gap-2">
                  <div
                    className={clsx(
                      'w-7 h-7 rounded-full flex items-center justify-center text-xs font-semibold',
                      currentStep === step.number
                        ? 'bg-emerald-500/20 border-2 border-emerald-500 text-emerald-400'
                        : currentStep > step.number
                          ? 'bg-emerald-500 text-white'
                          : 'bg-slate-700/50 border-2 border-slate-600 text-slate-500'
                    )}
                  >
                    {currentStep > step.number ? '✓' : step.number}
                  </div>
                  <span
                    className={clsx(
                      'text-sm',
                      currentStep === step.number
                        ? 'text-emerald-400 font-medium'
                        : currentStep > step.number
                          ? 'text-white'
                          : 'text-slate-500'
                    )}
                  >
                    {step.label}
                  </span>
                </div>
                {index < steps.length - 1 && (
                  <div
                    className="w-12 h-0.5 mx-2"
                    style={{ background: currentStep > step.number ? '#22c55e' : borderColor }}
                  />
                )}
              </div>
            ))}
          </div>

          <AnimatePresence mode="wait">
            {/* Step 1: File Selection */}
            {currentStep === 1 && (
              <motion.div
                key="step1"
                initial={{ opacity: 0, x: 20 }}
                animate={{ opacity: 1, x: 0 }}
                exit={{ opacity: 0, x: -20 }}
              >
                {/* Portfolio Selector */}
                <div className="mb-6">
                  <label className="block text-sm font-medium mb-2" style={{ color: textColor }}>
                    Target Portfolio
                  </label>
                  <select
                    value={selectedPortfolio}
                    onChange={(e) => setSelectedPortfolio(e.target.value)}
                    className="w-full px-3 py-2 rounded-lg text-sm"
                    style={{
                      background: cardBg,
                      border: `1px solid ${borderColor}`,
                      color: textColor,
                    }}
                  >
                    <option value="alpha-growth">Alpha Growth</option>
                    <option value="beta-momentum">Beta Momentum</option>
                    <option value="gamma-value">Gamma Value</option>
                    <option value="delta-quant">Delta Quant</option>
                  </select>
                </div>

                {/* File Drop Zone */}
                <div
                  onDragOver={(e) => e.preventDefault()}
                  onDrop={handleFileDrop}
                  className={clsx(
                    'border-2 border-dashed rounded-xl p-8 text-center transition-all cursor-pointer',
                    selectedFile ? 'border-emerald-500/50 bg-emerald-500/10' : 'border-slate-600 hover:border-slate-500'
                  )}
                  onClick={() => document.getElementById('file-input')?.click()}
                >
                  <input
                    id="file-input"
                    type="file"
                    accept=".csv,.xlsx,.xls"
                    onChange={handleFileSelect}
                    className="hidden"
                  />
                  {selectedFile ? (
                    <div>
                      <div className="text-3xl mb-3">📄</div>
                      <div className="font-medium mb-1" style={{ color: textColor }}>
                        {selectedFile.name}
                      </div>
                      <div className="text-sm" style={{ color: mutedColor }}>
                        {(selectedFile.size / 1024).toFixed(1)} KB
                      </div>
                      <button
                        onClick={(e) => {
                          e.stopPropagation()
                          setSelectedFile(null)
                        }}
                        className="mt-3 text-sm text-red-400 hover:text-red-300"
                      >
                        Remove
                      </button>
                    </div>
                  ) : (
                    <div>
                      <div className="text-3xl mb-3">📁</div>
                      <div className="font-medium mb-1" style={{ color: textColor }}>
                        Drop file here or click to browse
                      </div>
                      <div className="text-sm" style={{ color: mutedColor }}>
                        Supports: CSV, Excel (.xlsx, .xls)
                      </div>
                    </div>
                  )}
                </div>

                {/* Google Sheet URL option */}
                {mode === 'google' && (
                  <div className="mt-6">
                    <label className="block text-sm font-medium mb-2" style={{ color: textColor }}>
                      Or paste Google Sheets URL
                    </label>
                    <input
                      type="url"
                      placeholder="https://docs.google.com/spreadsheets/d/..."
                      className="w-full px-3 py-2 rounded-lg text-sm"
                      style={{
                        background: cardBg,
                        border: `1px solid ${borderColor}`,
                        color: textColor,
                      }}
                    />
                  </div>
                )}
              </motion.div>
            )}

            {/* Step 2: Column Mapping */}
            {currentStep === 2 && (
              <motion.div
                key="step2"
                initial={{ opacity: 0, x: 20 }}
                animate={{ opacity: 1, x: 0 }}
                exit={{ opacity: 0, x: -20 }}
              >
                <div className="mb-4">
                  <div className="text-sm" style={{ color: mutedColor }}>
                    File: <span style={{ color: textColor }}>{selectedFile?.name}</span> (95 rows)
                  </div>
                  <div className="text-sm" style={{ color: mutedColor }}>
                    Mode: <span style={{ color: textColor }}>{modeLabels[mode]}</span>
                  </div>
                </div>

                <div
                  className="rounded-lg overflow-hidden"
                  style={{ border: `1px solid ${borderColor}` }}
                >
                  <table className="w-full">
                    <thead style={{ background: headerBg }}>
                      <tr>
                        <th className="px-4 py-3 text-left text-xs font-semibold" style={{ color: mutedColor }}>
                          File Column
                        </th>
                        <th className="px-4 py-3 text-left text-xs font-semibold" style={{ color: mutedColor }}>
                          Maps To
                        </th>
                        <th className="px-4 py-3 text-left text-xs font-semibold" style={{ color: mutedColor }}>
                          Sample Value
                        </th>
                      </tr>
                    </thead>
                    <tbody>
                      {mappedColumns.map((col, index) => (
                        <tr
                          key={index}
                          style={{ borderTop: `1px solid ${borderColor}` }}
                        >
                          <td className="px-4 py-3 text-sm" style={{ color: textColor }}>
                            {col.fileColumn}
                          </td>
                          <td className="px-4 py-3">
                            <select
                              value={col.mapsTo}
                              onChange={(e) => {
                                const newCols = [...mappedColumns]
                                newCols[index].mapsTo = e.target.value
                                setMappedColumns(newCols)
                              }}
                              className="px-2 py-1 rounded text-sm"
                              style={{
                                background: cardBg,
                                border: `1px solid ${borderColor}`,
                                color: textColor,
                              }}
                            >
                              <option value="Ticker">Ticker</option>
                              <option value="Quantity">Quantity</option>
                              <option value="Price">Price</option>
                              <option value="Cost Basis">Cost Basis</option>
                              <option value="Instr Type">Instr Type</option>
                              <option value="-- Skip --">-- Skip --</option>
                            </select>
                          </td>
                          <td className="px-4 py-3 text-sm font-mono" style={{ color: mutedColor }}>
                            {col.sampleValue}
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>

                {unmatchedCount > 0 && (
                  <div
                    className="mt-4 flex items-center gap-2 p-3 rounded-lg"
                    style={{
                      background: 'rgba(245, 158, 11, 0.1)',
                      border: '1px solid rgba(245, 158, 11, 0.3)',
                    }}
                  >
                    <span className="text-amber-400">⚠️</span>
                    <span className="text-sm text-amber-400">
                      {unmatchedCount} securities may not match (will queue for review)
                    </span>
                  </div>
                )}
              </motion.div>
            )}

            {/* Step 3: Reconciliation Preview */}
            {currentStep === 3 && mode === 'portfolio' && (
              <motion.div
                key="step3"
                initial={{ opacity: 0, x: 20 }}
                animate={{ opacity: 1, x: 0 }}
                exit={{ opacity: 0, x: -20 }}
                className="space-y-4"
              >
                {/* Summary Header */}
                <div
                  className="flex justify-between items-center p-4 rounded-lg"
                  style={{ background: cardBg }}
                >
                  <div>
                    <div className="text-sm" style={{ color: mutedColor }}>
                      Portfolio: <span className="font-medium" style={{ color: textColor }}>Alpha Growth</span>
                    </div>
                    <div className="text-sm" style={{ color: mutedColor }}>
                      Import: 95 positions | System: 100 positions
                    </div>
                  </div>
                  <div className="text-sm" style={{ color: mutedColor }}>
                    As of: Jan 19, 2026 16:00
                  </div>
                </div>

                {/* Matched Section */}
                <div
                  className="rounded-lg overflow-hidden"
                  style={{ border: `1px solid ${borderColor}` }}
                >
                  <div
                    className="flex items-center justify-between px-4 py-3"
                    style={{ background: 'rgba(34, 197, 94, 0.1)' }}
                  >
                    <div className="flex items-center gap-2">
                      <span className="text-emerald-400">✓</span>
                      <span className="font-medium text-emerald-400">MATCHED ({matchedCount} positions)</span>
                    </div>
                    <span className="text-sm" style={{ color: mutedColor }}>Identical in file and system</span>
                  </div>
                </div>

                {/* Mismatch Section */}
                {mismatchCount > 0 && (
                  <div
                    className="rounded-lg overflow-hidden"
                    style={{ border: `1px solid ${borderColor}` }}
                  >
                    <div
                      className="flex items-center justify-between px-4 py-3"
                      style={{ background: 'rgba(245, 158, 11, 0.1)' }}
                    >
                      <div className="flex items-center gap-2">
                        <span className="text-amber-400">⚠️</span>
                        <span className="font-medium text-amber-400">QUANTITY MISMATCH ({mismatchCount} positions)</span>
                      </div>
                      <div className="flex gap-2">
                        <button
                          onClick={() => handleSelectAll('mismatch', 'update')}
                          className="text-xs px-2 py-1 rounded bg-blue-500/20 text-blue-400 hover:bg-blue-500/30"
                        >
                          Update All
                        </button>
                        <button
                          onClick={() => handleSelectAll('mismatch', 'keep')}
                          className="text-xs px-2 py-1 rounded bg-slate-500/20 text-slate-400 hover:bg-slate-500/30"
                        >
                          Keep All
                        </button>
                      </div>
                    </div>
                    <table className="w-full">
                      <thead style={{ background: headerBg }}>
                        <tr>
                          <th className="px-4 py-2 text-left text-xs font-semibold" style={{ color: mutedColor }}>Security</th>
                          <th className="px-4 py-2 text-right text-xs font-semibold" style={{ color: mutedColor }}>System</th>
                          <th className="px-4 py-2 text-right text-xs font-semibold" style={{ color: mutedColor }}>Import</th>
                          <th className="px-4 py-2 text-center text-xs font-semibold" style={{ color: mutedColor }}>Action</th>
                        </tr>
                      </thead>
                      <tbody>
                        {reconciliationItems
                          .filter(i => i.type === 'mismatch')
                          .map((item) => (
                            <tr key={item.id} style={{ borderTop: `1px solid ${borderColor}` }}>
                              <td className="px-4 py-2 text-sm font-medium" style={{ color: textColor }}>{item.security}</td>
                              <td className="px-4 py-2 text-right text-sm font-mono" style={{ color: textColor }}>{item.systemQty?.toLocaleString()}</td>
                              <td className="px-4 py-2 text-right text-sm font-mono" style={{ color: textColor }}>{item.importQty?.toLocaleString()}</td>
                              <td className="px-4 py-2 text-center">
                                <div className="flex justify-center gap-2">
                                  <button
                                    onClick={() => handleReconciliationAction(item.id, 'update')}
                                    className={clsx(
                                      'px-2 py-1 rounded text-xs font-medium transition-all',
                                      item.action === 'update'
                                        ? 'bg-blue-500 text-white'
                                        : 'bg-blue-500/20 text-blue-400 hover:bg-blue-500/30'
                                    )}
                                  >
                                    Update
                                  </button>
                                  <button
                                    onClick={() => handleReconciliationAction(item.id, 'keep')}
                                    className={clsx(
                                      'px-2 py-1 rounded text-xs font-medium transition-all',
                                      item.action === 'keep'
                                        ? 'bg-slate-500 text-white'
                                        : 'bg-slate-500/20 text-slate-400 hover:bg-slate-500/30'
                                    )}
                                  >
                                    Keep
                                  </button>
                                </div>
                              </td>
                            </tr>
                          ))}
                      </tbody>
                    </table>
                  </div>
                )}

                {/* Stale Section */}
                {staleCount > 0 && (
                  <div
                    className="rounded-lg overflow-hidden"
                    style={{ border: `1px solid ${borderColor}` }}
                  >
                    <div
                      className="flex items-center justify-between px-4 py-3"
                      style={{ background: 'rgba(239, 68, 68, 0.1)' }}
                    >
                      <div className="flex items-center gap-2">
                        <span className="text-red-400">✕</span>
                        <span className="font-medium text-red-400">STALE POSITIONS ({staleCount} positions)</span>
                      </div>
                      <div className="flex gap-2">
                        <button
                          onClick={() => handleSelectAll('stale', 'delete')}
                          className="text-xs px-2 py-1 rounded bg-red-500/20 text-red-400 hover:bg-red-500/30"
                        >
                          Delete All
                        </button>
                        <button
                          onClick={() => handleSelectAll('stale', 'keep')}
                          className="text-xs px-2 py-1 rounded bg-slate-500/20 text-slate-400 hover:bg-slate-500/30"
                        >
                          Keep All
                        </button>
                      </div>
                    </div>
                    <table className="w-full">
                      <thead style={{ background: headerBg }}>
                        <tr>
                          <th className="px-4 py-2 text-left text-xs font-semibold" style={{ color: mutedColor }}>Security</th>
                          <th className="px-4 py-2 text-right text-xs font-semibold" style={{ color: mutedColor }}>Quantity</th>
                          <th className="px-4 py-2 text-right text-xs font-semibold" style={{ color: mutedColor }}>Value</th>
                          <th className="px-4 py-2 text-center text-xs font-semibold" style={{ color: mutedColor }}>Action</th>
                        </tr>
                      </thead>
                      <tbody>
                        {reconciliationItems
                          .filter(i => i.type === 'stale')
                          .map((item) => (
                            <tr key={item.id} style={{ borderTop: `1px solid ${borderColor}` }}>
                              <td className="px-4 py-2 text-sm font-medium" style={{ color: textColor }}>{item.security}</td>
                              <td className="px-4 py-2 text-right text-sm font-mono" style={{ color: textColor }}>{item.systemQty?.toLocaleString()}</td>
                              <td className="px-4 py-2 text-right text-sm font-mono" style={{ color: textColor }}>${item.systemValue?.toLocaleString()}</td>
                              <td className="px-4 py-2 text-center">
                                <div className="flex justify-center gap-2">
                                  <button
                                    onClick={() => handleReconciliationAction(item.id, 'delete')}
                                    className={clsx(
                                      'px-2 py-1 rounded text-xs font-medium transition-all',
                                      item.action === 'delete'
                                        ? 'bg-red-500 text-white'
                                        : 'bg-red-500/20 text-red-400 hover:bg-red-500/30'
                                    )}
                                  >
                                    Delete
                                  </button>
                                  <button
                                    onClick={() => handleReconciliationAction(item.id, 'keep')}
                                    className={clsx(
                                      'px-2 py-1 rounded text-xs font-medium transition-all',
                                      item.action === 'keep'
                                        ? 'bg-slate-500 text-white'
                                        : 'bg-slate-500/20 text-slate-400 hover:bg-slate-500/30'
                                    )}
                                  >
                                    Keep
                                  </button>
                                </div>
                              </td>
                            </tr>
                          ))}
                      </tbody>
                    </table>
                    <div className="px-4 py-2 text-xs text-red-400" style={{ background: 'rgba(239, 68, 68, 0.05)' }}>
                      ⚠️ Deleting positions is permanent
                    </div>
                  </div>
                )}

                {/* New Positions Section */}
                {newCount > 0 && (
                  <div
                    className="rounded-lg overflow-hidden"
                    style={{ border: `1px solid ${borderColor}` }}
                  >
                    <div
                      className="flex items-center justify-between px-4 py-3"
                      style={{ background: 'rgba(59, 130, 246, 0.1)' }}
                    >
                      <div className="flex items-center gap-2">
                        <span className="text-blue-400">+</span>
                        <span className="font-medium text-blue-400">NEW POSITIONS ({newCount} positions)</span>
                      </div>
                    </div>
                    <table className="w-full">
                      <thead style={{ background: headerBg }}>
                        <tr>
                          <th className="px-4 py-2 text-left text-xs font-semibold" style={{ color: mutedColor }}>Security</th>
                          <th className="px-4 py-2 text-right text-xs font-semibold" style={{ color: mutedColor }}>Quantity</th>
                          <th className="px-4 py-2 text-right text-xs font-semibold" style={{ color: mutedColor }}>Est Value</th>
                          <th className="px-4 py-2 text-center text-xs font-semibold" style={{ color: mutedColor }}>Status</th>
                        </tr>
                      </thead>
                      <tbody>
                        {reconciliationItems
                          .filter(i => i.type === 'new')
                          .map((item) => (
                            <tr key={item.id} style={{ borderTop: `1px solid ${borderColor}` }}>
                              <td className="px-4 py-2 text-sm font-medium" style={{ color: textColor }}>{item.security}</td>
                              <td className="px-4 py-2 text-right text-sm font-mono" style={{ color: textColor }}>{item.importQty?.toLocaleString()}</td>
                              <td className="px-4 py-2 text-right text-sm font-mono" style={{ color: textColor }}>${item.importValue?.toLocaleString()}</td>
                              <td className="px-4 py-2 text-center">
                                {item.status === 'ready' ? (
                                  <span className="text-xs px-2 py-1 rounded bg-emerald-500/20 text-emerald-400">
                                    ✓ Ready to add
                                  </span>
                                ) : (
                                  <button className="text-xs px-2 py-1 rounded bg-amber-500/20 text-amber-400 hover:bg-amber-500/30">
                                    ⚠️ Resolve
                                  </button>
                                )}
                              </td>
                            </tr>
                          ))}
                      </tbody>
                    </table>
                  </div>
                )}

                {/* Summary */}
                <div
                  className="p-4 rounded-lg"
                  style={{ background: cardBg }}
                >
                  <div className="text-sm font-semibold mb-2" style={{ color: textColor }}>
                    Summary of Changes:
                  </div>
                  <ul className="text-sm space-y-1" style={{ color: mutedColor }}>
                    <li>• Update {updatesSelected} positions</li>
                    <li>• Delete {deletesSelected} positions</li>
                    <li>• Add {addsReady} new positions ({unmatchedCount > 0 ? `${unmatchedCount} pending mapping` : 'all ready'})</li>
                  </ul>
                </div>

                {!canProceed() && (
                  <div
                    className="p-3 rounded-lg text-sm"
                    style={{
                      background: 'rgba(245, 158, 11, 0.1)',
                      border: '1px solid rgba(245, 158, 11, 0.3)',
                      color: '#fbbf24',
                    }}
                  >
                    ⚠️ You must resolve all unmatched securities and select an action for each mismatch before applying.
                  </div>
                )}
              </motion.div>
            )}

            {/* Step 3 for non-portfolio modes */}
            {currentStep === 3 && mode !== 'portfolio' && (
              <motion.div
                key="step3-simple"
                initial={{ opacity: 0, x: 20 }}
                animate={{ opacity: 1, x: 0 }}
                exit={{ opacity: 0, x: -20 }}
                className="text-center py-8"
              >
                <div className="text-4xl mb-4">✓</div>
                <h3 className="text-lg font-semibold mb-2" style={{ color: textColor }}>
                  Ready to Import
                </h3>
                <p className="text-sm mb-4" style={{ color: mutedColor }}>
                  {mode === 'trades' && '95 trades will be added to Alpha Growth'}
                  {mode === 'delta' && '15 positions will be updated'}
                  {mode === 'google' && 'Sheet will be connected for syncing'}
                  {mode === 'fix' && 'FIX message will be processed'}
                </p>
              </motion.div>
            )}
          </AnimatePresence>
        </div>

        {/* Footer */}
        <div
          className="flex justify-between items-center px-5 py-4"
          style={{ background: headerBg, borderTop: `1px solid ${borderColor}` }}
        >
          <button
            onClick={currentStep === 1 ? onClose : () => setCurrentStep(s => s - 1)}
            className="px-4 py-2 rounded-lg text-sm font-medium transition-all"
            style={{
              background: 'transparent',
              border: `1px solid ${borderColor}`,
              color: mutedColor,
            }}
          >
            {currentStep === 1 ? 'Cancel' : '← Back'}
          </button>
          <button
            onClick={() => {
              if (currentStep < 3) {
                setCurrentStep(s => s + 1)
              } else {
                handleApply()
              }
            }}
            disabled={!canProceed() || isProcessing}
            className={clsx(
              'px-4 py-2 rounded-lg text-sm font-medium transition-all',
              canProceed() && !isProcessing
                ? 'bg-emerald-500 text-white hover:bg-emerald-600'
                : 'bg-slate-600 text-slate-400 cursor-not-allowed'
            )}
          >
            {isProcessing ? (
              <span className="flex items-center gap-2">
                <span className="animate-spin">↻</span>
                Processing...
              </span>
            ) : currentStep < 3 ? (
              'Continue →'
            ) : (
              'Apply Changes'
            )}
          </button>
        </div>
      </motion.div>
    </motion.div>
  )
}
