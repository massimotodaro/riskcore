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

// Default tenant ID for development (from mock data generator)
// In production, this would come from auth context
const DEFAULT_TENANT_ID = 'b95fbd3b-e6f0-41f8-9c0c-5337e469cf50'

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

// ============================================
// Riskboard API (New unified dashboard)
// ============================================

export const riskboardApi = {
  // Get risk summary for top bar
  getSummary: (tenantId: string = DEFAULT_TENANT_ID, bookIds?: string[]) => {
    let url = `/riskboard/summary?tenant_id=${tenantId}`
    if (bookIds?.length) url += `&book_ids=${bookIds.join(',')}`
    return fetchApi<RiskSummary>(url)
  },

  // Get risk by asset class for selected books
  getRiskByAssetClass: (bookIds: string[]) =>
    fetchApi<AssetClassRisk[]>(`/riskboard/risk-by-asset-class?book_ids=${bookIds.join(',')}`),

  // Get all books for portfolio selector
  getBooks: (tenantId: string = DEFAULT_TENANT_ID, bookType?: 'trading' | 'overlay') => {
    let url = `/riskboard/books?tenant_id=${tenantId}`
    if (bookType) url += `&book_type=${bookType}`
    return fetchApi<Book[]>(url)
  },

  // Get position overlap for correlation panel
  getPositionOverlap: (tenantId: string = DEFAULT_TENANT_ID, bookIds?: string[]) => {
    let url = `/riskboard/position-overlap?tenant_id=${tenantId}`
    if (bookIds?.length) url += `&book_ids=${bookIds.join(',')}`
    return fetchApi<PositionOverlapItem[]>(url)
  },

  // Get sector concentration
  getConcentrationBySector: (tenantId: string = DEFAULT_TENANT_ID, bookIds?: string[]) => {
    let url = `/riskboard/concentration/sector?tenant_id=${tenantId}`
    if (bookIds?.length) url += `&book_ids=${bookIds.join(',')}`
    return fetchApi<ConcentrationItem[]>(url)
  },

  // Get security concentration
  getConcentrationBySecurity: (tenantId: string = DEFAULT_TENANT_ID, bookIds?: string[], limit: number = 20) => {
    let url = `/riskboard/concentration/security?tenant_id=${tenantId}&limit=${limit}`
    if (bookIds?.length) url += `&book_ids=${bookIds.join(',')}`
    return fetchApi<ConcentrationItem[]>(url)
  },

  // Get positions for drill-down
  getPositions: (bookIds: string[], assetClass: string, page: number = 1, pageSize: number = 50) =>
    fetchApi<PositionsResponse>(
      `/riskboard/positions?book_ids=${bookIds.join(',')}&asset_class=${assetClass}&page=${page}&page_size=${pageSize}`
    ),
}

// ============================================
// Pricing API
// ============================================

export const pricingApi = {
  // Get pricing status
  getStatus: (tenantId: string = DEFAULT_TENANT_ID) =>
    fetchApi<PricingStatus>(`/pricing/status?tenant_id=${tenantId}`),

  // Trigger full reprice
  repriceAll: (tenantId: string = DEFAULT_TENANT_ID, userId?: string) => {
    let url = `/pricing/reprice-all?tenant_id=${tenantId}`
    if (userId) url += `&user_id=${userId}`
    return fetchApi<RepriceResponse>(url, { method: 'POST' })
  },

  // Get security price
  getSecurityPrice: (securityId: string) =>
    fetchApi<SecurityPrice>(`/pricing/security/${securityId}`),

  // Override security price
  overrideSecurityPrice: (securityId: string, price: number, userId: string, reason?: string) =>
    fetchApi<PriceOverrideResponse>(`/pricing/security/${securityId}/override?user_id=${userId}`, {
      method: 'PUT',
      body: JSON.stringify({ price, reason }),
    }),

  // Get position valuation
  getPositionValuation: (positionId: string) =>
    fetchApi<ValuationResponse>(`/pricing/valuation/${positionId}`),

  // Override model inputs
  overrideModelInputs: (positionId: string, overrideInputs: Record<string, any>, reason: string, userId: string) =>
    fetchApi<ModelOverrideResponse>(`/pricing/valuation/${positionId}/override?user_id=${userId}`, {
      method: 'PUT',
      body: JSON.stringify({ override_inputs: overrideInputs, reason }),
    }),

  // Recalculate position
  recalculatePosition: (positionId: string) =>
    fetchApi<any>(`/pricing/valuation/${positionId}/recalculate`, { method: 'POST' }),
}

// ============================================
// Market Data API
// ============================================

export const marketApi = {
  // Get market snapshot
  getSnapshot: (symbols?: string[]) => {
    let url = '/market/snapshot'
    if (symbols?.length) url += `?symbols=${symbols.join(',')}`
    return fetchApi<MarketSnapshotResponse>(url)
  },

  // Get single quote
  getQuote: (symbol: string) =>
    fetchApi<MarketIndex>(`/market/quote/${symbol}`),

  // Get available symbols
  getSymbols: () =>
    fetchApi<AvailableSymbolsResponse>('/market/symbols'),
}

// ============================================
// Type Definitions for New APIs
// ============================================

interface RiskSummary {
  nav: number
  gross_exposure: number
  net_exposure: number
  long_exposure: number
  short_exposure: number
  position_count: number
  security_count: number
  book_count: number
  total_delta: number
  total_dv01: number
  total_cs01: number
  last_priced?: string
}

interface PositionOverlapItem {
  security_id: string
  ticker?: string
  security_name: string
  asset_class: string
  book_count: number
  books: string[]
  book_ids: string[]
  net_quantity: number
  gross_exposure: number
  net_exposure: number
  netting_opportunity: number
  net_delta: number
  net_dv01: number
  net_cs01: number
}

interface ConcentrationItem {
  sector?: string
  security_id?: string
  ticker?: string
  security_name?: string
  asset_class?: string
  security_count?: number
  book_count: number
  gross_exposure: number
  net_exposure: number
  percentage: number
  is_warning: boolean
}

interface PositionsResponse {
  positions: PositionDetail[]
  total: number
  page: number
  page_size: number
  total_pages: number
}

interface PositionDetail {
  position_id: string
  book_id: string
  book_name: string
  security_id: string
  ticker?: string
  security_name: string
  asset_class: string
  direction: string
  quantity: number
  cost_basis: number
  current_price: number
  market_value: number
  unrealized_pnl: number
  delta: number
  gamma: number
  vega: number
  theta: number
  dv01: number
  cs01: number
  price_source: string
  price_date?: string
  has_model_details: boolean
}

interface PricingStatus {
  latest_run?: {
    id: string
    trigger_type: string
    started_at: string
    completed_at?: string
    securities_priced: number
    securities_failed: number
    status: string
    error_details?: Record<string, any>
  }
  price_sources: Record<string, number>
  stale_price_count: number
}

interface RepriceResponse {
  run_id: string
  status: string
  securities_priced: number
  securities_failed: number
  message: string
}

interface SecurityPrice {
  security_id: string
  security_name: string
  asset_class: string
  price: number
  price_date: string
  price_source: string
  model_id?: string
  is_stale: boolean
}

interface PriceOverrideResponse {
  security_id: string
  price: number
  price_date: string
  price_source: string
  updated_by: string
  reason?: string
}

interface ValuationResponse {
  position_id: string
  security_id: string
  ticker?: string
  security_name: string
  asset_class: string
  security_type?: string
  book_id: string
  quantity: number
  direction: string
  current_price: number
  market_value: number
  price_source: string
  price_as_of?: string
  has_model_details: boolean
  model_inputs?: {
    model_name: string
    model_version?: string
    inputs: Record<string, any>
    model_price?: number
    has_override: boolean
    override_inputs?: Record<string, any>
    override_by?: string
    override_at?: string
    override_reason?: string
    calculated_at?: string
  }
  can_override: boolean
}

interface ModelOverrideResponse {
  model_id: string
  has_override: boolean
  override_inputs: Record<string, any>
  override_by: string
  override_reason: string
  message: string
}

interface MarketSnapshotResponse {
  indices: MarketIndex[]
  as_of: string
}

interface MarketIndex {
  symbol: string
  name: string
  value: number
  formatted_value: string
  change_pct: number
  change_direction: 'up' | 'down' | 'flat'
  sparkline: number[]
  category: string
  as_of: string
}

interface AvailableSymbolsResponse {
  symbols: string[]
  categories: Record<string, string[]>
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
