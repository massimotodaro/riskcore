import { useState, useEffect } from 'react'
import { useQuery } from '@tanstack/react-query'
import { motion, AnimatePresence } from 'framer-motion'
import clsx from 'clsx'
import { tradesPageApi, formatDateTime } from '../../services/api'
import type { TimePreset, SnapshotInfo } from '../../types'

interface TimeSelectorProps {
  value: string | null  // null = Latest, ISO string = historical
  onChange: (value: string | null) => void
  tenantId?: string
  className?: string
}

export default function TimeSelector({
  value,
  onChange,
  tenantId,
  className,
}: TimeSelectorProps) {
  const [isOpen, setIsOpen] = useState(false)
  const [showDatePicker, setShowDatePicker] = useState(false)

  // Fetch time presets
  const { data: presets = [] } = useQuery({
    queryKey: ['time-presets', tenantId],
    queryFn: () => tradesPageApi.getTimePresets(tenantId),
    staleTime: 60000,
  })

  // Fetch available snapshots for custom date picker
  const { data: snapshots = [] } = useQuery({
    queryKey: ['snapshots', tenantId],
    queryFn: () => tradesPageApi.getSnapshots(tenantId, 30),
    staleTime: 60000,
    enabled: showDatePicker,
  })

  // Get display label for current value
  const getDisplayLabel = () => {
    if (!value) return 'Latest'

    const preset = presets.find(p => p.timestamp === value)
    if (preset) return preset.label

    return formatDateTime(value)
  }

  const handlePresetSelect = (preset: TimePreset) => {
    onChange(preset.timestamp || null)
    setIsOpen(false)
    setShowDatePicker(false)
  }

  const handleSnapshotSelect = (snapshot: SnapshotInfo) => {
    onChange(snapshot.timestamp || null)
    setIsOpen(false)
    setShowDatePicker(false)
  }

  // Close on click outside
  useEffect(() => {
    const handleClickOutside = (e: MouseEvent) => {
      const target = e.target as HTMLElement
      if (!target.closest('.time-selector')) {
        setIsOpen(false)
        setShowDatePicker(false)
      }
    }
    document.addEventListener('click', handleClickOutside)
    return () => document.removeEventListener('click', handleClickOutside)
  }, [])

  return (
    <div className={clsx('time-selector relative', className)}>
      {/* Trigger Button */}
      <button
        onClick={() => setIsOpen(!isOpen)}
        className={clsx(
          'flex items-center gap-2 px-3 py-2 rounded-lg',
          'bg-white/5 border border-white/10 hover:border-white/20',
          'text-sm font-medium transition-colors',
          isOpen && 'border-blue-500/50'
        )}
      >
        <svg
          className="w-4 h-4 text-slate-400"
          fill="none"
          viewBox="0 0 24 24"
          stroke="currentColor"
        >
          <path
            strokeLinecap="round"
            strokeLinejoin="round"
            strokeWidth={1.5}
            d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z"
          />
        </svg>
        <span className="text-white">{getDisplayLabel()}</span>
        <svg
          className={clsx(
            'w-4 h-4 text-slate-400 transition-transform',
            isOpen && 'rotate-180'
          )}
          fill="none"
          viewBox="0 0 24 24"
          stroke="currentColor"
        >
          <path
            strokeLinecap="round"
            strokeLinejoin="round"
            strokeWidth={1.5}
            d="M19 9l-7 7-7-7"
          />
        </svg>
      </button>

      {/* Dropdown */}
      <AnimatePresence>
        {isOpen && (
          <motion.div
            initial={{ opacity: 0, y: -10 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -10 }}
            className={clsx(
              'absolute top-full left-0 mt-2 z-50',
              'min-w-[200px] rounded-lg',
              'glass border border-white/10 shadow-xl'
            )}
          >
            {!showDatePicker ? (
              /* Presets View */
              <div className="p-2">
                <div className="text-xs font-medium text-slate-500 px-2 py-1 mb-1">
                  Quick Select
                </div>
                {presets.map((preset) => (
                  <button
                    key={preset.type}
                    onClick={() => handlePresetSelect(preset)}
                    className={clsx(
                      'w-full flex items-center gap-2 px-3 py-2 rounded-md',
                      'text-sm text-left transition-colors',
                      (value === preset.timestamp || (!value && preset.type === 'latest'))
                        ? 'bg-blue-500/20 text-blue-300'
                        : 'hover:bg-white/5 text-slate-300'
                    )}
                  >
                    {preset.type === 'latest' && (
                      <span className="w-2 h-2 rounded-full bg-green-500 animate-pulse" />
                    )}
                    <span>{preset.label}</span>
                    {preset.date && (
                      <span className="ml-auto text-xs text-slate-500">
                        {preset.date}
                      </span>
                    )}
                  </button>
                ))}

                {/* Custom Date Button */}
                <div className="border-t border-white/10 mt-2 pt-2">
                  <button
                    onClick={() => setShowDatePicker(true)}
                    className="w-full flex items-center gap-2 px-3 py-2 rounded-md text-sm hover:bg-white/5 text-slate-300"
                  >
                    <svg
                      className="w-4 h-4 text-slate-400"
                      fill="none"
                      viewBox="0 0 24 24"
                      stroke="currentColor"
                    >
                      <path
                        strokeLinecap="round"
                        strokeLinejoin="round"
                        strokeWidth={1.5}
                        d="M8 7V3m8 4V3m-9 8h10M5 21h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v12a2 2 0 002 2z"
                      />
                    </svg>
                    <span>Custom Date...</span>
                  </button>
                </div>
              </div>
            ) : (
              /* Date Picker View */
              <div className="p-2">
                <div className="flex items-center justify-between mb-2">
                  <button
                    onClick={() => setShowDatePicker(false)}
                    className="p-1 hover:bg-white/5 rounded"
                  >
                    <svg
                      className="w-4 h-4 text-slate-400"
                      fill="none"
                      viewBox="0 0 24 24"
                      stroke="currentColor"
                    >
                      <path
                        strokeLinecap="round"
                        strokeLinejoin="round"
                        strokeWidth={1.5}
                        d="M15 19l-7-7 7-7"
                      />
                    </svg>
                  </button>
                  <span className="text-xs font-medium text-slate-500">
                    Available Snapshots
                  </span>
                  <div className="w-4" />
                </div>

                <div className="max-h-64 overflow-y-auto">
                  {snapshots.length === 0 ? (
                    <div className="text-sm text-slate-500 text-center py-4">
                      No historical snapshots available
                    </div>
                  ) : (
                    snapshots.map((snapshot) => (
                      <button
                        key={snapshot.snapshot_date}
                        onClick={() => handleSnapshotSelect(snapshot)}
                        className={clsx(
                          'w-full flex items-center justify-between px-3 py-2 rounded-md',
                          'text-sm text-left transition-colors',
                          value === snapshot.timestamp
                            ? 'bg-blue-500/20 text-blue-300'
                            : 'hover:bg-white/5 text-slate-300'
                        )}
                      >
                        <span>{snapshot.snapshot_date}</span>
                        <span className="text-xs text-slate-500">
                          {snapshot.position_count} pos
                        </span>
                      </button>
                    ))
                  )}
                </div>
              </div>
            )}
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  )
}
