import { NavLink } from 'react-router-dom'
import { motion } from 'framer-motion'
import clsx from 'clsx'
import { useTheme } from '../../context/ThemeContext'

const navigation = [
  {
    name: 'Riskboard',
    href: '/riskboard',
    icon: (
      <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M4 6a2 2 0 012-2h2a2 2 0 012 2v2a2 2 0 01-2 2H6a2 2 0 01-2-2V6zM14 6a2 2 0 012-2h2a2 2 0 012 2v2a2 2 0 01-2 2h-2a2 2 0 01-2-2V6zM4 16a2 2 0 012-2h2a2 2 0 012 2v2a2 2 0 01-2 2H6a2 2 0 01-2-2v-2zM14 16a2 2 0 012-2h2a2 2 0 012 2v2a2 2 0 01-2 2h-2a2 2 0 01-2-2v-2z" />
      </svg>
    ),
  },
  {
    name: 'Trades',
    href: '/trades',
    icon: (
      <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2m-3 7h3m-3 4h3m-6-4h.01M9 16h.01" />
      </svg>
    ),
  },
  {
    name: 'CIO View',
    href: '/cio',
    icon: (
      <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />
      </svg>
    ),
  },
  {
    name: 'Dashboard',
    href: '/dashboard',
    icon: (
      <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M3 12l2-2m0 0l7-7 7 7M5 10v10a1 1 0 001 1h3m10-11l2 2m-2-2v10a1 1 0 01-1 1h-3m-6 0a1 1 0 001-1v-4a1 1 0 011-1h2a1 1 0 011 1v4a1 1 0 001 1m-6 0h6" />
      </svg>
    ),
  },
  {
    name: 'Overlaps',
    href: '/overlaps',
    icon: (
      <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M8 7h12m0 0l-4-4m4 4l-4 4m0 6H4m0 0l4 4m-4-4l4-4" />
      </svg>
    ),
  },
  {
    name: 'Correlation',
    href: '/correlation',
    icon: (
      <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M7 12l3-3 3 3 4-4M8 21l4-4 4 4M3 4h18M4 4h16v12a1 1 0 01-1 1H5a1 1 0 01-1-1V4z" />
      </svg>
    ),
  },
  {
    name: 'Upload',
    href: '/upload',
    icon: (
      <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M15 13l-3-3m0 0l-3 3m3-3v12" />
      </svg>
    ),
  },
]

export default function Sidebar() {
  const { isDarkMode } = useTheme()

  return (
    <aside className={clsx(
      'w-64 flex flex-col rounded-none border-r transition-colors duration-200',
      isDarkMode ? 'glass border-white/5' : 'bg-[#ECECEC] border-[#CCCCCC]'
    )}>
      {/* Logo */}
      <div className={clsx(
        'h-16 flex items-center px-6 border-b transition-colors duration-200',
        isDarkMode ? 'border-white/5' : 'border-[#CCCCCC]'
      )}>
        <motion.div
          initial={{ opacity: 0, x: -10 }}
          animate={{ opacity: 1, x: 0 }}
        >
          <span className="text-xl font-bold" style={{ color: '#22C55E' }}>RISKCORE</span>
        </motion.div>
      </div>

      {/* Navigation */}
      <nav className="flex-1 px-3 py-4 space-y-1">
        {navigation.map((item, index) => (
          <motion.div
            key={item.name}
            initial={{ opacity: 0, x: -20 }}
            animate={{ opacity: 1, x: 0 }}
            transition={{ delay: index * 0.05 }}
          >
            <NavLink
              to={item.href}
              className={({ isActive }) =>
                clsx(
                  'flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm font-medium transition-all duration-200',
                  isActive
                    ? isDarkMode
                      ? 'bg-white/10 text-white'
                      : 'bg-[#D9D9D9] text-slate-900'
                    : isDarkMode
                      ? 'text-slate-300 hover:bg-white/5 hover:text-white'
                      : 'text-slate-600 hover:bg-[#D9D9D9] hover:text-slate-900'
                )
              }
            >
              <span className={isDarkMode ? 'text-slate-400' : 'text-slate-500'}>{item.icon}</span>
              <span>{item.name}</span>
            </NavLink>
          </motion.div>
        ))}
      </nav>

      {/* Command palette hint */}
      <div className={clsx(
        'px-4 py-3 border-t transition-colors duration-200',
        isDarkMode ? 'border-white/5' : 'border-[#CCCCCC]'
      )}>
        <div className={clsx(
          'flex items-center justify-between text-xs',
          isDarkMode ? 'text-slate-500' : 'text-slate-500'
        )}>
          <span>Quick search</span>
          <kbd className={clsx(
            'px-2 py-1 rounded font-mono transition-colors duration-200',
            isDarkMode ? 'bg-white/5 text-slate-400' : 'bg-[#D9D9D9] text-slate-600'
          )}>
            Ctrl K
          </kbd>
        </div>
      </div>

      {/* Footer */}
      <div className={clsx(
        'px-4 py-4 border-t transition-colors duration-200',
        isDarkMode ? 'border-white/5' : 'border-[#CCCCCC]'
      )}>
        <div className="text-xs">
          <div className={clsx(
            'font-medium',
            isDarkMode ? 'text-slate-400' : 'text-slate-600'
          )}>RISKCORE v0.1.0</div>
          <div className={clsx(
            'mt-0.5',
            isDarkMode ? 'text-slate-500' : 'text-slate-500'
          )}>Risk Aggregation Platform</div>
        </div>
      </div>
    </aside>
  )
}
