import { useState, useRef, useEffect } from 'react'
import { useTheme } from '../../context/ThemeContext'
import clsx from 'clsx'

export interface Portfolio {
  id: string
  name: string
}

interface PortfolioSelectorProps {
  portfolios: Portfolio[]
  selectedIds: string[]
  onChange: (selectedIds: string[]) => void
  className?: string
}

export default function PortfolioSelector({
  portfolios,
  selectedIds,
  onChange,
  className,
}: PortfolioSelectorProps) {
  const { isDarkMode } = useTheme()
  const [isOpen, setIsOpen] = useState(false)
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

  const allSelected = selectedIds.length === portfolios.length
  const noneSelected = selectedIds.length === 0

  const togglePortfolio = (id: string) => {
    if (selectedIds.includes(id)) {
      // Don't allow deselecting if it's the last one
      if (selectedIds.length > 1) {
        onChange(selectedIds.filter((i) => i !== id))
      }
    } else {
      onChange([...selectedIds, id])
    }
  }

  const selectAll = () => {
    onChange(portfolios.map((p) => p.id))
  }

  const getSelectionText = () => {
    if (allSelected) return 'All'
    if (noneSelected) return 'None'
    return `${selectedIds.length} selected`
  }

  return (
    <div className={clsx('flex items-center gap-2', className)} ref={dropdownRef}>
      {/* Dropdown Button */}
      <div className="relative">
        <button
          onClick={() => setIsOpen(!isOpen)}
          className={clsx(
            'h-9 px-3 rounded-lg text-xs font-medium flex items-center gap-2 transition-all',
            isDarkMode
              ? 'bg-slate-700/80 border border-white/10 text-slate-200 hover:bg-slate-700'
              : 'bg-white border border-slate-200 text-slate-700 hover:bg-slate-50'
          )}
        >
          <span>Portfolios</span>
          <span className={clsx('text-[10px]', isDarkMode ? 'text-slate-400' : 'text-slate-500')}>
            ▼
          </span>
        </button>

        {/* Dropdown Menu */}
        {isOpen && (
          <div
            className={clsx(
              'absolute top-full left-0 mt-1 min-w-[220px] max-h-[300px] overflow-y-auto rounded-lg z-50 shadow-lg',
              isDarkMode
                ? 'bg-slate-800/98 border border-white/15'
                : 'bg-white border border-slate-200'
            )}
          >
            {/* Header */}
            <div
              className={clsx(
                'px-3 py-2.5 flex justify-between items-center border-b',
                isDarkMode ? 'border-white/10' : 'border-slate-100'
              )}
            >
              <span
                className={clsx(
                  'text-[11px] uppercase tracking-wide',
                  isDarkMode ? 'text-slate-500' : 'text-slate-500'
                )}
              >
                Select Portfolios
              </span>
              <button
                onClick={selectAll}
                className="text-[10px] text-blue-500 hover:underline"
              >
                Select All
              </button>
            </div>

            {/* Portfolio Items */}
            {portfolios.map((portfolio) => (
              <div
                key={portfolio.id}
                className={clsx(
                  'flex items-center gap-2.5 px-3 py-2.5 cursor-pointer transition-colors',
                  isDarkMode ? 'hover:bg-slate-700/50' : 'hover:bg-slate-50'
                )}
                onClick={() => togglePortfolio(portfolio.id)}
              >
                <input
                  type="checkbox"
                  checked={selectedIds.includes(portfolio.id)}
                  onChange={() => togglePortfolio(portfolio.id)}
                  className="w-4 h-4 cursor-pointer accent-[#3CD574]"
                />
                <label
                  className={clsx(
                    'text-[13px] cursor-pointer flex-1',
                    isDarkMode ? 'text-slate-200' : 'text-slate-700'
                  )}
                >
                  {portfolio.name}
                </label>
              </div>
            ))}
          </div>
        )}
      </div>

      {/* Selection Text (outside the button) */}
      <span
        className={clsx(
          'text-xs',
          allSelected
            ? 'text-[#3CD574] font-semibold'
            : isDarkMode
            ? 'text-slate-400'
            : 'text-slate-500'
        )}
      >
        {getSelectionText()}
      </span>
    </div>
  )
}
