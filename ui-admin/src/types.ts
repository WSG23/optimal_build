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

export interface BuildableRuleProvenance {
  rule_id: number;
  clause_ref: string | null;
  document_id: number | null;
  pages: number[] | null;
  seed_tag: string | null;
}

export interface BuildableRuleRecord {
  id: number;
  authority: string;
  parameter_key: string;
  operator: string;
  value: string;
  unit: string | null;
  provenance: BuildableRuleProvenance;
}

export interface BuildableMetrics {
  gfa_cap_m2: number;
  floors_max: number;
  footprint_m2: number;
  nsa_est_m2: number;
}

export interface ZoneSourceInfo {
  kind: 'parcel' | 'geometry' | 'unknown';
  layer_name: string | null;
  jurisdiction: string | null;
  parcel_ref: string | null;
  parcel_source: string | null;
  note: string | null;
}

export interface BuildableScreeningResponse {
  input_kind: 'address' | 'geometry';
  zone_code: string | null;
  overlays: string[];
  advisory_hints: string[];
  metrics: BuildableMetrics;
  zone_source: ZoneSourceInfo;
  rules: BuildableRuleRecord[];
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

export interface PaginatedResponse<T> {
  items: T[];
  total: number;
  limit: number;
  offset: number;
}

export interface EntRoadmapItemRecord {
  id: number;
  project_id: number;
  approval_type_id: number | null;
  sequence_order: number;
  status: string;
  status_changed_at: string | null;
  target_submission_date: string | null;
  target_decision_date: string | null;
  actual_submission_date: string | null;
  actual_decision_date: string | null;
  notes: string | null;
  metadata: Record<string, unknown>;
  created_at: string;
  updated_at: string;
}

export interface EntStudyRecord {
  id: number;
  project_id: number;
  name: string;
  study_type: string;
  status: string;
  summary: string | null;
  consultant: string | null;
  due_date: string | null;
  completed_at: string | null;
  attachments: Record<string, unknown>[];
  metadata: Record<string, unknown>;
  created_at: string;
  updated_at: string;
}

export interface EntEngagementRecord {
  id: number;
  project_id: number;
  name: string;
  organisation: string | null;
  engagement_type: string;
  status: string;
  contact_email: string | null;
  contact_phone: string | null;
  meetings: Record<string, unknown>[];
  notes: string | null;
  metadata: Record<string, unknown>;
  created_at: string;
  updated_at: string;
}

export interface EntLegalInstrumentRecord {
  id: number;
  project_id: number;
  name: string;
  instrument_type: string;
  status: string;
  reference_code: string | null;
  effective_date: string | null;
  expiry_date: string | null;
  attachments: Record<string, unknown>[];
  metadata: Record<string, unknown>;
  created_at: string;
  updated_at: string;
}
