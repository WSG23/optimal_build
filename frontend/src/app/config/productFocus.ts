export const PRIMARY_MARKET = 'Singapore'

export const PUBLIC_JURISDICTIONS = ['SG'] as const

export const INTERNAL_JURISDICTION_FLAGS = {
  HK: false,
  NZ: false,
  SEA: false,
  TOR: false,
} as const

export type PartnerIntegrationStatus =
  | 'live'
  | 'partner_access_required'
  | 'coming_soon'

export interface PartnerIntegrationDefinition {
  id: string
  name: string
  category: 'portal' | 'market_data' | 'crm' | 'regulatory'
  status: PartnerIntegrationStatus
  description: string
  detail: string
  nextStep: string
}

export const PARTNER_INTEGRATIONS: PartnerIntegrationDefinition[] = [
  {
    id: 'ura_data_service',
    name: 'URA Data Service',
    category: 'market_data',
    status: 'live',
    description: 'Primary Singapore planning and land-data foundation.',
    detail:
      'Live Singapore workflows should anchor to official URA datasets and expose provenance in every result.',
    nextStep:
      'Use as the default land-data spine for Singapore deal screening.',
  },
  {
    id: 'propertyguru',
    name: 'PropertyGuru',
    category: 'portal',
    status: 'partner_access_required',
    description: 'Singapore portal distribution and listing visibility.',
    detail:
      'Commercial access is required before any live publish, sync, or lead routing should appear in the product.',
    nextStep: 'Enable only for partner-approved accounts.',
  },
  {
    id: 'edgeprop',
    name: 'EdgeProp',
    category: 'market_data',
    status: 'partner_access_required',
    description: 'Singapore market comparables and transaction context.',
    detail:
      'Position as a gated market-data relationship, not as a self-serve connection flow.',
    nextStep:
      'Expose once data rights and usage limits are contractually confirmed.',
  },
  {
    id: 'zoho_crm',
    name: 'Zoho CRM',
    category: 'crm',
    status: 'coming_soon',
    description:
      'Lead and relationship handoff for teams that still run CRM outside Optimal Build.',
    detail:
      'Keep hidden behind a roadmap state until there is a non-mock account and sync model.',
    nextStep: 'Ship after the first live Singapore data partnership is stable.',
  },
]

export interface SampleProjectDefinition {
  name: string
  description: string
  templateId: string
}

export const SINGAPORE_SAMPLE_PROJECT: SampleProjectDefinition = {
  name: 'Singapore Mixed-Use Demo',
  description:
    'Seeded demonstration project for Singapore developer underwriting, workbook import, and audit evidence review.',
  templateId: 'sg_mixed_use',
}
