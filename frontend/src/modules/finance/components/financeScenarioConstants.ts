import type { FinanceFeasibilityRequest } from '../../../api/finance'

export type AssetFormRow = {
  id: string
  assetType: string
  allocationPct: string
  niaSqm: string
  rentPsmMonth: string
  vacancyPct: string
  opexPct: string
  estimatedRevenue: string
  estimatedCapex: string
  absorptionMonths: string
  riskLevel: string
  notes: string
}

export const DEFAULT_ASSET_ROWS: Array<Omit<AssetFormRow, 'id'>> = [
  {
    assetType: 'Office',
    allocationPct: '55',
    niaSqm: '1000',
    rentPsmMonth: '10',
    vacancyPct: '5',
    opexPct: '20',
    estimatedRevenue: '91200',
    estimatedCapex: '500000',
    absorptionMonths: '6',
    riskLevel: 'balanced',
    notes: 'Office baseline with healthy demand.',
  },
  {
    assetType: 'Retail',
    allocationPct: '25',
    niaSqm: '500',
    rentPsmMonth: '8',
    vacancyPct: '10',
    opexPct: '25',
    estimatedRevenue: '32400',
    estimatedCapex: '150000',
    absorptionMonths: '9',
    riskLevel: 'moderate',
    notes: 'Retail uplift assumes curated tenant mix.',
  },
]

export function createAssetRows(
  rows: Array<Omit<AssetFormRow, 'id'>>,
): AssetFormRow[] {
  const timestamp = Date.now()
  return rows.map((row, index) => ({
    id: `asset-${String(timestamp)}-${String(index)}`,
    ...row,
  }))
}

export const BASE_FINANCE_REQUEST: FinanceScenarioDefaults = {
  description: 'Phase 2C feasibility scenario',
  currency: 'SGD',
  isPrimary: true,
  costEscalation: {
    amount: '38950000',
    basePeriod: '2024-Q1',
    seriesName: 'construction_all_in',
    jurisdiction: 'SG',
  },
  cashFlow: {
    discountRate: '0.085',
    cashFlows: ['-38950000', '5000000', '7500000', '9500000', '12000000'],
  },
  drawdownSchedule: [
    { period: 'M1', equityDraw: '6000000', debtDraw: '0' },
    { period: 'M2', equityDraw: '4500000', debtDraw: '2500000' },
    { period: 'M3', equityDraw: '3000000', debtDraw: '4500000' },
    { period: 'M4', equityDraw: '1200000', debtDraw: '5000000' },
    { period: 'M5', equityDraw: '800000', debtDraw: '6500000' },
    { period: 'M6', equityDraw: '300000', debtDraw: '4870000' },
  ],
  constructionLoan: {
    interestRate: '0.05',
    periodsPerYear: 12,
    capitaliseInterest: true,
    facilities: [
      {
        name: 'Senior Loan',
        amount: '23370000',
        interestRate: '0.045',
        periodsPerYear: 12,
        capitaliseInterest: true,
      },
      {
        name: 'Mezz Loan',
        amount: '6000000',
        interestRate: '0.08',
        periodsPerYear: 12,
        capitaliseInterest: false,
        upfrontFeePct: '1.0',
        exitFeePct: '2.0',
      },
    ],
  },
  sensitivityBands: [
    { parameter: 'Rent', low: '-8', base: '0', high: '6' },
    { parameter: 'Construction Cost', low: '10', base: '0', high: '-5' },
    {
      parameter: 'Interest Rate (delta %)',
      low: '1.50',
      base: '0',
      high: '-0.75',
    },
  ],
}

export type FinanceScenarioDefaults = Omit<
  FinanceFeasibilityRequest['scenario'],
  'name' | 'assetMix'
>

export type FinanceTemplateDefinition = {
  id: string
  label: string
  description: string
  scenarioName: string
  scenarioDefaults: FinanceScenarioDefaults
  assets: Array<Omit<AssetFormRow, 'id'>>
}

export const SG_FINANCE_TEMPLATES: FinanceTemplateDefinition[] = [
  {
    id: 'sg_mixed_use',
    label: 'SG Mixed-Use',
    description:
      'Balanced residential-retail podium scheme for early Singapore feasibility.',
    scenarioName: 'Singapore Mixed-Use Base Case',
    scenarioDefaults: BASE_FINANCE_REQUEST,
    assets: [
      {
        assetType: 'Residential',
        allocationPct: '60',
        niaSqm: '1800',
        rentPsmMonth: '7',
        vacancyPct: '3',
        opexPct: '12',
        estimatedRevenue: '146664',
        estimatedCapex: '680000',
        absorptionMonths: '7',
        riskLevel: 'balanced',
        notes: 'Assumes city-fringe apartment pricing and stable demand.',
      },
      {
        assetType: 'Retail Podium',
        allocationPct: '25',
        niaSqm: '620',
        rentPsmMonth: '11',
        vacancyPct: '8',
        opexPct: '24',
        estimatedRevenue: '75293',
        estimatedCapex: '210000',
        absorptionMonths: '9',
        riskLevel: 'moderate',
        notes: 'Neighbourhood-serving retail with curated tenant mix.',
      },
      {
        assetType: 'Office',
        allocationPct: '15',
        niaSqm: '420',
        rentPsmMonth: '10',
        vacancyPct: '6',
        opexPct: '18',
        estimatedRevenue: '47376',
        estimatedCapex: '160000',
        absorptionMonths: '8',
        riskLevel: 'moderate',
        notes: 'Flexible office floors above podium retail.',
      },
    ],
  },
  {
    id: 'sg_repositioning',
    label: 'Office Repositioning',
    description:
      'CBD or fringe-office repositioning with capex-led upside and staged leasing risk.',
    scenarioName: 'Singapore Office Repositioning',
    scenarioDefaults: {
      ...BASE_FINANCE_REQUEST,
      cashFlow: {
        discountRate: '0.09',
        cashFlows: ['-32500000', '4500000', '7200000', '10400000', '13800000'],
      },
      sensitivityBands: [
        { parameter: 'Rent', low: '-10', base: '0', high: '8' },
        { parameter: 'Construction Cost', low: '12', base: '0', high: '-4' },
        {
          parameter: 'Interest Rate (delta %)',
          low: '1.75',
          base: '0',
          high: '-0.5',
        },
      ],
    },
    assets: [
      {
        assetType: 'Grade B+ Office',
        allocationPct: '80',
        niaSqm: '2200',
        rentPsmMonth: '12',
        vacancyPct: '7',
        opexPct: '19',
        estimatedRevenue: '294624',
        estimatedCapex: '980000',
        absorptionMonths: '10',
        riskLevel: 'moderate',
        notes: 'Repositioned office floors with lobby and MEP upgrade.',
      },
      {
        assetType: 'Retail / F&B',
        allocationPct: '20',
        niaSqm: '500',
        rentPsmMonth: '13',
        vacancyPct: '9',
        opexPct: '28',
        estimatedRevenue: '70980',
        estimatedCapex: '240000',
        absorptionMonths: '12',
        riskLevel: 'high',
        notes: 'Ground-floor activation and amenity-led rent premium.',
      },
    ],
  },
  {
    id: 'sg_industrial',
    label: 'Industrial / Adaptive Reuse',
    description:
      'Light industrial or adaptive-reuse underwriting with conservative rent and debt assumptions.',
    scenarioName: 'Singapore Industrial Reuse',
    scenarioDefaults: {
      ...BASE_FINANCE_REQUEST,
      cashFlow: {
        discountRate: '0.0825',
        cashFlows: ['-27800000', '3200000', '6100000', '8600000', '11100000'],
      },
      constructionLoan: {
        interestRate: '0.0475',
        periodsPerYear: 12,
        capitaliseInterest: true,
        facilities: [
          {
            name: 'Senior Loan',
            amount: '18370000',
            interestRate: '0.0425',
            periodsPerYear: 12,
            capitaliseInterest: true,
          },
        ],
      },
    },
    assets: [
      {
        assetType: 'Light Industrial',
        allocationPct: '70',
        niaSqm: '2600',
        rentPsmMonth: '6',
        vacancyPct: '5',
        opexPct: '16',
        estimatedRevenue: '177840',
        estimatedCapex: '620000',
        absorptionMonths: '6',
        riskLevel: 'balanced',
        notes: 'Assumes JTC-compatible positioning and efficient floorplates.',
      },
      {
        assetType: 'Ancillary Office',
        allocationPct: '20',
        niaSqm: '700',
        rentPsmMonth: '8',
        vacancyPct: '7',
        opexPct: '18',
        estimatedRevenue: '62496',
        estimatedCapex: '170000',
        absorptionMonths: '7',
        riskLevel: 'moderate',
        notes: 'Support office space tied to industrial occupiers.',
      },
      {
        assetType: 'Retail Support',
        allocationPct: '10',
        niaSqm: '220',
        rentPsmMonth: '9',
        vacancyPct: '10',
        opexPct: '24',
        estimatedRevenue: '21384',
        estimatedCapex: '90000',
        absorptionMonths: '9',
        riskLevel: 'moderate',
        notes: 'Small convenience-led retail component.',
      },
    ],
  },
]

export function cloneScenarioDefaults(
  template: FinanceScenarioDefaults,
): FinanceScenarioDefaults {
  return {
    ...template,
    costEscalation: { ...template.costEscalation },
    cashFlow: {
      ...template.cashFlow,
      cashFlows: [...template.cashFlow.cashFlows],
    },
    drawdownSchedule: template.drawdownSchedule?.map((entry) => ({ ...entry })),
    constructionLoan: template.constructionLoan
      ? {
          ...template.constructionLoan,
          facilities: template.constructionLoan.facilities?.map((facility) => ({
            ...facility,
            metadata: facility.metadata
              ? { ...facility.metadata }
              : facility.metadata,
          })),
        }
      : template.constructionLoan,
    sensitivityBands: template.sensitivityBands?.map((band) => ({ ...band })),
  }
}
