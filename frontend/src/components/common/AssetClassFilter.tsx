import clsx from 'clsx'
import type { RiskPodType } from '../../types'
import { RISKPOD_COLORS } from '../../services/api'

interface AssetClassFilterProps {
  selected: RiskPodType[]
  onChange: (selected: RiskPodType[]) => void
  className?: string
}

// Use brand colors from api.ts
const RISKPODS: { key: RiskPodType; label: string; color: string }[] = [
  { key: 'equity', label: 'Equity', color: RISKPOD_COLORS.equity },
  { key: 'rates', label: 'Rates', color: RISKPOD_COLORS.rates },
  { key: 'credit', label: 'Credit', color: RISKPOD_COLORS.credit },
  { key: 'fx', label: 'FX', color: RISKPOD_COLORS.fx },
  { key: 'commodities', label: 'Commodities', color: RISKPOD_COLORS.commodities },
  { key: 'other', label: 'Other', color: RISKPOD_COLORS.other },
]

export default function AssetClassFilter({
  selected,
  onChange,
  className,
}: AssetClassFilterProps) {
  const togglePod = (pod: RiskPodType) => {
    if (selected.includes(pod)) {
      // Remove if already selected (but keep at least one)
      if (selected.length > 1) {
        onChange(selected.filter((p) => p !== pod))
      }
    } else {
      // Add to selection
      onChange([...selected, pod])
    }
  }

  const selectAll = () => {
    onChange(RISKPODS.map((p) => p.key))
  }

  const allSelected = selected.length === RISKPODS.length

  return (
    <div className={clsx('flex items-center gap-2', className)}>
      {/* All button */}
      <button
        onClick={selectAll}
        className={clsx(
          'px-3 py-1.5 rounded-full text-xs font-medium transition-colors',
          allSelected
            ? 'bg-white/10 text-white border border-white/20'
            : 'bg-white/5 text-slate-400 border border-white/5 hover:border-white/10'
        )}
      >
        All
      </button>

      {/* RiskPod pills */}
      {RISKPODS.map((pod) => {
        const isSelected = selected.includes(pod.key)
        return (
          <button
            key={pod.key}
            onClick={() => togglePod(pod.key)}
            className={clsx(
              'flex items-center gap-1.5 px-3 py-1.5 rounded-full text-xs font-medium transition-all',
              isSelected
                ? 'bg-white/10 text-white border border-white/20'
                : 'bg-white/5 text-slate-500 border border-transparent hover:border-white/10'
            )}
          >
            <span
              className="w-2 h-2 rounded-full transition-opacity"
              style={{
                backgroundColor: pod.color,
                opacity: isSelected ? 1 : 0.3,
              }}
            />
            <span>{pod.label}</span>
          </button>
        )
      })}
    </div>
  )
}
