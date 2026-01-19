import { useState } from 'react'
import { useTheme } from '../../context/ThemeContext'
import clsx from 'clsx'

interface CalculateButtonProps {
  onCalculate: () => void | Promise<void>
  timestamp?: string
  showTimestamp?: boolean
  isHistorical?: boolean
  className?: string
}

export default function CalculateButton({
  onCalculate,
  timestamp = 'Just now',
  showTimestamp = true,
  isHistorical = false,
  className,
}: CalculateButtonProps) {
  const { isDarkMode } = useTheme()
  const [isCalculating, setIsCalculating] = useState(false)

  const handleClick = async () => {
    setIsCalculating(true)
    try {
      await onCalculate()
    } finally {
      // Minimum animation time for visual feedback
      setTimeout(() => {
        setIsCalculating(false)
      }, 500)
    }
  }

  return (
    <div className={clsx('flex items-center gap-3', className)}>
      {/* Calculate Button */}
      <button
        onClick={handleClick}
        disabled={isCalculating}
        className={clsx(
          'h-9 px-3 rounded-lg text-xs font-medium flex items-center gap-1.5 transition-all',
          isHistorical
            ? isDarkMode
              ? 'bg-amber-500/15 border border-amber-500/30 text-amber-400 hover:bg-amber-500/25'
              : 'bg-amber-50 border border-amber-200 text-amber-600 hover:bg-amber-100'
            : isDarkMode
            ? 'bg-emerald-500/15 border border-emerald-500/30 text-emerald-400 hover:bg-emerald-500/25'
            : 'bg-emerald-50 border border-emerald-200 text-emerald-600 hover:bg-emerald-100',
          isCalculating && 'opacity-75 cursor-not-allowed'
        )}
      >
        <span
          className={clsx(
            'text-sm',
            isCalculating && 'animate-spin'
          )}
        >
          ↻
        </span>
        <span>Calculate</span>
      </button>

      {/* Timestamp */}
      {showTimestamp && (
        <span
          className={clsx(
            'text-xs',
            isDarkMode ? 'text-slate-500' : 'text-slate-400'
          )}
        >
          Imported: {timestamp}
        </span>
      )}
    </div>
  )
}
