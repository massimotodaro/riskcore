import { useEffect, useState } from 'react'
import { motion } from 'framer-motion'
import clsx from 'clsx'
import type { RiskCardProps } from '../../types'

// Animated number counter
function AnimatedNumber({ value, format }: { value: string; format?: (v: string) => string }) {
  const [displayValue, setDisplayValue] = useState(value)

  useEffect(() => {
    setDisplayValue(value)
  }, [value])

  return (
    <motion.span
      key={value}
      initial={{ opacity: 0, y: 10 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.3 }}
    >
      {format ? format(displayValue) : displayValue}
    </motion.span>
  )
}

export default function RiskCard({
  title,
  value,
  change,
  changeLabel = 'vs. yesterday',
  icon,
  color = 'neutral',
  subtitle,
}: RiskCardProps) {
  const isPositiveChange = change !== undefined && change > 0
  const isNegativeChange = change !== undefined && change < 0

  const glowClass = {
    green: 'hover:shadow-glow-green',
    red: 'hover:shadow-glow-red',
    yellow: 'hover:shadow-glow-amber',
    neutral: 'hover:shadow-glow-blue',
  }[color]

  const iconBgClass = {
    green: 'bg-emerald-500/20 text-emerald-400',
    red: 'bg-rose-500/20 text-rose-400',
    yellow: 'bg-amber-500/20 text-amber-400',
    neutral: 'bg-blue-500/20 text-blue-400',
  }[color]

  const valueColorClass = {
    green: 'text-emerald-400',
    red: 'text-rose-400',
    yellow: 'text-amber-400',
    neutral: 'text-slate-100',
  }[color]

  return (
    <motion.div
      whileHover={{ y: -2 }}
      transition={{ duration: 0.2 }}
      className={clsx(
        'risk-card group cursor-default',
        glowClass
      )}
    >
      <div className="flex items-start justify-between">
        <div className="space-y-1">
          <p className="metric-label">{title}</p>
          <p className={clsx('metric-value', valueColorClass)}>
            <AnimatedNumber value={String(value)} />
          </p>
          {subtitle && (
            <p className="text-sm text-slate-500">{subtitle}</p>
          )}
        </div>
        {icon && (
          <motion.div
            whileHover={{ scale: 1.05 }}
            className={clsx(
              'p-2.5 rounded-xl transition-colors duration-200',
              iconBgClass
            )}
          >
            {icon}
          </motion.div>
        )}
      </div>

      {change !== undefined && (
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ delay: 0.2 }}
          className="mt-4 pt-4 border-t border-white/5 flex items-center gap-2"
        >
          {isPositiveChange && (
            <span className="flex items-center text-sm text-emerald-400">
              <svg className="w-4 h-4 mr-0.5" fill="currentColor" viewBox="0 0 20 20">
                <path
                  fillRule="evenodd"
                  d="M5.293 9.707a1 1 0 010-1.414l4-4a1 1 0 011.414 0l4 4a1 1 0 01-1.414 1.414L11 7.414V15a1 1 0 11-2 0V7.414L6.707 9.707a1 1 0 01-1.414 0z"
                  clipRule="evenodd"
                />
              </svg>
              {Math.abs(change).toFixed(1)}%
            </span>
          )}
          {isNegativeChange && (
            <span className="flex items-center text-sm text-rose-400">
              <svg className="w-4 h-4 mr-0.5" fill="currentColor" viewBox="0 0 20 20">
                <path
                  fillRule="evenodd"
                  d="M14.707 10.293a1 1 0 010 1.414l-4 4a1 1 0 01-1.414 0l-4-4a1 1 0 111.414-1.414L9 12.586V5a1 1 0 012 0v7.586l2.293-2.293a1 1 0 011.414 0z"
                  clipRule="evenodd"
                />
              </svg>
              {Math.abs(change).toFixed(1)}%
            </span>
          )}
          {change === 0 && (
            <span className="flex items-center text-sm text-slate-500">
              <svg className="w-4 h-4 mr-0.5" fill="currentColor" viewBox="0 0 20 20">
                <path fillRule="evenodd" d="M5 10a1 1 0 011-1h8a1 1 0 110 2H6a1 1 0 01-1-1z" clipRule="evenodd" />
              </svg>
              0%
            </span>
          )}
          <span className="text-sm text-slate-600">{changeLabel}</span>
        </motion.div>
      )}
    </motion.div>
  )
}
