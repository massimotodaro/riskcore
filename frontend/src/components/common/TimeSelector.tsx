import { useState, useRef, useEffect } from 'react'
import { useTheme } from '../../context/ThemeContext'
import clsx from 'clsx'

export interface TimePreset {
  type: string
  label: string
  sublabel?: string
  isHistorical: boolean
}

interface TimeSelectorProps {
  presets?: TimePreset[]
  selectedPreset: TimePreset
  onSelect: (preset: TimePreset) => void
  showCustomDateTime?: boolean
  className?: string
}

// Default presets that can be used across the platform
export const DEFAULT_TIME_PRESETS: TimePreset[] = [
  { type: 'live', label: 'Latest', sublabel: 'Most recent import', isHistorical: false },
  { type: 'cob', label: 'COB Yesterday', sublabel: 'Close of business', isHistorical: true },
  { type: 'som', label: 'Start of Month', sublabel: 'Month beginning', isHistorical: true },
  { type: 'soq', label: 'Start of Quarter', sublabel: 'Quarter beginning', isHistorical: true },
  { type: 'soy', label: 'Start of Year', sublabel: 'Year beginning', isHistorical: true },
]

export default function TimeSelector({
  presets = DEFAULT_TIME_PRESETS,
  selectedPreset,
  onSelect,
  showCustomDateTime = true,
  className,
}: TimeSelectorProps) {
  const { isDarkMode } = useTheme()
  const [isOpen, setIsOpen] = useState(false)
  const [customDateTime, setCustomDateTime] = useState('')
  const dropdownRef = useRef<HTMLDivElement>(null)

  // Close dropdown when clicking outside
  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (dropdownRef.current && !dropdownRef.current.contains(event.target as Node)) {
        setIsOpen(false)
      }
    }
    document.addEventListener('mousedown', handleClickOutside)
    return () => document.removeEventListener('mousedown', handleClickOutside)
  }, [])

  const handleSelectPreset = (preset: TimePreset) => {
    onSelect(preset)
    setIsOpen(false)
  }

  const handleApplyCustom = () => {
    if (customDateTime) {
      const customPreset: TimePreset = {
        type: 'custom',
        label: new Date(customDateTime).toLocaleString(),
        sublabel: 'Custom date/time',
        isHistorical: true,
      }
      onSelect(customPreset)
      setIsOpen(false)
    }
  }

  return (
    <div className={clsx('relative', className)} ref={dropdownRef}>
      {/* Dropdown Button */}
      <button
        onClick={() => setIsOpen(!isOpen)}
        className={clsx(
          'h-9 px-3 rounded-lg text-xs font-medium flex items-center gap-2 transition-all',
          isDarkMode
            ? 'bg-slate-700/80 border border-white/10 text-slate-200 hover:bg-slate-700'
            : 'bg-white border border-slate-200 text-slate-700 hover:bg-slate-50'
        )}
      >
        {/* Live/Historical Dot */}
        <span
          className={clsx(
            'w-2 h-2 rounded-full',
            selectedPreset.isHistorical
              ? 'bg-amber-500'
              : 'bg-emerald-500 animate-pulse'
          )}
        />
        <span>{selectedPreset.label}</span>
        <span className={clsx('text-[10px]', isDarkMode ? 'text-slate-400' : 'text-slate-500')}>
          ▼
        </span>
      </button>

      {/* Dropdown Menu */}
      {isOpen && (
        <div
          className={clsx(
            'absolute top-full left-0 mt-1 min-w-[220px] max-h-[400px] overflow-y-auto rounded-lg z-50 shadow-lg',
            isDarkMode
              ? 'bg-slate-800/98 border border-white/15'
              : 'bg-white border border-slate-200'
          )}
        >
          {/* Presets Section */}
          <div className={clsx('py-2 border-b', isDarkMode ? 'border-white/5' : 'border-slate-100')}>
            <div
              className={clsx(
                'px-3 py-1 text-[10px] font-semibold uppercase tracking-wide',
                isDarkMode ? 'text-slate-500' : 'text-slate-400'
              )}
            >
              Snapshots
            </div>
            {presets.map((preset) => (
              <div
                key={preset.type}
                onClick={() => handleSelectPreset(preset)}
                className={clsx(
                  'flex items-center gap-2.5 px-3 py-2 cursor-pointer transition-colors',
                  selectedPreset.type === preset.type
                    ? isDarkMode
                      ? 'bg-blue-500/10'
                      : 'bg-blue-50'
                    : isDarkMode
                    ? 'hover:bg-slate-700/50'
                    : 'hover:bg-slate-50'
                )}
              >
                {/* Radio Circle */}
                <div
                  className={clsx(
                    'w-3.5 h-3.5 rounded-full border-2',
                    selectedPreset.type === preset.type
                      ? 'border-blue-500 bg-blue-500'
                      : isDarkMode
                      ? 'border-slate-500'
                      : 'border-slate-300'
                  )}
                  style={{
                    boxShadow:
                      selectedPreset.type === preset.type
                        ? 'inset 0 0 0 3px ' + (isDarkMode ? '#1e293b' : '#fff')
                        : 'none',
                  }}
                />
                <div className="flex-1">
                  <div
                    className={clsx(
                      'text-[13px]',
                      isDarkMode ? 'text-slate-200' : 'text-slate-700'
                    )}
                  >
                    {preset.label}
                  </div>
                  {preset.sublabel && (
                    <div
                      className={clsx(
                        'text-[11px]',
                        isDarkMode ? 'text-slate-500' : 'text-slate-400'
                      )}
                    >
                      {preset.sublabel}
                    </div>
                  )}
                </div>
              </div>
            ))}
          </div>

          {/* Custom Date/Time Section */}
          {showCustomDateTime && (
            <div className="p-3">
              <div
                className={clsx(
                  'text-[10px] font-semibold uppercase tracking-wide mb-2',
                  isDarkMode ? 'text-slate-500' : 'text-slate-400'
                )}
              >
                Custom Date & Time
              </div>
              <div className="flex gap-2">
                <input
                  type="datetime-local"
                  value={customDateTime}
                  onChange={(e) => setCustomDateTime(e.target.value)}
                  className={clsx(
                    'flex-1 px-2 py-1.5 rounded text-xs',
                    isDarkMode
                      ? 'bg-slate-700/50 border border-white/10 text-slate-200'
                      : 'bg-slate-100 border border-slate-200 text-slate-700'
                  )}
                />
                <button
                  onClick={handleApplyCustom}
                  className="px-3 py-1.5 bg-blue-500 text-white rounded text-xs font-medium hover:bg-blue-600 transition-colors"
                >
                  Apply
                </button>
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  )
}
