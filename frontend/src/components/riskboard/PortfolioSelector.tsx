import { useState, useRef, useEffect } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import clsx from 'clsx'
import type { Book } from '../../types'

interface PortfolioSelectorProps {
  books: Book[]
  selectedBook: Book | null
  onSelect: (book: Book) => void
  label?: string
  placeholder?: string
  disabled?: boolean
  excludeBookIds?: string[]
  className?: string
}

export default function PortfolioSelector({
  books,
  selectedBook,
  onSelect,
  label = 'Portfolio',
  placeholder = 'Select a portfolio...',
  disabled = false,
  excludeBookIds = [],
  className,
}: PortfolioSelectorProps) {
  const [isOpen, setIsOpen] = useState(false)
  const [searchQuery, setSearchQuery] = useState('')
  const containerRef = useRef<HTMLDivElement>(null)
  const inputRef = useRef<HTMLInputElement>(null)

  // Filter books based on search and exclusions
  const filteredBooks = books.filter((book) => {
    // Exclude specified books
    if (excludeBookIds.includes(book.book_id)) return false

    // Filter by search query
    if (searchQuery) {
      const query = searchQuery.toLowerCase()
      return (
        book.name.toLowerCase().includes(query) ||
        book.pm_name?.toLowerCase().includes(query) ||
        book.strategy?.toLowerCase().includes(query)
      )
    }
    return true
  })

  // Group books by fund
  const groupedBooks = filteredBooks.reduce<Record<string, Book[]>>((acc, book) => {
    const fund = book.fund_name || 'Other'
    if (!acc[fund]) acc[fund] = []
    acc[fund].push(book)
    return acc
  }, {})

  // Close dropdown when clicking outside
  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (containerRef.current && !containerRef.current.contains(event.target as Node)) {
        setIsOpen(false)
        setSearchQuery('')
      }
    }
    document.addEventListener('mousedown', handleClickOutside)
    return () => document.removeEventListener('mousedown', handleClickOutside)
  }, [])

  // Focus search input when opening
  useEffect(() => {
    if (isOpen && inputRef.current) {
      inputRef.current.focus()
    }
  }, [isOpen])

  const handleSelect = (book: Book) => {
    onSelect(book)
    setIsOpen(false)
    setSearchQuery('')
  }

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Escape') {
      setIsOpen(false)
      setSearchQuery('')
    }
  }

  // Book type badge colors
  const bookTypeBadge = (type: string) => {
    switch (type) {
      case 'overlay':
        return 'bg-purple-500/20 text-purple-400 border-purple-500/30'
      case 'trading':
      default:
        return 'bg-blue-500/20 text-blue-400 border-blue-500/30'
    }
  }

  return (
    <div ref={containerRef} className={clsx('relative', className)} onKeyDown={handleKeyDown}>
      {/* Label */}
      {label && (
        <label className="block text-xs text-slate-500 uppercase tracking-wider mb-1">
          {label}
        </label>
      )}

      {/* Trigger Button */}
      <button
        type="button"
        onClick={() => !disabled && setIsOpen(!isOpen)}
        disabled={disabled}
        className={clsx(
          'w-full flex items-center justify-between gap-2 px-4 py-2.5',
          'glass border border-white/10 rounded-lg',
          'text-left transition-all duration-200',
          disabled
            ? 'opacity-50 cursor-not-allowed'
            : 'hover:border-white/20 hover:bg-white/5 cursor-pointer',
          isOpen && 'border-blue-500/50 ring-1 ring-blue-500/20'
        )}
      >
        <div className="flex items-center gap-3 min-w-0">
          {selectedBook ? (
            <>
              <div className="w-8 h-8 rounded-lg bg-gradient-to-br from-blue-500/20 to-cyan-500/20 flex items-center justify-center flex-shrink-0">
                <span className="text-sm font-semibold text-blue-400">
                  {selectedBook.name.charAt(0).toUpperCase()}
                </span>
              </div>
              <div className="min-w-0">
                <p className="text-sm font-medium text-slate-100 truncate">
                  {selectedBook.name}
                </p>
                <p className="text-xs text-slate-500 truncate">
                  {selectedBook.pm_name || selectedBook.strategy || 'Trading Book'}
                </p>
              </div>
            </>
          ) : (
            <span className="text-sm text-slate-500">{placeholder}</span>
          )}
        </div>
        <svg
          className={clsx(
            'w-5 h-5 text-slate-400 transition-transform duration-200 flex-shrink-0',
            isOpen && 'rotate-180'
          )}
          fill="none"
          viewBox="0 0 24 24"
          stroke="currentColor"
        >
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
        </svg>
      </button>

      {/* Dropdown */}
      <AnimatePresence>
        {isOpen && (
          <motion.div
            initial={{ opacity: 0, y: -10 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -10 }}
            transition={{ duration: 0.15 }}
            className="absolute z-50 w-full mt-2 glass border border-white/10 rounded-lg shadow-xl overflow-hidden"
          >
            {/* Search Input */}
            <div className="p-2 border-b border-white/5">
              <div className="relative">
                <svg
                  className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-500"
                  fill="none"
                  viewBox="0 0 24 24"
                  stroke="currentColor"
                >
                  <path
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    strokeWidth={2}
                    d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z"
                  />
                </svg>
                <input
                  ref={inputRef}
                  type="text"
                  value={searchQuery}
                  onChange={(e) => setSearchQuery(e.target.value)}
                  placeholder="Search portfolios..."
                  className="w-full pl-9 pr-3 py-2 bg-slate-800/50 border border-white/5 rounded-lg
                           text-sm text-slate-100 placeholder-slate-500
                           focus:outline-none focus:border-blue-500/50 focus:ring-1 focus:ring-blue-500/20"
                />
              </div>
            </div>

            {/* Book List */}
            <div className="max-h-64 overflow-y-auto py-1">
              {Object.keys(groupedBooks).length === 0 ? (
                <div className="px-4 py-6 text-center">
                  <p className="text-sm text-slate-500">No portfolios found</p>
                </div>
              ) : (
                Object.entries(groupedBooks).map(([fundName, fundBooks]) => (
                  <div key={fundName}>
                    {/* Fund Group Header */}
                    <div className="px-3 py-1.5 text-xs font-medium text-slate-500 uppercase tracking-wider bg-slate-800/30">
                      {fundName}
                    </div>
                    {/* Books in Fund */}
                    {fundBooks.map((book) => (
                      <button
                        key={book.book_id}
                        type="button"
                        onClick={() => handleSelect(book)}
                        className={clsx(
                          'w-full flex items-center gap-3 px-3 py-2.5',
                          'text-left transition-colors duration-150',
                          selectedBook?.book_id === book.book_id
                            ? 'bg-blue-500/10 border-l-2 border-blue-500'
                            : 'hover:bg-white/5 border-l-2 border-transparent'
                        )}
                      >
                        {/* Book Initial */}
                        <div
                          className={clsx(
                            'w-8 h-8 rounded-lg flex items-center justify-center flex-shrink-0',
                            book.book_type === 'overlay'
                              ? 'bg-gradient-to-br from-purple-500/20 to-pink-500/20'
                              : 'bg-gradient-to-br from-blue-500/20 to-cyan-500/20'
                          )}
                        >
                          <span
                            className={clsx(
                              'text-sm font-semibold',
                              book.book_type === 'overlay' ? 'text-purple-400' : 'text-blue-400'
                            )}
                          >
                            {book.name.charAt(0).toUpperCase()}
                          </span>
                        </div>

                        {/* Book Info */}
                        <div className="flex-1 min-w-0">
                          <div className="flex items-center gap-2">
                            <p className="text-sm font-medium text-slate-100 truncate">
                              {book.name}
                            </p>
                            <span
                              className={clsx(
                                'px-1.5 py-0.5 text-[10px] font-medium rounded border',
                                bookTypeBadge(book.book_type)
                              )}
                            >
                              {book.book_type === 'overlay' ? 'Overlay' : 'Trading'}
                            </span>
                          </div>
                          <p className="text-xs text-slate-500 truncate">
                            {book.pm_name && `PM: ${book.pm_name}`}
                            {book.pm_name && book.strategy && ' • '}
                            {book.strategy}
                          </p>
                        </div>

                        {/* Selected Checkmark */}
                        {selectedBook?.book_id === book.book_id && (
                          <svg
                            className="w-5 h-5 text-blue-400 flex-shrink-0"
                            fill="none"
                            viewBox="0 0 24 24"
                            stroke="currentColor"
                          >
                            <path
                              strokeLinecap="round"
                              strokeLinejoin="round"
                              strokeWidth={2}
                              d="M5 13l4 4L19 7"
                            />
                          </svg>
                        )}
                      </button>
                    ))}
                  </div>
                ))
              )}
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  )
}
