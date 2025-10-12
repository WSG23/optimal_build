import type {
  AnalyticsMetric,
  BenchmarkEntry,
  DealSnapshot,
  PipelineColumn,
  RoiSummary,
  StageEvent,
  CommissionEntry,
  TrendPoint,
} from './types'

export const MOCK_PIPELINE_COLUMNS: PipelineColumn[] = [
  {
    key: 'lead_captured',
    label: 'Lead captured',
    totalCount: 2,
    totalValue: 4800000,
    weightedValue: 960000,
    deals: [
      {
        id: 'deal-001',
        title: 'Harbourfront Tower B',
        assetType: 'Office',
        dealType: 'Sell-side',
        estimatedValue: 3200000,
        currency: 'SGD',
        confidence: 0.3,
        latestActivity: '2 days ago',
      },
      {
        id: 'deal-002',
        title: 'Sentosa Retail Podium',
        assetType: 'Retail',
        dealType: 'Lease',
        estimatedValue: 1600000,
        currency: 'SGD',
        confidence: 0.3,
        latestActivity: '5 days ago',
      },
    ],
  },
  {
    key: 'negotiation',
    label: 'Negotiation',
    totalCount: 1,
    totalValue: 5200000,
    weightedValue: 3120000,
    deals: [
      {
        id: 'deal-003',
        title: 'Changi Logistics Hub',
        assetType: 'Industrial',
        dealType: 'Lease',
        estimatedValue: 5200000,
        currency: 'SGD',
        confidence: 0.6,
        latestActivity: '1 day ago',
        hasDispute: true,
      },
    ],
  },
  {
    key: 'closed_won',
    label: 'Closed won',
    totalCount: 1,
    totalValue: 7500000,
    weightedValue: 7500000,
    deals: [
      {
        id: 'deal-004',
        title: 'Marina View Redevelopment',
        assetType: 'Mixed-use',
        dealType: 'Capital raise',
        estimatedValue: 7500000,
        currency: 'SGD',
        confidence: 1,
        latestActivity: '12 hours ago',
      },
    ],
  },
  {
    key: 'closed_lost',
    label: 'Closed lost',
    totalCount: 0,
    totalValue: null,
    weightedValue: null,
    deals: [],
  },
] as const

export const MOCK_DEAL: DealSnapshot = {
  id: 'deal-003',
  title: 'Changi Logistics Hub',
  agentName: 'Tessa Lim',
  leadSource: 'Developer referral',
  stage: 'negotiation',
  expectedCloseDate: '2025-11-02',
}

export const MOCK_TIMELINE: StageEvent[] = [
  {
    id: 'evt-001',
    toStage: 'lead_captured',
    recordedAt: '2025-09-14 09:12',
    note: 'Inbound enquiry from developer, captured credentials.',
    auditHash: '3d9c5e...a1f4',
    auditSignature: 'sig-001',
  },
  {
    id: 'evt-002',
    toStage: 'negotiation',
    recordedAt: '2025-10-01 14:45',
    durationSeconds: 86400 * 10,
    changedBy: 'Tessa Lim',
    note: 'Developer requested revised floor plate options.',
    auditHash: '7f01c1...ff83',
    auditSignature: 'sig-002',
  },
] as const

export const MOCK_COMMISSIONS: CommissionEntry[] = [
  {
    id: 'cm-001',
    type: 'Exclusive',
    status: 'pending',
    amount: null,
    currency: 'SGD',
    basisAmount: 5200000,
  },
  {
    id: 'cm-002',
    type: 'Introducer',
    status: 'paid',
    amount: 85000,
    currency: 'SGD',
    confirmedAt: '2025-08-11',
  },
] as const

export const MOCK_METRICS: AnalyticsMetric[] = [
  { key: 'dealsOpen', label: 'Open deals', value: '6' },
  { key: 'dealsWon', label: 'Deals won (30d)', value: '2' },
  {
    key: 'grossPipeline',
    label: 'Gross pipeline',
    value: 'SGD 18.4M',
    helperText: 'All open opportunities, unweighted.',
  },
  {
    key: 'weightedPipeline',
    label: 'Weighted pipeline',
    value: 'SGD 9.7M',
    helperText: 'Weighted by confidence percentage.',
  },
  { key: 'conversionRate', label: 'Conversion rate', value: '42.0%' },
  { key: 'avgCycle', label: 'Average cycle', value: '78 days' },
  {
    key: 'confirmedCommission',
    label: 'Confirmed commission',
    value: 'SGD 186K',
  },
  { key: 'disputedCommission', label: 'Disputed commission', value: 'SGD 0' },
] as const

export const MOCK_TREND: TrendPoint[] = [
  { label: 'Week 1', gross: 8.2, weighted: 4.7, conversion: 0.38, cycle: 82 },
  { label: 'Week 2', gross: 9.1, weighted: 5.1, conversion: 0.4, cycle: 80 },
  { label: 'Week 3', gross: 10.5, weighted: 5.7, conversion: 0.41, cycle: 79 },
  { label: 'Week 4', gross: 11.3, weighted: 6.2, conversion: 0.42, cycle: 78 },
] as const

export const MOCK_BENCHMARKS: BenchmarkEntry[] = [
  {
    key: 'conversion',
    label: 'Conversion rate',
    actual: '42.0%',
    benchmark: '38.0%',
    cohort: 'industry avg',
    deltaText: '+4.0 pts',
    deltaPositive: true,
  },
  {
    key: 'cycle',
    label: 'Average cycle time',
    actual: '78 days',
    benchmark: '90 days',
    cohort: 'industry avg',
    deltaText: '-12 days',
    deltaPositive: true,
  },
  {
    key: 'pipeline',
    label: 'Weighted pipeline value',
    actual: 'SGD 9.7M',
    benchmark: 'SGD 12.0M',
    cohort: 'top quartile',
    deltaText: '-SGD 2.3M',
    deltaPositive: false,
  },
] as const

export const MOCK_ROI: RoiSummary = {
  projectCount: 3,
  totalReviewHoursSaved: 18.6,
  averageAutomationScore: 0.62,
  averageAcceptanceRate: 0.78,
  averageSavingsPercent: 0.61,
  bestPaybackWeeks: 3,
  projects: [
    {
      projectId: 3201,
      hoursSaved: 8.4,
      automationScore: 0.62,
      acceptanceRate: 0.78,
      paybackWeeks: 3,
    },
    {
      projectId: 3207,
      hoursSaved: 6.2,
      automationScore: 0.58,
      acceptanceRate: 0.72,
      paybackWeeks: 4,
    },
    {
      projectId: 3210,
      hoursSaved: 4.0,
      automationScore: 0.66,
      acceptanceRate: 0.83,
      paybackWeeks: 2,
    },
  ],
} as const

