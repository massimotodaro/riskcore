import type {
  FirmSummary,
  NettingSummary,
  OverlapSummary,
  Overlap,
  CorrelationMatrix,
  CorrelationPair,
  HierarchyNode,
  ExposureBreakdown,
  AssetClassRisk,
  Book,
  OverlayBook,
  TradeDetail,
  ValuationDetail,
  BookCorrelation,
} from '../types'

const API_BASE = '/api/v1'

// Default tenant ID for development (from mock data)
// In production, this would come from auth context
const DEFAULT_TENANT_ID = '550e8400-e29b-41d4-a716-446655440000'

async function fetchApi<T>(endpoint: string, options?: RequestInit): Promise<T> {
  const url = `${API_BASE}${endpoint}`

  const response = await fetch(url, {
    ...options,
    headers: {
      'Content-Type': 'application/json',
      ...options?.headers,
    },
  })

  if (!response.ok) {
    const error = await response.json().catch(() => ({ detail: 'Unknown error' }))
    throw new Error(error.detail || `HTTP ${response.status}`)
  }

  return response.json()
}

// Aggregation API
export const aggregationApi = {
  getFirmSummary: (tenantId: string = DEFAULT_TENANT_ID) =>
    fetchApi<FirmSummary>(`/aggregation/firm/summary?tenant_id=${tenantId}`),

  getFirmHierarchy: (tenantId: string = DEFAULT_TENANT_ID) =>
    fetchApi<HierarchyNode>(`/aggregation/firm/hierarchy?tenant_id=${tenantId}`),

  getNettingSummary: (tenantId: string = DEFAULT_TENANT_ID) =>
    fetchApi<NettingSummary>(`/aggregation/netting/summary?tenant_id=${tenantId}`),

  getOverlapsSummary: (tenantId: string = DEFAULT_TENANT_ID) =>
    fetchApi<OverlapSummary>(`/aggregation/overlaps/summary?tenant_id=${tenantId}`),

  getOverlapsBySecurity: (tenantId: string = DEFAULT_TENANT_ID, severity?: string) => {
    let url = `/aggregation/overlaps?tenant_id=${tenantId}`
    if (severity) url += `&severity=${severity}`
    return fetchApi<Overlap[]>(url)
  },
}

// Correlation API
export const correlationApi = {
  getMatrix: (tenantId: string = DEFAULT_TENANT_ID, window: string = '21d') =>
    fetchApi<CorrelationMatrix>(`/correlation/pm/matrix?tenant_id=${tenantId}&window=${window}`),

  getConcerns: (tenantId: string = DEFAULT_TENANT_ID, threshold: number = 0.7, window: string = '21d') =>
    fetchApi<CorrelationPair[]>(`/correlation/pm/high-correlations?tenant_id=${tenantId}&threshold=${threshold}&window=${window}`),

  getPairCorrelation: (pm1Id: string, pm2Id: string, window: string = '21d') =>
    fetchApi<CorrelationPair>(`/correlation/pm/${pm1Id}/correlation/${pm2Id}?window=${window}`),
}

// Risk API
export const riskApi = {
  getExposures: (bookId: string, dimension: string = 'sector') =>
    fetchApi<ExposureBreakdown>(`/risk/exposures/${bookId}?dimension=${dimension}`),

  getConcentration: (bookId: string) =>
    fetchApi<{ hhi: number; top_10_pct: number; max_single_pct: number }>(
      `/risk/exposures/${bookId}/concentration`
    ),
}

// Positions API
export const positionsApi = {
  list: (params: {
    tenant_id?: string
    book_id?: string
    page?: number
    page_size?: number
  }) => {
    const searchParams = new URLSearchParams()
    Object.entries(params).forEach(([key, value]) => {
      if (value !== undefined) searchParams.set(key, String(value))
    })
    return fetchApi<{ positions: Position[]; total: number; page: number; page_size: number }>(
      `/positions?${searchParams}`
    )
  },
}

// Utility function to format currency
export function formatCurrency(value: number): string {
  const absValue = Math.abs(value)
  if (absValue >= 1_000_000_000) {
    return `$${(value / 1_000_000_000).toFixed(2)}B`
  }
  if (absValue >= 1_000_000) {
    return `$${(value / 1_000_000).toFixed(1)}M`
  }
  if (absValue >= 1_000) {
    return `$${(value / 1_000).toFixed(0)}K`
  }
  return `$${value.toFixed(0)}`
}

// Utility function to format percentage
export function formatPercent(value: number): string {
  return `${(value * 100).toFixed(1)}%`
}

// Utility function to format correlation
export function formatCorrelation(value: number): string {
  return value.toFixed(2)
}

// Position type for the positions API
interface Position {
  id: string
  book_id: string
  ticker: string
  quantity: number
  current_price: number
  market_value: number
}

// ============================================
// CIO Dashboard API
// ============================================

// Risk by Asset Class API (for RiskPod cards)
export const riskByAssetClassApi = {
  // Get firm-wide risk by asset class (Row 1: Firm-Wide)
  getFirmRisk: (tenantId: string = DEFAULT_TENANT_ID) =>
    fetchApi<AssetClassRisk[]>(`/aggregation/risk/by-asset-class?tenant_id=${tenantId}`),

  // Get single book risk by asset class (Rows 3-4: Portfolio comparison)
  getBookRisk: (bookId: string) =>
    fetchApi<AssetClassRisk[]>(`/aggregation/risk/by-asset-class/${bookId}`),

  // Get overlay risk by asset class (Row 2: Overlay Portfolio)
  getOverlayRisk: (tenantId: string = DEFAULT_TENANT_ID) =>
    fetchApi<AssetClassRisk[]>(`/aggregation/risk/overlay?tenant_id=${tenantId}`),
}

// Books API
export const booksApi = {
  // Get all books for portfolio selector
  getAll: (tenantId: string = DEFAULT_TENANT_ID, bookType?: 'trading' | 'overlay') => {
    let url = `/aggregation/books?tenant_id=${tenantId}`
    if (bookType) url += `&book_type=${bookType}`
    return fetchApi<Book[]>(url)
  },

  // Get trading books only
  getTradingBooks: (tenantId: string = DEFAULT_TENANT_ID) =>
    fetchApi<Book[]>(`/aggregation/books?tenant_id=${tenantId}&book_type=trading`),

  // Get overlay books with source book links
  getOverlayBooks: (tenantId: string = DEFAULT_TENANT_ID) =>
    fetchApi<OverlayBook[]>(`/aggregation/books/overlay?tenant_id=${tenantId}`),
}

// Book Correlation API (Row 5: Portfolio comparison)
export const bookCorrelationApi = {
  // Get correlation between two books
  getCorrelation: (book1Id: string, book2Id: string, tenantId: string = DEFAULT_TENANT_ID) =>
    fetchApi<BookCorrelation>(`/correlation/books/${book1Id}/${book2Id}?tenant_id=${tenantId}`),
}

// Trades API (for underlying trades drill-down)
export const tradesApi = {
  // Get trades for a book, optionally filtered by asset class
  getByBook: (bookId: string, assetClass?: string, page: number = 1, pageSize: number = 50) => {
    let url = `/trades?book_id=${bookId}&page=${page}&page_size=${pageSize}`
    if (assetClass) url += `&asset_class=${assetClass}`
    return fetchApi<{ trades: TradeDetail[]; total: number; page: number; page_size: number }>(url)
  },

  // Get trades by security
  getBySecurity: (securityId: string, tenantId: string = DEFAULT_TENANT_ID) =>
    fetchApi<TradeDetail[]>(`/trades/security/${securityId}?tenant_id=${tenantId}`),
}

// Valuation API (for valuation transparency)
export const valuationApi = {
  // Get valuation details for a position
  getPositionValuation: (positionId: string) =>
    fetchApi<ValuationDetail>(`/positions/${positionId}/valuation`),

  // Override model inputs
  overrideModelInputs: (positionId: string, inputs: Record<string, number>, reason: string) =>
    fetchApi<ValuationDetail>(`/positions/${positionId}/valuation/override`, {
      method: 'PUT',
      body: JSON.stringify({ inputs, reason }),
    }),
}

// Utility: Get primary risk metric display
export function getPrimaryRiskMetricDisplay(assetClass: string): { label: string; unit: string } {
  const displays: Record<string, { label: string; unit: string }> = {
    equity: { label: 'Delta', unit: '' },
    option: { label: 'Delta', unit: '' },
    fixed_income: { label: 'DV01', unit: '' },
    swap: { label: 'DV01', unit: '' },
    cds: { label: 'CS01', unit: '' },
    fx: { label: 'Delta', unit: '' },
    future: { label: 'Delta', unit: '' },
  }
  return displays[assetClass] || { label: 'Net Exp', unit: '' }
}

// Utility: Format risk metric value with appropriate scale
export function formatRiskMetric(value: number, metric: string): string {
  const absValue = Math.abs(value)

  if (metric === 'dv01' || metric === 'cs01') {
    // DV01/CS01 typically in thousands
    if (absValue >= 1_000_000) {
      return `${(value / 1_000_000).toFixed(2)}M`
    }
    if (absValue >= 1_000) {
      return `${(value / 1_000).toFixed(1)}K`
    }
    return value.toFixed(0)
  }

  // Delta, gamma, vega - show as-is or scaled
  if (absValue >= 1_000_000) {
    return `${(value / 1_000_000).toFixed(2)}M`
  }
  if (absValue >= 1_000) {
    return `${(value / 1_000).toFixed(1)}K`
  }
  if (absValue >= 1) {
    return value.toFixed(0)
  }
  return value.toFixed(4)
}
