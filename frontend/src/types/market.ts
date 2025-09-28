export interface MarketReport {
  report_date: string;
  property_type: string;
  location: string;
  period_months: number;
  executive_summary: ExecutiveSummary;
  comparables?: ComparablesAnalysis;
  supply_pipeline?: SupplyPipelineAnalysis;
  yield_analysis?: YieldAnalysis;
  absorption_trends?: AbsorptionAnalysis;
  market_dynamics?: MarketDynamics;
  recommendations: string[];
}

export interface ExecutiveSummary {
  market_sentiment: 'bullish' | 'neutral' | 'bearish';
  key_metrics: {
    avg_price_psf: number;
    median_cap_rate: number;
    total_transaction_volume: number;
    yoy_price_change: number;
    vacancy_rate: number;
    new_supply_sqm: number;
  };
  key_findings: string[];
}

export interface ComparablesAnalysis {
  total_transactions: number;
  transactions: MarketTransaction[];
  price_statistics: {
    mean: number;
    median: number;
    std_dev: number;
    min: number;
    max: number;
  };
  trends: {
    price_trend: 'increasing' | 'stable' | 'decreasing';
    volume_trend: 'increasing' | 'stable' | 'decreasing';
  };
}

export interface MarketTransaction {
  id: string;
  property_id: string;
  property_name: string;
  transaction_date: string;
  sale_price: number;
  psf_price?: number;
  property_type: string;
  district?: string;
  floor_area_sqm?: number;
  buyer_type?: string;
  seller_type?: string;
}

export interface SupplyPipelineAnalysis {
  total_pipeline_sqm: number;
  projects_count: number;
  projects: DevelopmentPipeline[];
  completion_timeline: {
    [year: string]: number; // sqm by year
  };
  impact_assessment: string;
}

export interface DevelopmentPipeline {
  id: string;
  project_name: string;
  developer: string;
  property_type: string;
  total_gfa_sqm: number;
  expected_completion: string;
  development_status: string;
  district?: string;
  units_total?: number;
  pre_commitment_rate?: number;
}

export interface YieldAnalysis {
  current_yields: {
    cap_rate_median: number;
    rental_yield_median: number;
    spread_vs_risk_free: number;
  };
  benchmarks: YieldBenchmark[];
  yield_trends: {
    direction: 'compressing' | 'stable' | 'expanding';
    basis_points_change: number;
  };
}

export interface YieldBenchmark {
  id: string;
  benchmark_date: string;
  property_type: string;
  district?: string;
  location_tier?: string;
  cap_rate_median: number;
  cap_rate_mean?: number;
  cap_rate_min?: number;
  cap_rate_max?: number;
  rental_yield_median?: number;
  sample_size?: number;
}

export interface AbsorptionAnalysis {
  net_absorption_sqm: number;
  gross_absorption_sqm: number;
  absorption_rate: number;
  avg_time_to_lease: number;
  data: AbsorptionData[];
  velocity_assessment: string;
}

export interface AbsorptionData {
  id: string;
  tracking_date: string;
  property_type: string;
  district?: string;
  units_launched?: number;
  units_sold_period?: number;
  sales_absorption_rate?: number;
  nla_leased_period?: number;
  leasing_absorption_rate?: number;
  velocity_trend?: string;
}

export interface MarketDynamics {
  current_cycle_phase: string;
  phase_confidence: number;
  cycles: MarketCycle[];
  leading_indicators: {
    [indicator: string]: {
      value: number;
      trend: string;
      signal: string;
    };
  };
  market_outlook: string;
}

export interface MarketCycle {
  id: string;
  cycle_date: string;
  property_type: string;
  cycle_phase: string;
  phase_duration_months?: number;
  price_momentum?: number;
  rental_momentum?: number;
  supply_demand_ratio?: number;
  cycle_outlook?: string;
  model_confidence?: number;
}