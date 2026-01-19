import { useState } from 'react'
import { NavLink, useLocation } from 'react-router-dom'
import { motion, AnimatePresence } from 'framer-motion'
import clsx from 'clsx'
import { useTheme } from '../../context/ThemeContext'

// Navigation sections
const dashboardNav = [
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
    name: 'Positions & Trades',
    href: '/trades',
    icon: (
      <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2m-3 7h3m-3 4h3m-6-4h.01M9 16h.01" />
      </svg>
    ),
  },
]

const analysisNav = [
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
    name: 'Reports',
    href: '/reports',
    icon: (
      <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
      </svg>
    ),
  },
]

const importSubmenu = [
  { name: 'Upload Trades', href: '/upload?mode=trades' },
  { name: 'Portfolio Snapshot', href: '/upload?mode=portfolio' },
  { name: 'Position Updates', href: '/upload?mode=delta' },
  { name: 'Google Sheet', href: '/upload?mode=google' },
  { name: 'FIX Message', href: '/upload?mode=fix' },
]

const systemNav = [
  {
    name: 'Settings',
    href: '/settings',
    icon: (
      <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M10.325 4.317c.426-1.756 2.924-1.756 3.35 0a1.724 1.724 0 002.573 1.066c1.543-.94 3.31.826 2.37 2.37a1.724 1.724 0 001.065 2.572c1.756.426 1.756 2.924 0 3.35a1.724 1.724 0 00-1.066 2.573c.94 1.543-.826 3.31-2.37 2.37a1.724 1.724 0 00-2.572 1.065c-.426 1.756-2.924 1.756-3.35 0a1.724 1.724 0 00-2.573-1.066c-1.543.94-3.31-.826-2.37-2.37a1.724 1.724 0 00-1.065-2.572c-1.756-.426-1.756-2.924 0-3.35a1.724 1.724 0 001.066-2.573c-.94-1.543.826-3.31 2.37-2.37.996.608 2.296.07 2.572-1.065z" />
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
      </svg>
    ),
  },
  {
    name: 'Help',
    href: '/help',
    icon: (
      <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M8.228 9c.549-1.165 2.03-2 3.772-2 2.21 0 4 1.343 4 3 0 1.4-1.278 2.575-3.006 2.907-.542.104-.994.54-.994 1.093m0 3h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
      </svg>
    ),
  },
]

// Nav Item Component
function NavItem({ item, index }: { item: typeof dashboardNav[0]; index: number }) {
  const { isDarkMode } = useTheme()

  return (
    <motion.div
      initial={{ opacity: 0, x: -20 }}
      animate={{ opacity: 1, x: 0 }}
      transition={{ delay: index * 0.03 }}
    >
      <NavLink
        to={item.href}
        className={({ isActive }) =>
          clsx(
            'group relative flex items-center gap-3 px-3 py-2 rounded-md text-[13px] font-medium transition-all duration-200',
            isActive
              ? isDarkMode
                ? 'bg-emerald-500/15 text-emerald-400'
                : 'bg-emerald-100 text-emerald-700'
              : isDarkMode
                ? 'text-slate-400 hover:bg-white/5 hover:text-slate-200'
                : 'text-slate-600 hover:bg-slate-200 hover:text-slate-900'
          )
        }
      >
        {({ isActive }) => (
          <>
            {/* Active indicator bar */}
            {isActive && (
              <motion.div
                layoutId="activeIndicator"
                className={clsx(
                  'absolute left-0 top-1/2 -translate-y-1/2 w-[3px] h-5 rounded-r-full',
                  isDarkMode ? 'bg-emerald-400' : 'bg-emerald-600'
                )}
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                transition={{ duration: 0.2 }}
              />
            )}
            <span className={clsx(
              'transition-colors',
              isActive
                ? isDarkMode ? 'text-emerald-400' : 'text-emerald-600'
                : isDarkMode ? 'text-slate-500 group-hover:text-slate-300' : 'text-slate-500 group-hover:text-slate-700'
            )}>
              {item.icon}
            </span>
            <span>{item.name}</span>
          </>
        )}
      </NavLink>
    </motion.div>
  )
}

// Section Title Component
function SectionTitle({ children }: { children: React.ReactNode }) {
  const { isDarkMode } = useTheme()

  return (
    <div className={clsx(
      'text-[10px] font-semibold uppercase tracking-wider px-3 py-2',
      isDarkMode ? 'text-slate-600' : 'text-slate-500'
    )}>
      {children}
    </div>
  )
}

export default function Sidebar() {
  const { isDarkMode } = useTheme()
  const location = useLocation()
  const [importExpanded, setImportExpanded] = useState(false)
  const pendingCount = 3 // TODO: Get from context/state

  // Check if current page is upload/import related
  const isImportActive = location.pathname.startsWith('/upload')

  return (
    <aside className={clsx(
      'w-[200px] flex flex-col h-screen border-r transition-colors duration-200',
      isDarkMode
        ? 'bg-slate-950/95 border-white/10'
        : 'bg-slate-100 border-slate-300'
    )}>
      {/* Logo */}
      <div className={clsx(
        'h-14 flex items-center px-4 border-b transition-colors duration-200',
        isDarkMode ? 'border-white/10' : 'border-slate-300'
      )}>
        <motion.h1
          initial={{ opacity: 0, x: -10 }}
          animate={{ opacity: 1, x: 0 }}
          className="text-xl font-extrabold tracking-wider"
          style={{
            background: 'linear-gradient(135deg, #3CD574, #22c55e)',
            WebkitBackgroundClip: 'text',
            WebkitTextFillColor: 'transparent',
          }}
        >
          RISKCORE
        </motion.h1>
      </div>

      {/* Main Navigation */}
      <nav className="flex-1 overflow-y-auto py-3 px-2">
        {/* Dashboard Section */}
        <div className="mb-4">
          <SectionTitle>Dashboard</SectionTitle>
          <div className="space-y-0.5">
            {dashboardNav.map((item, index) => (
              <NavItem key={item.name} item={item} index={index} />
            ))}
          </div>
        </div>

        {/* Analysis Section */}
        <div className="mb-4">
          <SectionTitle>Analysis</SectionTitle>
          <div className="space-y-0.5">
            {analysisNav.map((item, index) => (
              <NavItem key={item.name} item={item} index={index + dashboardNav.length} />
            ))}
          </div>
        </div>
      </nav>

      {/* Bottom Section - Import & System */}
      <div className={clsx(
        'border-t py-3 px-2',
        isDarkMode ? 'border-white/10' : 'border-slate-300'
      )}>
        {/* Data Section */}
        <div className="mb-3">
          <SectionTitle>Data</SectionTitle>

          {/* Import Data with submenu */}
          <div>
            <button
              onClick={() => setImportExpanded(!importExpanded)}
              className={clsx(
                'w-full group relative flex items-center justify-between px-3 py-2 rounded-md text-[13px] font-medium transition-all duration-200',
                isImportActive
                  ? isDarkMode
                    ? 'bg-emerald-500/15 text-emerald-400'
                    : 'bg-emerald-100 text-emerald-700'
                  : isDarkMode
                    ? 'text-slate-400 hover:bg-white/5 hover:text-slate-200'
                    : 'text-slate-600 hover:bg-slate-200 hover:text-slate-900'
              )}
            >
              <div className="flex items-center gap-3">
                {/* Active indicator */}
                {isImportActive && (
                  <div className={clsx(
                    'absolute left-0 top-1/2 -translate-y-1/2 w-[3px] h-5 rounded-r-full',
                    isDarkMode ? 'bg-emerald-400' : 'bg-emerald-600'
                  )} />
                )}
                <svg className={clsx(
                  'w-5 h-5 transition-colors',
                  isImportActive
                    ? isDarkMode ? 'text-emerald-400' : 'text-emerald-600'
                    : isDarkMode ? 'text-slate-500 group-hover:text-slate-300' : 'text-slate-500 group-hover:text-slate-700'
                )} fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M15 13l-3-3m0 0l-3 3m3-3v12" />
                </svg>
                <span>Import Data</span>
              </div>
              <div className="flex items-center gap-2">
                {pendingCount > 0 && (
                  <span className="px-1.5 py-0.5 text-[10px] font-bold rounded-full bg-amber-500 text-slate-900">
                    {pendingCount}
                  </span>
                )}
                <svg
                  className={clsx(
                    'w-4 h-4 transition-transform duration-200',
                    importExpanded && 'rotate-180',
                    isDarkMode ? 'text-slate-500' : 'text-slate-400'
                  )}
                  fill="none"
                  viewBox="0 0 24 24"
                  stroke="currentColor"
                >
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
                </svg>
              </div>
            </button>

            {/* Submenu */}
            <AnimatePresence>
              {importExpanded && (
                <motion.div
                  initial={{ height: 0, opacity: 0 }}
                  animate={{ height: 'auto', opacity: 1 }}
                  exit={{ height: 0, opacity: 0 }}
                  transition={{ duration: 0.2 }}
                  className="overflow-hidden"
                >
                  <div className="pl-8 py-1 space-y-0.5">
                    {importSubmenu.map((item) => (
                      <NavLink
                        key={item.name}
                        to={item.href}
                        className={clsx(
                          'block px-3 py-1.5 rounded text-[12px] transition-colors',
                          isDarkMode
                            ? 'text-slate-500 hover:text-slate-300 hover:bg-white/5'
                            : 'text-slate-500 hover:text-slate-700 hover:bg-slate-200'
                        )}
                      >
                        {item.name}
                      </NavLink>
                    ))}
                    {pendingCount > 0 && (
                      <NavLink
                        to="/upload?pending=true"
                        className={clsx(
                          'block px-3 py-1.5 rounded text-[12px] transition-colors',
                          isDarkMode
                            ? 'text-amber-400 hover:bg-amber-500/10'
                            : 'text-amber-600 hover:bg-amber-100'
                        )}
                      >
                        Pending ({pendingCount})
                      </NavLink>
                    )}
                  </div>
                </motion.div>
              )}
            </AnimatePresence>
          </div>
        </div>

        {/* System Section */}
        <div>
          <SectionTitle>System</SectionTitle>
          <div className="space-y-0.5">
            {systemNav.map((item, index) => (
              <NavItem key={item.name} item={item} index={index} />
            ))}
          </div>
        </div>
      </div>

      {/* Footer */}
      <div className={clsx(
        'px-4 py-3 border-t text-[10px]',
        isDarkMode ? 'border-white/10 text-slate-600' : 'border-slate-300 text-slate-500'
      )}>
        Powered by RISKCORE
      </div>
    </aside>
  )
}
