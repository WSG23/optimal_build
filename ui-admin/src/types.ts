export interface SourceRecord {
  id: number;
  jurisdiction: string;
  authority: string;
  topic: string;
  doc_title: string;
  landing_url: string;
}

export interface DocumentRecord {
  id: number;
  source_id: number;
  version_label: string | null;
  storage_path: string;
  retrieved_at: string | null;
}

export interface ClauseRecord {
  id: number;
  document_id: number;
  clause_ref: string | null;
  section_heading: string | null;
  text_span: string;
  page_from: number | null;
  page_to: number | null;
}

export interface RuleRecord {
  id: number;
  parameter_key: string;
  operator: string;
  value: string;
  unit: string | null;
  jurisdiction: string;
  authority: string;
  topic: string;
  review_status: string;
  is_published: boolean;
  overlays: string[];
  advisory_hints: string[];
  normalized: NormalizedParameter[];
}

export interface NormalizedParameter {
  parameter_key: string;
  operator: string;
  value: number | string;
  unit?: string;
  hints: string[];
}

export interface DiffRecord {
  rule_id: number;
  baseline: string;
  updated: string;
}

export interface BuildableScreeningResponse {
  input_kind: 'address' | 'geometry';
  zone_code: string | null;
  overlays: string[];
  advisory_hints: string[];
  buildable_metrics: BuildableMetrics | null;
}

export interface BuildableMetrics {
  site_area_sqm: number;
  plot_ratio: number;
  assumed_floorplate_sqm: number;
  gross_floor_area_sqm: number;
  net_floor_area_sqm: number;
  estimated_storeys: number;
  estimated_height_m: number;
  efficiency_ratio: number;
  typ_floor_to_floor_m: number;
}

export interface ProductRecord {
  id: number;
  vendor: string;
  category: string;
  product_code: string;
  name: string;
  brand: string | null;
  model_number: string | null;
  sku: string | null;
  dimensions: Record<string, number>;
  bim_uri: string | null;
  spec_uri: string | null;
}

export interface ErgonomicsMetric {
  id: number;
  metric_key: string;
  population: string;
  percentile: string | null;
  value: number;
  unit: string;
  context: Record<string, unknown>;
  notes: string | null;
}
