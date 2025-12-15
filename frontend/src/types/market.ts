import { PropertyType } from './property'

export interface MarketPeriod {
  start: string
  end: string
}

export interface ComparableTransaction {
  date: string
  property_name: string
  price: number
  psf?: number | null
  buyer_type?: string | null
}

export interface ComparablesAnalysis {
  transaction_count: number
  total_volume: number
  average_psf: number
  median_psf: number
  psf_range: {
    min: number
    max: number
  }
  quarterly_trends: Record<
    string,
    {
      count: number
      total_volume: number
      avg_psf: number
    }
  >
  price_trend: string
  top_transactions: ComparableTransaction[]
  buyer_profile: Record<string, number>
  message?: string
}

export interface MarketTransaction {
  transaction_id: string
  property_name: string
  transaction_date: string
  sale_price: number
  psf_price?: number | null
  property_type: string
  district?: string | null
  floor_area_sqm?: number | null
  buyer_type?: string | null
}

export interface SupplyByYearEntry {
  projects: number
  total_gfa: number
  total_units: number
}

export type SupplyByYear = Record<string, SupplyByYearEntry>

export interface MajorDevelopment {
  name: string
  developer?: string | null
  gfa: number
  units?: number | null
  completion?: string | null
  status: string
}

export interface SupplyDynamics {
  pipeline_projects: number
  total_upcoming_gfa: number
  supply_by_year: SupplyByYear
  supply_pressure: string
  major_developments: MajorDevelopment[]
  market_impact: string
}

export interface YieldBenchmarks {
  current_metrics: {
    cap_rate: {
      mean: number
      median: number
      range: {
        p25: number
        p75: number
      }
    }
    rental_rates: {
      mean_psf: number
      median_psf: number
      occupancy: number
    }
    transaction_volume: {
      count: number
      total_value: number
    }
  }
  trends: {
    cap_rate_trend: string
    rental_trend: string
  }
  yoy_changes: {
    cap_rate_change_bps?: number
    rental_change_pct?: number
    transaction_volume_change_pct?: number
  }
  market_position: string
}

export interface AbsorptionTrends {
  current_metrics: {
    sales_absorption_rate: number
    leasing_absorption_rate: number
    avg_days_to_sale: number
    avg_days_to_lease: number
  }
  period_averages: {
    avg_sales_absorption: number
    avg_leasing_absorption: number
  }
  velocity_trend: string
  market_comparison: {
    vs_market_average: number
  }
  forecast: {
    current_absorption?: number
    projected_absorption_6m?: number
    avg_monthly_absorption?: number
    estimated_sellout_months?: number | null
    message?: string
  }
  seasonal_patterns?: {
    peak_month?: number
    peak_absorption?: number
    low_month?: number
    low_absorption?: number
    seasonality_strength?: number
    message?: string
  }
}

export interface MarketCyclePosition {
  current_phase: string
  phase_duration_months?: number | null
  phase_strength?: number | null
  indicators: {
    price_momentum?: number | null
    rental_momentum?: number | null
    transaction_volume_change?: number | null
    supply_demand_ratio?: number | null
  }
  outlook: {
    next_12_months?: string | null
    pipeline_impact?: number | null
    demand_forecast?: number | null
  }
  index_trends?: {
    current_index?: number
    mom_change?: number
    qoq_change?: number
    yoy_change?: number
    trend?: string
  }
}

export interface MarketReport {
  property_type: PropertyType
  location: string
  period: MarketPeriod
  comparables_analysis: ComparablesAnalysis
  supply_dynamics: SupplyDynamics
  yield_benchmarks: YieldBenchmarks
  absorption_trends: AbsorptionTrends
  market_cycle_position: MarketCyclePosition
  recommendations: string[]
  generated_at: string
}
