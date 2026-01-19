import { useState } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import clsx from 'clsx'
import { useTheme } from '../../context/ThemeContext'

export default function Header() {
  const [isDropdownOpen, setIsDropdownOpen] = useState(false)
  const { isDarkMode, toggleTheme } = useTheme()

  return (
    <header className={clsx(
      'h-16 border-b flex items-center justify-between px-6 transition-colors duration-200',
      isDarkMode
        ? 'border-white/5 bg-white/5 backdrop-blur-sm'
        : 'border-[#CCCCCC] bg-[#ECECEC]'
    )}>
      {/* Left side - Search bar */}
      <div className="flex items-center gap-4 flex-1">
        <div className="relative max-w-md flex-1">
          <svg
            className={clsx(
              'absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4',
              isDarkMode ? 'text-slate-500' : 'text-slate-400'
            )}
            fill="none"
            viewBox="0 0 24 24"
            stroke="currentColor"
          >
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              strokeWidth={1.5}
              d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z"
            />
          </svg>
          <input
            type="text"
            placeholder="Search positions, PMs, securities..."
            className={clsx(
              'w-full pl-10 pr-4 py-2 rounded-xl text-sm transition-all duration-200',
              'focus:outline-none focus:ring-1',
              isDarkMode
                ? 'bg-white/5 border border-white/10 text-slate-300 placeholder:text-slate-500 focus:border-primary-500/50 focus:ring-primary-500/20'
                : 'bg-[#D9D9D9] border border-[#CCCCCC] text-slate-700 placeholder:text-slate-500 focus:border-blue-400 focus:ring-blue-200'
            )}
          />
        </div>
      </div>

      {/* Right side - actions */}
      <div className="flex items-center gap-3">
        {/* Theme Toggle - Multicolor Circle */}
        <div className="flex items-center gap-2">
          <span className={clsx(
            'text-[11px] uppercase tracking-wide',
            isDarkMode ? 'text-slate-500' : 'text-slate-500'
          )}>
            {isDarkMode ? 'Dark' : 'Light'}
          </span>
          <label
            className="relative w-14 h-7 cursor-pointer"
            title={isDarkMode ? 'Switch to light mode' : 'Switch to dark mode'}
          >
            <input
              type="checkbox"
              checked={!isDarkMode}
              onChange={toggleTheme}
              className="sr-only"
            />
            <div className={clsx(
              'absolute inset-0 rounded-full border transition-all duration-300',
              isDarkMode
                ? 'bg-slate-700/80 border-white/15'
                : 'bg-slate-400/30 border-slate-300'
            )}>
              <div
                className={clsx(
                  'absolute top-[2px] w-[22px] h-[22px] rounded-full transition-all duration-300',
                  !isDarkMode && 'translate-x-7'
                )}
                style={{
                  left: '2px',
                  background: isDarkMode
                    ? 'conic-gradient(#ef4444 0deg 60deg, #f97316 60deg 120deg, #22c55e 120deg 180deg, #06b6d4 180deg 240deg, #3b82f6 240deg 300deg, #a855f7 300deg 360deg)'
                    : '#475569',
                  boxShadow: !isDarkMode ? '0 0 8px rgba(71, 85, 105, 0.5)' : 'none'
                }}
              />
            </div>
          </label>
        </div>

        {/* Notifications */}
        <button
          className={clsx(
            'relative p-2 rounded-xl transition-all duration-200',
            isDarkMode
              ? 'text-slate-400 hover:text-slate-100 hover:bg-white/5'
              : 'text-slate-600 hover:text-slate-800 hover:bg-[#D9D9D9]'
          )}
          title="Notifications"
        >
          <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              strokeWidth={1.5}
              d="M15 17h5l-1.405-1.405A2.032 2.032 0 0118 14.158V11a6.002 6.002 0 00-4-5.659V5a2 2 0 10-4 0v.341C7.67 6.165 6 8.388 6 11v3.159c0 .538-.214 1.055-.595 1.436L4 17h5m6 0v1a3 3 0 11-6 0v-1m6 0H9"
            />
          </svg>
          {/* Notification badge */}
          <span className="absolute top-1.5 right-1.5 w-2 h-2 bg-rose-500 rounded-full" />
        </button>

        {/* Refresh button */}
        <button
          className={clsx(
            'p-2 rounded-xl transition-all duration-200',
            isDarkMode
              ? 'text-slate-400 hover:text-slate-100 hover:bg-white/5'
              : 'text-slate-600 hover:text-slate-800 hover:bg-[#D9D9D9]'
          )}
          title="Refresh data"
        >
          <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              strokeWidth={1.5}
              d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15"
            />
          </svg>
        </button>

        {/* Separator */}
        <div className={clsx(
          'w-px h-6',
          isDarkMode ? 'bg-white/10' : 'bg-slate-200'
        )} />

        {/* Time indicator */}
        <div className={clsx(
          'text-sm',
          isDarkMode ? 'text-slate-500' : 'text-slate-500'
        )}>
          <span className={clsx(
            'font-medium',
            isDarkMode ? 'text-slate-400' : 'text-slate-600'
          )}>Live</span>
          <span className="ml-1.5 inline-flex items-center">
            <span className="w-1.5 h-1.5 bg-emerald-500 rounded-full animate-pulse mr-1" />
          </span>
        </div>

        {/* User menu */}
        <div className="relative">
          <button
            onClick={() => setIsDropdownOpen(!isDropdownOpen)}
            className={clsx(
              'flex items-center gap-2 p-1.5 rounded-xl transition-all duration-200',
              isDarkMode ? 'hover:bg-white/5' : 'hover:bg-slate-100'
            )}
          >
            <div className="w-8 h-8 bg-gradient-to-br from-blue-500 to-cyan-500 text-white rounded-lg flex items-center justify-center text-xs font-semibold">
              CRO
            </div>
            <svg
              className={clsx(
                'w-4 h-4',
                isDarkMode ? 'text-slate-500' : 'text-slate-400'
              )}
              fill="none"
              viewBox="0 0 24 24"
              stroke="currentColor"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M19 9l-7 7-7-7"
              />
            </svg>
          </button>

          {/* Dropdown menu */}
          <AnimatePresence>
            {isDropdownOpen && (
              <motion.div
                initial={{ opacity: 0, y: -10, scale: 0.95 }}
                animate={{ opacity: 1, y: 0, scale: 1 }}
                exit={{ opacity: 0, y: -10, scale: 0.95 }}
                transition={{ duration: 0.15 }}
                className={clsx(
                  'absolute right-0 mt-2 w-56 rounded-xl py-1 z-50 shadow-lg',
                  isDarkMode ? 'glass' : 'bg-[#ECECEC] border border-[#CCCCCC]'
                )}
              >
                <div className={clsx(
                  'px-4 py-3 border-b',
                  isDarkMode ? 'border-white/5' : 'border-slate-100'
                )}>
                  <div className={clsx(
                    'text-sm font-medium',
                    isDarkMode ? 'text-slate-100' : 'text-slate-800'
                  )}>Chief Risk Officer</div>
                  <div className={clsx(
                    'text-xs',
                    isDarkMode ? 'text-slate-500' : 'text-slate-500'
                  )}>cro@hedgefund.com</div>
                </div>
                <div className="py-1">
                  <button className={clsx(
                    'w-full text-left px-4 py-2 text-sm transition-colors',
                    isDarkMode
                      ? 'text-slate-300 hover:bg-white/5 hover:text-slate-100'
                      : 'text-slate-600 hover:bg-slate-50 hover:text-slate-900'
                  )}>
                    <span className="flex items-center gap-2">
                      <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M10.325 4.317c.426-1.756 2.924-1.756 3.35 0a1.724 1.724 0 002.573 1.066c1.543-.94 3.31.826 2.37 2.37a1.724 1.724 0 001.065 2.572c1.756.426 1.756 2.924 0 3.35a1.724 1.724 0 00-1.066 2.573c.94 1.543-.826 3.31-2.37 2.37a1.724 1.724 0 00-2.572 1.065c-.426 1.756-2.924 1.756-3.35 0a1.724 1.724 0 00-2.573-1.066c-1.543.94-3.31-.826-2.37-2.37a1.724 1.724 0 00-1.065-2.572c-1.756-.426-1.756-2.924 0-3.35a1.724 1.724 0 001.066-2.573c-.94-1.543.826-3.31 2.37-2.37.996.608 2.296.07 2.572-1.065z" />
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
                      </svg>
                      Settings
                    </span>
                  </button>
                  <button className={clsx(
                    'w-full text-left px-4 py-2 text-sm transition-colors',
                    isDarkMode
                      ? 'text-slate-300 hover:bg-white/5 hover:text-slate-100'
                      : 'text-slate-600 hover:bg-slate-50 hover:text-slate-900'
                  )}>
                    <span className="flex items-center gap-2">
                      <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M8.228 9c.549-1.165 2.03-2 3.772-2 2.21 0 4 1.343 4 3 0 1.4-1.278 2.575-3.006 2.907-.542.104-.994.54-.994 1.093m0 3h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                      </svg>
                      Help & Support
                    </span>
                  </button>
                </div>
                <div className={clsx(
                  'border-t py-1',
                  isDarkMode ? 'border-white/5' : 'border-slate-100'
                )}>
                  <button className={clsx(
                    'w-full text-left px-4 py-2 text-sm transition-colors',
                    isDarkMode
                      ? 'text-rose-400 hover:bg-white/5 hover:text-rose-300'
                      : 'text-rose-500 hover:bg-slate-50 hover:text-rose-600'
                  )}>
                    <span className="flex items-center gap-2">
                      <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M17 16l4-4m0 0l-4-4m4 4H7m6 4v1a3 3 0 01-3 3H6a3 3 0 01-3-3V7a3 3 0 013-3h4a3 3 0 013 3v1" />
                      </svg>
                      Sign out
                    </span>
                  </button>
                </div>
              </motion.div>
            )}
          </AnimatePresence>
        </div>
      </div>
    </header>
  )
}
