// API Response Types

export interface FirmSummary {
  tenant_id: string
  total_books: number
  total_positions: number
  gross_exposure: number
  net_exposure: number
  long_exposure: number
  short_exposure: number
  netting_efficiency: number
  total_overlaps: number
  high_severity_overlaps: number
  as_of: string
}

export interface NettingSummary {
  gross_exposure: number
  net_exposure: number
  netting_benefit: number
  netting_efficiency: number
  total_securities: number
  netted_securities: number
}

export interface Overlap {
  security_id: string
  ticker: string
  security_name: string
  pm_count: number
  book_count: number
  long_exposure: number
  short_exposure: number
  net_exposure: number
  severity: 'high' | 'medium' | 'low'
  overlap_type: 'concentration' | 'netting_opportunity' | 'offset'
  books: OverlapBook[]
}

export interface OverlapBook {
  book_id: string
  book_name: string
  pm_name: string
  quantity: number
  exposure: number
  direction: 'long' | 'short'
}

export interface OverlapSummary {
  total_overlaps: number
  high_severity: number
  medium_severity: number
  low_severity: number
  total_netting_opportunity: number
  concentration_risk_exposure: number
}

export interface CorrelationPair {
  pm1_id: string
  pm1_name: string
  pm2_id: string
  pm2_name: string
  correlation: number
  window_days: number
  data_points: number
  strength: 'strong_positive' | 'moderate_positive' | 'weak' | 'moderate_negative' | 'strong_negative'
  is_concerning: boolean
}

export interface CorrelationMatrix {
  pm_ids: string[]
  pm_names: string[]
  matrix: number[][]
  window_days: number
  as_of: string
}

export interface HierarchyNode {
  id: string
  name: string
  type: 'firm' | 'fund' | 'pm' | 'book'
  gross_exposure: number
  net_exposure: number
  position_count: number
  children: HierarchyNode[]
}

export interface Position {
  id: string
  book_id: string
  security_id: string
  ticker: string
  security_name: string
  quantity: number
  current_price: number
  market_value: number
  direction: 'long' | 'short'
  asset_class: string
  sector: string
  geography: string
}

export interface ExposureBreakdown {
  dimension: string
  items: ExposureItem[]
  total_exposure: number
}

export interface ExposureItem {
  name: string
  value: number
  percentage: number
  long_exposure: number
  short_exposure: number
}

// UI Types

export interface RiskCardProps {
  title: string
  value: string | number
  change?: number
  changeLabel?: string
  icon?: React.ReactNode
  color?: 'green' | 'red' | 'yellow' | 'neutral'
  subtitle?: string
}

export interface BookSelectorOption {
  id: string
  name: string
  type: 'firm' | 'fund' | 'pm' | 'book'
  level: number
}

// API Error
export interface ApiError {
  detail: string
  status_code: number
}

// ============================================
// CIO Dashboard Types
// ============================================

// Asset class-based risk aggregation
export interface AssetClassRisk {
  asset_class: string
  asset_class_display: string
  position_count: number
  book_count?: number
  gross_exposure: number
  net_exposure: number
  delta: number
  gamma: number
  vega: number
  theta: number
  rho: number
  dv01: number
  cs01: number
  convexity: number
  primary_risk_metric: string
  primary_risk_value: number
}

// Book with optional overlay info
export interface Book {
  book_id: string
  name: string
  book_type: 'trading' | 'overlay'
  strategy?: string
  pm_id?: string
  pm_name?: string
  fund_name?: string
}

// Overlay book with source books
export interface OverlayBook extends Book {
  source_books: SourceBook[]
  source_count: number
}

export interface SourceBook {
  book_id: string
  name: string
  hedge_weight: number
  target_metric: string
}

// Trade details for drill-down
export interface TradeDetail {
  trade_id: string
  book_id: string
  book_name: string
  security_id: string
  ticker: string
  security_name: string
  asset_class: string
  side: 'buy' | 'sell' | 'short' | 'cover'
  quantity: number
  price: number
  notional: number
  trade_date: string
  settlement_date?: string
  trader_name?: string
  // Risk factors
  delta?: number
  gamma?: number
  vega?: number
  dv01?: number
  cs01?: number
  // Valuation
  price_source: 'market' | 'manual' | 'model' | 'stale'
  has_model_details: boolean
}

// Position with valuation details
export interface PositionWithValuation extends Position {
  price_source: 'market' | 'manual' | 'model' | 'stale'
  delta?: number
  gamma?: number
  vega?: number
  theta?: number
  rho?: number
  dv01?: number
  cs01?: number
  convexity?: number
}

// Valuation details for model transparency
export interface ValuationDetail {
  position_id: string
  security_id: string
  price_source: 'market' | 'manual' | 'model' | 'stale'
  current_price: number
  price_as_of: string
  // Model-derived pricing
  model_name?: string
  model_version?: string
  model_inputs?: Record<string, number>
  model_output?: number
  // Override info
  has_override: boolean
  override_inputs?: Record<string, number>
  override_by?: string
  override_at?: string
  override_reason?: string
  can_override: boolean
}

// User role context for role-based views
export interface UserContext {
  user_id: string
  tenant_id: string
  email: string
  name: string
  role: 'superadmin' | 'admin' | 'cio' | 'cro' | 'pm' | 'analyst'
  accessible_books: string[]
  can_view_firm_wide: boolean
  can_manage_overlay: boolean
}

// Book correlation for portfolio comparison
export interface BookCorrelation {
  book1_id: string
  book1_name: string
  book2_id: string
  book2_name: string
  correlation: number
  overlapping_securities: number
  netting_opportunity: number
  data_points: number
}
