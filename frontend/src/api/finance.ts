import { applyIdentityHeaders } from './identity'
import { buildUrl, apiBaseUrl, toOptionalString } from './shared'

export interface CostEscalationInput {
  amount: string
  basePeriod: string
  seriesName: string
  jurisdiction: string
  provider?: string | null
}

export interface CashflowInputs {
  discountRate: string
  cashFlows: string[]
}

export interface DscrInputs {
  netOperatingIncomes: string[]
  debtServices: string[]
  periodLabels?: string[]
}

export interface CapitalStackSliceInput {
  name: string
  sourceType: string
  amount: string
  rate?: string | null
  trancheOrder?: number | null
  metadata?: Record<string, unknown> | null
}

export interface DrawdownPeriodInput {
  period: string
  equityDraw?: string
  debtDraw?: string
}

export interface FinanceAssetMixInput {
  assetType: string
  allocationPct?: string | null
  niaSqm?: string | null
  rentPsmMonth?: string | null
  stabilisedVacancyPct?: string | null
  opexPctOfRent?: string | null
  estimatedRevenueSgd?: string | null
  estimatedCapexSgd?: string | null
  absorptionMonths?: string | null
  riskLevel?: string | null
  heritagePremiumPct?: string | null
  notes?: string[]
}

export interface SensitivityBandInput {
  parameter: string
  low?: string | null
  base?: string | null
  high?: string | null
  notes?: string[]
}

export interface FinanceScenarioInput {
  name: string
  description?: string
  currency: string
  isPrimary?: boolean
  costEscalation: CostEscalationInput
  cashFlow: CashflowInputs
  dscr?: DscrInputs
  capitalStack?: CapitalStackSliceInput[]
  drawdownSchedule?: DrawdownPeriodInput[]
  assetMix?: FinanceAssetMixInput[]
  constructionLoan?: ConstructionLoanInput | null
  sensitivityBands?: SensitivityBandInput[]
}

export interface FinanceFeasibilityRequest {
  projectId: number | string
  projectName?: string
  finProjectId?: number
  scenario: FinanceScenarioInput
}

export interface CostIndexSnapshot {
  period: string
  value: string
  unit: string
  source?: string | null
  provider?: string | null
  methodology?: string | null
}

export interface CostIndexProvenance {
  seriesName: string
  jurisdiction: string
  provider?: string | null
  basePeriod: string
  latestPeriod?: string | null
  scalar?: string | null
  baseIndex?: CostIndexSnapshot | null
  latestIndex?: CostIndexSnapshot | null
}

export interface DscrEntry {
  period: string
  noi: string
  debtService: string
  dscr?: string | null
  currency: string
}

export interface FinanceResultItem {
  name: string
  value?: string | null
  unit?: string | null
  metadata: Record<string, unknown>
}

export interface CapitalStackSlice {
  name: string
  sourceType: string
  category: string
  amount: string
  share: string
  rate?: string | null
  trancheOrder?: number | null
  metadata: Record<string, unknown>
}

export interface CapitalStackSummary {
  currency: string
  total: string
  equityTotal: string
  debtTotal: string
  otherTotal: string
  equityRatio?: string | null
  debtRatio?: string | null
  otherRatio?: string | null
  loanToCost?: string | null
  weightedAverageDebtRate?: string | null
  slices: CapitalStackSlice[]
}

export interface AssetFinancialSummary {
  totalEstimatedRevenueSgd: string | null
  totalEstimatedCapexSgd: string | null
  dominantRiskProfile: string | null
  notes: string[]
}

export interface FinanceAssetBreakdown {
  assetType: string
  allocationPct: string | null
  niaSqm: string | null
  rentPsmMonth: string | null
  grossRentAnnualSgd: string | null
  vacancyLossSgd: string | null
  effectiveGrossIncomeSgd: string | null
  operatingExpensesSgd: string | null
  noiAnnualSgd: string | null
  estimatedCapexSgd: string | null
  paybackYears: string | null
  absorptionMonths: string | null
  riskLevel: string | null
  heritagePremiumPct: string | null
  notes: string[]
}

export interface ConstructionLoanFacilityInput {
  name: string
  amount?: string | null
  interestRate?: string | null
  periodsPerYear?: number | null
  capitaliseInterest?: boolean | null
  upfrontFeePct?: string | null
  exitFeePct?: string | null
  reserveMonths?: number | null
  amortisationMonths?: number | null
  metadata?: Record<string, unknown> | null
}

export interface ConstructionLoanInput {
  interestRate?: string | null
  periodsPerYear?: number | null
  capitaliseInterest?: boolean | null
  facilities?: ConstructionLoanFacilityInput[] | null
}

export interface ConstructionLoanInterestFacility {
  name: string
  amount: string | null
  interestRate: string | null
  periodsPerYear: number | null
  capitalised: boolean
  totalInterest: string | null
  upfrontFee: string | null
  exitFee: string | null
}

export interface ConstructionLoanInterestEntry {
  period: string
  openingBalance: string
  closingBalance: string
  averageBalance: string
  interestAccrued: string
}

export interface ConstructionLoanInterest {
  currency: string
  interestRate: string | null
  periodsPerYear: number | null
  capitalised: boolean
  totalInterest: string | null
  upfrontFeeTotal: string | null
  exitFeeTotal: string | null
  facilities: ConstructionLoanInterestFacility[]
  entries: ConstructionLoanInterestEntry[]
}

export interface FinanceSensitivityOutcome {
  parameter: string
  scenario: string
  deltaLabel: string | null
  deltaValue: string | null
  npv: string | null
  irr: string | null
  escalatedCost: string | null
  totalInterest: string | null
  notes: string[]
}

export interface FinanceJobStatus {
  scenarioId: number
  taskId: string | null
  status: string
  backend: string | null
  queuedAt: string | null
}

export interface DrawdownEntry {
  period: string
  equityDraw: string
  debtDraw: string
  totalDraw: string
  cumulativeEquity: string
  cumulativeDebt: string
  outstandingDebt: string
}

export interface DrawdownSchedule {
  currency: string
  entries: DrawdownEntry[]
  totalEquity: string
  totalDebt: string
  peakDebtBalance: string
  finalDebtBalance: string
}

export interface FinanceAnalyticsBucket {
  key: string
  label: string
  count: number
  periods: string[]
}

export interface FinanceAnalyticsMetadata {
  moic?: string | null
  equity_multiple?: string | null
  cash_flow_summary?: {
    invested_equity?: string | null
    distributions?: string | null
    net_cash?: string | null
  }
  dscr_heatmap?: {
    buckets?: FinanceAnalyticsBucket[]
    entries?: Array<{
      period?: string
      dscr?: string | null
      bucket?: string | null
    }>
  }
  drawdown_summary?: {
    total_equity?: string | null
    total_debt?: string | null
    peak_debt_balance?: string | null
  }
  [key: string]: unknown
}

export interface FinanceScenarioSummary {
  scenarioId: number
  projectId: number | string
  finProjectId: number | null
  scenarioName: string
  description?: string | null
  currency: string
  escalatedCost: string
  costIndex: CostIndexProvenance
  results: FinanceResultItem[]
  dscrTimeline: DscrEntry[]
  capitalStack: CapitalStackSummary | null
  drawdownSchedule: DrawdownSchedule | null
  assetMixSummary: AssetFinancialSummary | null
  assetBreakdowns: FinanceAssetBreakdown[]
  constructionLoanInterest: ConstructionLoanInterest | null
  constructionLoan: ConstructionLoanInput | null
  sensitivityResults: FinanceSensitivityOutcome[]
  sensitivityJobs: FinanceJobStatus[]
  sensitivityBands: SensitivityBandInput[]
  isPrimary?: boolean
  isPrivate?: boolean
  updatedAt?: string | null
}

export interface FinanceScenarioUpdateInput {
  scenarioName?: string
  description?: string | null
  isPrimary?: boolean
}

interface FinanceFeasibilityRequestPayload {
  project_id: number
  project_name?: string
  fin_project_id?: number
  scenario: {
    name: string
    description?: string
    currency: string
    is_primary: boolean
    cost_escalation: {
      amount: string
      base_period: string
      series_name: string
      jurisdiction: string
      provider?: string | null
    }
    cash_flow: {
      discount_rate: string
      cash_flows: string[]
    }
    dscr?: {
      net_operating_incomes: string[]
      debt_services: string[]
      period_labels?: string[]
    }
    capital_stack?: Array<{
      name: string
      source_type: string
      amount: string
      rate?: string | null
      tranche_order?: number | null
      metadata?: Record<string, unknown> | null
    }>
    drawdown_schedule?: Array<{
      period: string
      equity_draw?: string
      debt_draw?: string
    }>
    asset_mix?: AssetMixPayload[]
    construction_loan?: ConstructionLoanInputPayload
    sensitivity_bands?: SensitivityBandPayload[]
  }
}

interface AssetMixPayload {
  asset_type: string
  allocation_pct?: string
  nia_sqm?: string
  rent_psm_month?: string
  stabilised_vacancy_pct?: string
  opex_pct_of_rent?: string
  estimated_revenue_sgd?: string
  estimated_capex_sgd?: string
  absorption_months?: string
  risk_level?: string | null
  heritage_premium_pct?: string
  notes?: string[]
}

interface SensitivityBandPayload {
  parameter: string
  low?: string
  base?: string
  high?: string
  notes?: string[]
}

interface CostIndexSnapshotPayload {
  period: string
  value: string
  unit: string
  source?: string | null
  provider?: string | null
  methodology?: string | null
}

interface CostIndexProvenancePayload {
  series_name: string
  jurisdiction: string
  provider?: string | null
  base_period: string
  latest_period?: string | null
  scalar?: string | null
  base_index?: CostIndexSnapshotPayload | null
  latest_index?: CostIndexSnapshotPayload | null
}

interface FinanceResultPayload {
  name: string
  value?: string | null
  unit?: string | null
  metadata?: Record<string, unknown> | null
}

interface CapitalStackSlicePayload {
  name: string
  source_type: string
  category: string
  amount: string
  share: string
  rate?: string | null
  tranche_order?: number | null
  metadata?: Record<string, unknown> | null
}

interface CapitalStackSummaryPayload {
  currency: string
  total: string
  equity_total: string
  debt_total: string
  other_total: string
  equity_ratio?: string | null
  debt_ratio?: string | null
  other_ratio?: string | null
  loan_to_cost?: string | null
  weighted_average_debt_rate?: string | null
  slices: CapitalStackSlicePayload[]
}

interface DscrEntryPayload {
  period: string
  noi: string
  debt_service: string
  dscr?: string | null
  currency: string
}

interface DrawdownEntryPayload {
  period: string
  equity_draw: string
  debt_draw: string
  total_draw: string
  cumulative_equity: string
  cumulative_debt: string
  outstanding_debt: string
}

interface DrawdownSchedulePayload {
  currency: string
  entries: DrawdownEntryPayload[]
  total_equity: string
  total_debt: string
  peak_debt_balance: string
  final_debt_balance: string
}

interface AssetFinancialSummaryPayload {
  total_estimated_revenue_sgd?: string | null
  total_estimated_capex_sgd?: string | null
  dominant_risk_profile?: string | null
  notes?: string[]
}

interface FinanceAssetBreakdownPayload {
  asset_type: string
  allocation_pct?: string | null
  nia_sqm?: string | null
  rent_psm_month?: string | null
  gross_rent_annual_sgd?: string | null
  vacancy_loss_sgd?: string | null
  effective_gross_income_sgd?: string | null
  operating_expenses_sgd?: string | null
  noi_annual_sgd?: string | null
  estimated_capex_sgd?: string | null
  payback_years?: string | null
  absorption_months?: string | null
  risk_level?: string | null
  heritage_premium_pct?: string | null
  notes?: string[]
}

interface ConstructionLoanFacilityInputPayload {
  name: string
  amount?: string | null
  interest_rate?: string | null
  periods_per_year?: number | null
  capitalise_interest?: boolean | null
  upfront_fee_pct?: string | null
  exit_fee_pct?: string | null
  reserve_months?: number | null
  amortisation_months?: number | null
}

interface ConstructionLoanInputPayload {
  interest_rate?: string | null
  periods_per_year?: number | null
  capitalise_interest?: boolean | null
  facilities?: ConstructionLoanFacilityInputPayload[] | null
}

interface ConstructionLoanFacilityPayload {
  name: string
  amount?: string | null
  interest_rate?: string | null
  periods_per_year?: number | null
  capitalised?: boolean | null
  total_interest?: string | null
  upfront_fee?: string | null
  exit_fee?: string | null
  reserve_months?: number | null
  amortisation_months?: number | null
}

interface ConstructionLoanInterestEntryPayload {
  period: string
  opening_balance: string
  closing_balance: string
  average_balance: string
  interest_accrued: string
}

interface ConstructionLoanInterestPayload {
  currency: string
  interest_rate?: string | null
  periods_per_year?: number | null
  capitalised?: boolean | null
  total_interest?: string | null
  upfront_fee_total?: string | null
  exit_fee_total?: string | null
  facilities?: ConstructionLoanFacilityPayload[] | null
  entries?: ConstructionLoanInterestEntryPayload[] | null
}

interface FinanceSensitivityOutcomePayload {
  parameter: string
  scenario: string
  delta_label?: string | null
  delta_value?: string | null
  npv?: string | null
  irr?: string | null
  escalated_cost?: string | null
  total_interest?: string | null
  notes?: string[]
}

interface FinanceJobStatusPayload {
  scenario_id: number
  task_id?: string | null
  status: string
  backend?: string | null
  queued_at?: string | null
}

interface FinanceFeasibilityResponsePayload {
  scenario_id: number
  project_id: number
  fin_project_id: number
  scenario_name: string
  currency: string
  escalated_cost: string
  cost_index: CostIndexProvenancePayload
  results: FinanceResultPayload[]
  dscr_timeline: DscrEntryPayload[]
  capital_stack?: CapitalStackSummaryPayload | null
  drawdown_schedule?: DrawdownSchedulePayload | null
  asset_mix_summary?: AssetFinancialSummaryPayload | null
  asset_breakdowns?: FinanceAssetBreakdownPayload[] | null
  construction_loan_interest?: ConstructionLoanInterestPayload | null
  construction_loan?: ConstructionLoanInputPayload | null
  sensitivity_results?: FinanceSensitivityOutcomePayload[] | null
  sensitivity_jobs?: FinanceJobStatusPayload[] | null
  sensitivity_bands?: SensitivityBandPayload[] | null
  is_primary?: boolean | null
  is_private?: boolean | null
  updated_at?: string | null
}

interface ConstructionLoanUpdateRequestPayload {
  construction_loan: ConstructionLoanInputPayload
}

function toAssetMixPayload(entry: FinanceAssetMixInput): AssetMixPayload {
  return {
    asset_type: entry.assetType,
    allocation_pct: toOptionalString(entry.allocationPct),
    nia_sqm: toOptionalString(entry.niaSqm),
    rent_psm_month: toOptionalString(entry.rentPsmMonth),
    stabilised_vacancy_pct: toOptionalString(entry.stabilisedVacancyPct),
    opex_pct_of_rent: toOptionalString(entry.opexPctOfRent),
    estimated_revenue_sgd: toOptionalString(entry.estimatedRevenueSgd),
    estimated_capex_sgd: toOptionalString(entry.estimatedCapexSgd),
    absorption_months: toOptionalString(entry.absorptionMonths),
    risk_level: entry.riskLevel ?? undefined,
    heritage_premium_pct: toOptionalString(entry.heritagePremiumPct),
    notes: entry.notes?.length ? [...entry.notes] : undefined,
  }
}

function toSensitivityBandPayload(
  band: SensitivityBandInput,
): SensitivityBandPayload {
  return {
    parameter: band.parameter,
    low: toOptionalString(band.low),
    base: toOptionalString(band.base),
    high: toOptionalString(band.high),
    notes: band.notes?.length ? [...band.notes] : undefined,
  }
}

function toConstructionLoanPayload(
  input: ConstructionLoanInput | null | undefined,
): ConstructionLoanInputPayload | undefined {
  if (!input) {
    return undefined
  }

  const facilities = input.facilities?.map((facility) => ({
    name: facility.name,
    amount: toOptionalString(facility.amount),
    interest_rate: toOptionalString(facility.interestRate),
    periods_per_year:
      typeof facility.periodsPerYear === 'number'
        ? facility.periodsPerYear
        : undefined,
    capitalise_interest:
      typeof facility.capitaliseInterest === 'boolean'
        ? facility.capitaliseInterest
        : undefined,
    upfront_fee_pct: toOptionalString(facility.upfrontFeePct),
    exit_fee_pct: toOptionalString(facility.exitFeePct),
    reserve_months:
      typeof facility.reserveMonths === 'number'
        ? facility.reserveMonths
        : undefined,
    amortisation_months:
      typeof facility.amortisationMonths === 'number'
        ? facility.amortisationMonths
        : undefined,
  }))

  return {
    interest_rate: toOptionalString(input.interestRate),
    periods_per_year:
      typeof input.periodsPerYear === 'number'
        ? input.periodsPerYear
        : undefined,
    capitalise_interest:
      typeof input.capitaliseInterest === 'boolean'
        ? input.capitaliseInterest
        : undefined,
    facilities: facilities?.length ? facilities : undefined,
  }
}

function toPayload(
  request: FinanceFeasibilityRequest,
): FinanceFeasibilityRequestPayload {
  const { scenario } = request
  const projectId =
    typeof request.projectId === 'number'
      ? request.projectId
      : Number.parseInt(String(request.projectId), 10)
  if (!Number.isFinite(projectId)) {
    throw new Error('Finance feasibility projectId must be numeric')
  }
  return {
    project_id: projectId,
    project_name: request.projectName ?? undefined,
    fin_project_id: request.finProjectId,
    scenario: {
      name: scenario.name,
      description: scenario.description,
      currency: scenario.currency,
      is_primary: Boolean(scenario.isPrimary),
      cost_escalation: {
        amount: scenario.costEscalation.amount,
        base_period: scenario.costEscalation.basePeriod,
        series_name: scenario.costEscalation.seriesName,
        jurisdiction: scenario.costEscalation.jurisdiction,
        provider: scenario.costEscalation.provider ?? undefined,
      },
      cash_flow: {
        discount_rate: scenario.cashFlow.discountRate,
        cash_flows: [...scenario.cashFlow.cashFlows],
      },
      dscr: scenario.dscr
        ? {
            net_operating_incomes: [...scenario.dscr.netOperatingIncomes],
            debt_services: [...scenario.dscr.debtServices],
            period_labels: scenario.dscr.periodLabels?.length
              ? [...scenario.dscr.periodLabels]
              : undefined,
          }
        : undefined,
      capital_stack: scenario.capitalStack?.length
        ? scenario.capitalStack.map((slice) => ({
            name: slice.name,
            source_type: slice.sourceType,
            amount: slice.amount,
            rate: slice.rate ?? undefined,
            tranche_order:
              typeof slice.trancheOrder === 'number'
                ? slice.trancheOrder
                : undefined,
            metadata: slice.metadata ?? undefined,
          }))
        : undefined,
      drawdown_schedule: scenario.drawdownSchedule?.length
        ? scenario.drawdownSchedule.map((entry) => ({
            period: entry.period,
            equity_draw: entry.equityDraw ?? undefined,
            debt_draw: entry.debtDraw ?? undefined,
          }))
        : undefined,
      asset_mix: scenario.assetMix?.length
        ? scenario.assetMix.map(toAssetMixPayload)
        : undefined,
      construction_loan: toConstructionLoanPayload(scenario.constructionLoan),
      sensitivity_bands: scenario.sensitivityBands?.length
        ? scenario.sensitivityBands.map(toSensitivityBandPayload)
        : undefined,
    },
  }
}

function mapSnapshot(
  payload: CostIndexSnapshotPayload | null | undefined,
): CostIndexSnapshot | null {
  if (!payload) {
    return null
  }
  return {
    period: payload.period,
    value: payload.value,
    unit: payload.unit,
    source: payload.source ?? null,
    provider: payload.provider ?? null,
    methodology: payload.methodology ?? null,
  }
}

function mapCostIndex(
  payload: CostIndexProvenancePayload,
): CostIndexProvenance {
  return {
    seriesName: payload.series_name,
    jurisdiction: payload.jurisdiction,
    provider: payload.provider ?? null,
    basePeriod: payload.base_period,
    latestPeriod: payload.latest_period ?? null,
    scalar: payload.scalar ?? null,
    baseIndex: mapSnapshot(payload.base_index),
    latestIndex: mapSnapshot(payload.latest_index),
  }
}

function mapResult(payload: FinanceResultPayload): FinanceResultItem {
  return {
    name: payload.name,
    value: payload.value ?? null,
    unit: payload.unit ?? null,
    metadata: payload.metadata ? { ...payload.metadata } : {},
  }
}

function mapCapitalStackSlice(
  payload: CapitalStackSlicePayload,
): CapitalStackSlice {
  return {
    name: payload.name,
    sourceType: payload.source_type,
    category: payload.category,
    amount: payload.amount,
    share: payload.share,
    rate: payload.rate ?? null,
    trancheOrder: payload.tranche_order ?? null,
    metadata: payload.metadata ? { ...payload.metadata } : {},
  }
}

function mapCapitalStack(
  payload: CapitalStackSummaryPayload | null | undefined,
): CapitalStackSummary | null {
  if (!payload) {
    return null
  }
  return {
    currency: payload.currency,
    total: payload.total,
    equityTotal: payload.equity_total,
    debtTotal: payload.debt_total,
    otherTotal: payload.other_total,
    equityRatio: payload.equity_ratio ?? null,
    debtRatio: payload.debt_ratio ?? null,
    otherRatio: payload.other_ratio ?? null,
    loanToCost: payload.loan_to_cost ?? null,
    weightedAverageDebtRate: payload.weighted_average_debt_rate ?? null,
    slices: Array.isArray(payload.slices)
      ? payload.slices.map(mapCapitalStackSlice)
      : [],
  }
}

function mapDrawdownEntry(payload: DrawdownEntryPayload): DrawdownEntry {
  return {
    period: payload.period,
    equityDraw: payload.equity_draw,
    debtDraw: payload.debt_draw,
    totalDraw: payload.total_draw,
    cumulativeEquity: payload.cumulative_equity,
    cumulativeDebt: payload.cumulative_debt,
    outstandingDebt: payload.outstanding_debt,
  }
}

function mapDrawdown(
  payload: DrawdownSchedulePayload | null | undefined,
): DrawdownSchedule | null {
  if (!payload) {
    return null
  }
  return {
    currency: payload.currency,
    entries: Array.isArray(payload.entries)
      ? payload.entries.map(mapDrawdownEntry)
      : [],
    totalEquity: payload.total_equity,
    totalDebt: payload.total_debt,
    peakDebtBalance: payload.peak_debt_balance,
    finalDebtBalance: payload.final_debt_balance,
  }
}

function mapDscrEntry(payload: DscrEntryPayload): DscrEntry {
  return {
    period: payload.period,
    noi: payload.noi,
    debtService: payload.debt_service,
    dscr: payload.dscr ?? null,
    currency: payload.currency,
  }
}

function mapAssetSummary(
  payload: AssetFinancialSummaryPayload | null | undefined,
): AssetFinancialSummary | null {
  if (!payload) {
    return null
  }
  return {
    totalEstimatedRevenueSgd: payload.total_estimated_revenue_sgd ?? null,
    totalEstimatedCapexSgd: payload.total_estimated_capex_sgd ?? null,
    dominantRiskProfile: payload.dominant_risk_profile ?? null,
    notes: Array.isArray(payload.notes) ? [...payload.notes] : [],
  }
}

function mapAssetBreakdown(
  payload: FinanceAssetBreakdownPayload,
): FinanceAssetBreakdown {
  return {
    assetType: payload.asset_type,
    allocationPct: payload.allocation_pct ?? null,
    niaSqm: payload.nia_sqm ?? null,
    rentPsmMonth: payload.rent_psm_month ?? null,
    grossRentAnnualSgd: payload.gross_rent_annual_sgd ?? null,
    vacancyLossSgd: payload.vacancy_loss_sgd ?? null,
    effectiveGrossIncomeSgd: payload.effective_gross_income_sgd ?? null,
    operatingExpensesSgd: payload.operating_expenses_sgd ?? null,
    noiAnnualSgd: payload.noi_annual_sgd ?? null,
    estimatedCapexSgd: payload.estimated_capex_sgd ?? null,
    paybackYears: payload.payback_years ?? null,
    absorptionMonths: payload.absorption_months ?? null,
    riskLevel: payload.risk_level ?? null,
    heritagePremiumPct: payload.heritage_premium_pct ?? null,
    notes: Array.isArray(payload.notes) ? [...payload.notes] : [],
  }
}

function mapConstructionLoanConfig(
  payload: ConstructionLoanInputPayload | null | undefined,
): ConstructionLoanInput | null {
  if (!payload) {
    return null
  }
  const facilities = Array.isArray(payload.facilities)
    ? payload.facilities.map((facility) => ({
        name: facility.name,
        amount: facility.amount ?? null,
        interestRate: facility.interest_rate ?? null,
        periodsPerYear: facility.periods_per_year ?? null,
        capitaliseInterest: facility.capitalise_interest ?? true,
        upfrontFeePct: facility.upfront_fee_pct ?? null,
        exitFeePct: facility.exit_fee_pct ?? null,
        reserveMonths: facility.reserve_months ?? null,
        amortisationMonths: facility.amortisation_months ?? null,
        metadata: null,
      }))
    : null

  return {
    interestRate: payload.interest_rate ?? null,
    periodsPerYear: payload.periods_per_year ?? null,
    capitaliseInterest: payload.capitalise_interest ?? true,
    facilities,
  }
}

function mapConstructionLoanFacility(
  payload: ConstructionLoanFacilityPayload,
): ConstructionLoanInterestFacility {
  return {
    name: payload.name,
    amount: payload.amount ?? null,
    interestRate: payload.interest_rate ?? null,
    periodsPerYear: payload.periods_per_year ?? null,
    capitalised: Boolean(payload.capitalised ?? true),
    totalInterest: payload.total_interest ?? null,
    upfrontFee: payload.upfront_fee ?? null,
    exitFee: payload.exit_fee ?? null,
  }
}

function mapConstructionLoanInterest(
  payload: ConstructionLoanInterestPayload | null | undefined,
): ConstructionLoanInterest | null {
  if (!payload) {
    return null
  }
  const facilities = Array.isArray(payload.facilities)
    ? payload.facilities.map(mapConstructionLoanFacility)
    : []
  const entries = Array.isArray(payload.entries)
    ? payload.entries.map((entry) => ({
        period: entry.period,
        openingBalance: entry.opening_balance,
        closingBalance: entry.closing_balance,
        averageBalance: entry.average_balance,
        interestAccrued: entry.interest_accrued,
      }))
    : []
  return {
    currency: payload.currency,
    interestRate: payload.interest_rate ?? null,
    periodsPerYear: payload.periods_per_year ?? null,
    capitalised: Boolean(payload.capitalised ?? true),
    totalInterest: payload.total_interest ?? null,
    upfrontFeeTotal: payload.upfront_fee_total ?? null,
    exitFeeTotal: payload.exit_fee_total ?? null,
    facilities,
    entries,
  }
}

function mapSensitivityOutcome(
  payload: FinanceSensitivityOutcomePayload,
): FinanceSensitivityOutcome {
  return {
    parameter: payload.parameter,
    scenario: payload.scenario,
    deltaLabel: payload.delta_label ?? null,
    deltaValue: payload.delta_value ?? payload.delta_label ?? null,
    npv: payload.npv ?? null,
    irr: payload.irr ?? null,
    escalatedCost: payload.escalated_cost ?? null,
    totalInterest: payload.total_interest ?? null,
    notes: Array.isArray(payload.notes) ? [...payload.notes] : [],
  }
}

function mapSensitivityBand(
  payload: SensitivityBandPayload,
): SensitivityBandInput {
  return {
    parameter: payload.parameter,
    low: payload.low ?? undefined,
    base: payload.base ?? undefined,
    high: payload.high ?? undefined,
    notes: Array.isArray(payload.notes) ? [...payload.notes] : [],
  }
}

function mapJobStatus(payload: FinanceJobStatusPayload): FinanceJobStatus {
  return {
    scenarioId: payload.scenario_id,
    taskId: payload.task_id ?? null,
    status: payload.status,
    backend: payload.backend ?? null,
    queuedAt: payload.queued_at ?? null,
  }
}

function mapResponse(
  payload: FinanceFeasibilityResponsePayload,
): FinanceScenarioSummary {
  const resultsSource = Array.isArray(payload.results) ? payload.results : []
  const dscrTimelineSource = Array.isArray(payload.dscr_timeline)
    ? payload.dscr_timeline
    : []
  const assetBreakdownSource = Array.isArray(payload.asset_breakdowns)
    ? payload.asset_breakdowns
    : []
  const sensitivitySource = Array.isArray(payload.sensitivity_results)
    ? payload.sensitivity_results
    : []
  const jobSource = Array.isArray(payload.sensitivity_jobs)
    ? payload.sensitivity_jobs
    : []
  const bandSource = Array.isArray(payload.sensitivity_bands)
    ? payload.sensitivity_bands
    : []

  const rawProjectId = payload.project_id
  const numericProjectId = Number(rawProjectId)
  const projectId =
    typeof rawProjectId === 'number'
      ? rawProjectId
      : Number.isFinite(numericProjectId)
        ? numericProjectId
        : rawProjectId

  const rawFinProjectId = payload.fin_project_id
  const finProjectId =
    typeof rawFinProjectId === 'number'
      ? rawFinProjectId
      : Number.isFinite(Number(rawFinProjectId))
        ? Number(rawFinProjectId)
        : null

  const assetMixSummary = mapAssetSummary(payload.asset_mix_summary)
  const assetBreakdowns = assetBreakdownSource.map(mapAssetBreakdown)
  const constructionLoanInterest = mapConstructionLoanInterest(
    payload.construction_loan_interest,
  )
  const constructionLoan = mapConstructionLoanConfig(payload.construction_loan)
  const sensitivityResults = sensitivitySource.map(mapSensitivityOutcome)
  const sensitivityJobs = jobSource.map(mapJobStatus)
  const sensitivityBands = bandSource.map(mapSensitivityBand)

  return {
    scenarioId: payload.scenario_id,
    projectId,
    finProjectId,
    scenarioName: payload.scenario_name,
    currency: payload.currency,
    escalatedCost: payload.escalated_cost,
    costIndex: mapCostIndex(payload.cost_index),
    results: resultsSource.map(mapResult),
    dscrTimeline: dscrTimelineSource.map(mapDscrEntry),
    capitalStack: mapCapitalStack(payload.capital_stack ?? null),
    drawdownSchedule: mapDrawdown(payload.drawdown_schedule ?? null),
    assetMixSummary,
    assetBreakdowns,
    constructionLoanInterest,
    constructionLoan,
    sensitivityResults,
    sensitivityJobs,
    sensitivityBands,
    isPrimary: payload.is_primary ?? undefined,
    isPrivate: payload.is_private ?? undefined,
    updatedAt: payload.updated_at ?? null,
  }
}

const FINANCE_FALLBACK_SUMMARY: FinanceScenarioSummary = {
  scenarioId: 0,
  projectId: 0,
  finProjectId: 0,
  scenarioName: 'Offline Feasibility Scenario',
  currency: 'SGD',
  escalatedCost: '24850000.00',
  costIndex: {
    seriesName: 'construction_all_in',
    jurisdiction: 'SG',
    provider: 'Public',
    basePeriod: '2024-Q1',
    latestPeriod: '2024-Q4',
    scalar: '1.1200',
    baseIndex: {
      period: '2024-Q1',
      value: '100',
      unit: 'index',
      source: 'BCA',
      provider: 'BCA',
      methodology: null,
    },
    latestIndex: {
      period: '2024-Q4',
      value: '112',
      unit: 'index',
      source: 'BCA',
      provider: 'BCA',
      methodology: null,
    },
  },
  results: [
    {
      name: 'NPV',
      value: '1850000.00',
      unit: 'currency',
      metadata: { currency: 'SGD' },
    },
    {
      name: 'IRR',
      value: '0.125',
      unit: 'ratio',
      metadata: { format: 'percentage' },
    },
    {
      name: 'Equity Multiple',
      value: '1.80',
      unit: 'multiple',
      metadata: {},
    },
  ],
  dscrTimeline: [
    {
      period: 'Year 1',
      noi: '5200000.00',
      debtService: '4300000.00',
      dscr: '1.21',
      currency: 'SGD',
    },
    {
      period: 'Year 2',
      noi: '5600000.00',
      debtService: '4300000.00',
      dscr: '1.30',
      currency: 'SGD',
    },
    {
      period: 'Year 3',
      noi: '5900000.00',
      debtService: '4300000.00',
      dscr: '1.37',
      currency: 'SGD',
    },
  ],
  capitalStack: {
    currency: 'SGD',
    total: '24850000.00',
    equityTotal: '9940000.00',
    debtTotal: '14910000.00',
    otherTotal: '0.00',
    equityRatio: '0.40',
    debtRatio: '0.60',
    otherRatio: '0.00',
    loanToCost: '0.60',
    weightedAverageDebtRate: '0.043',
    slices: [
      {
        name: 'Sponsor Equity',
        sourceType: 'equity',
        category: 'equity',
        amount: '7455000.00',
        share: '0.30',
        rate: null,
        trancheOrder: 1,
        metadata: {},
      },
      {
        name: 'Co-invest Equity',
        sourceType: 'equity',
        category: 'equity',
        amount: '2485000.00',
        share: '0.10',
        rate: null,
        trancheOrder: 2,
        metadata: {},
      },
      {
        name: 'Senior Debt',
        sourceType: 'debt',
        category: 'debt',
        amount: '14910000.00',
        share: '0.60',
        rate: '0.043',
        trancheOrder: 3,
        metadata: {},
      },
    ],
  },
  drawdownSchedule: {
    currency: 'SGD',
    entries: [
      {
        period: 'Q1',
        equityDraw: '3727500.00',
        debtDraw: '0.00',
        totalDraw: '3727500.00',
        cumulativeEquity: '3727500.00',
        cumulativeDebt: '0.00',
        outstandingDebt: '0.00',
      },
      {
        period: 'Q2',
        equityDraw: '3727500.00',
        debtDraw: '4970000.00',
        totalDraw: '8697500.00',
        cumulativeEquity: '7455000.00',
        cumulativeDebt: '4970000.00',
        outstandingDebt: '4970000.00',
      },
      {
        period: 'Q3',
        equityDraw: '2485000.00',
        debtDraw: '4960000.00',
        totalDraw: '7445000.00',
        cumulativeEquity: '9940000.00',
        cumulativeDebt: '9930000.00',
        outstandingDebt: '9930000.00',
      },
      {
        period: 'Q4',
        equityDraw: '0.00',
        debtDraw: '4980000.00',
        totalDraw: '4980000.00',
        cumulativeEquity: '9940000.00',
        cumulativeDebt: '14910000.00',
        outstandingDebt: '14910000.00',
      },
    ],
    totalEquity: '9940000.00',
    totalDebt: '14910000.00',
    peakDebtBalance: '14910000.00',
    finalDebtBalance: '14910000.00',
  },
  assetMixSummary: null,
  assetBreakdowns: [],
  constructionLoanInterest: null,
  constructionLoan: null,
  sensitivityResults: [],
  sensitivityJobs: [],
  sensitivityBands: [],
  isPrimary: true,
  isPrivate: false,
  updatedAt: null,
}

function cloneFinanceSummary(
  summary: FinanceScenarioSummary,
): FinanceScenarioSummary {
  return {
    ...summary,
    costIndex: {
      ...summary.costIndex,
      baseIndex: summary.costIndex.baseIndex
        ? { ...summary.costIndex.baseIndex }
        : null,
      latestIndex: summary.costIndex.latestIndex
        ? { ...summary.costIndex.latestIndex }
        : null,
    },
    results: summary.results.map((item) => ({
      ...item,
      metadata: { ...item.metadata },
    })),
    dscrTimeline: summary.dscrTimeline.map((entry) => ({ ...entry })),
    capitalStack: summary.capitalStack
      ? {
          ...summary.capitalStack,
          slices: summary.capitalStack.slices.map((slice) => ({
            ...slice,
            metadata: { ...slice.metadata },
          })),
        }
      : null,
    drawdownSchedule: summary.drawdownSchedule
      ? {
          ...summary.drawdownSchedule,
          entries: summary.drawdownSchedule.entries.map((entry) => ({
            ...entry,
          })),
        }
      : null,
    assetMixSummary: summary.assetMixSummary
      ? {
          ...summary.assetMixSummary,
          notes: [...summary.assetMixSummary.notes],
        }
      : null,
    assetBreakdowns: summary.assetBreakdowns.map((entry) => ({
      ...entry,
      notes: [...entry.notes],
    })),
    constructionLoanInterest: summary.constructionLoanInterest
      ? {
          ...summary.constructionLoanInterest,
          facilities: summary.constructionLoanInterest.facilities.map(
            (facility) => ({ ...facility }),
          ),
          entries: summary.constructionLoanInterest.entries.map((entry) => ({
            ...entry,
          })),
        }
      : null,
    constructionLoan: summary.constructionLoan
      ? {
          ...summary.constructionLoan,
          facilities: summary.constructionLoan.facilities
            ? summary.constructionLoan.facilities.map((facility) => ({
                ...facility,
              }))
            : null,
        }
      : null,
    sensitivityResults: summary.sensitivityResults.map((entry) => ({
      ...entry,
      notes: [...entry.notes],
    })),
    sensitivityJobs: summary.sensitivityJobs.map((job) => ({ ...job })),
  }
}

function createFinanceFallbackSummary(
  request: FinanceFeasibilityRequest,
): FinanceScenarioSummary {
  const fallback = cloneFinanceSummary(FINANCE_FALLBACK_SUMMARY)
  // Ensure locally-created fallback scenarios do not collide with the static
  // offline summary (scenarioId=0) used by listFinanceScenarios fallback.
  fallback.scenarioId = -Date.now()
  fallback.isPrimary = true
  if (request.projectId !== undefined && request.projectId !== null) {
    fallback.projectId = request.projectId as typeof fallback.projectId
  }
  if (typeof request.finProjectId === 'number') {
    fallback.finProjectId = request.finProjectId
  }
  fallback.scenarioName = request.scenario.name?.trim() || fallback.scenarioName
  const currency = request.scenario.currency?.trim() || fallback.currency
  fallback.currency = currency
  fallback.costIndex = {
    ...fallback.costIndex,
  }
  if (fallback.costIndex.baseIndex) {
    fallback.costIndex.baseIndex = {
      ...fallback.costIndex.baseIndex,
    }
  }
  if (fallback.costIndex.latestIndex) {
    fallback.costIndex.latestIndex = {
      ...fallback.costIndex.latestIndex,
    }
  }
  fallback.results = fallback.results.map((item) => {
    const metadata = { ...item.metadata }
    if (item.name.toLowerCase().includes('npv')) {
      metadata.currency = currency
    }
    return {
      ...item,
      metadata,
    }
  })
  fallback.dscrTimeline = fallback.dscrTimeline.map((entry) => ({
    ...entry,
    currency,
  }))
  if (fallback.capitalStack) {
    fallback.capitalStack = {
      ...fallback.capitalStack,
      currency,
      slices: fallback.capitalStack.slices.map((slice) => ({
        ...slice,
        metadata: { ...slice.metadata },
      })),
    }
  }
  if (fallback.drawdownSchedule) {
    fallback.drawdownSchedule = {
      ...fallback.drawdownSchedule,
      currency,
      entries: fallback.drawdownSchedule.entries.map((entry) => ({
        ...entry,
      })),
    }
  }
  return fallback
}

export interface FinanceFeasibilityOptions {
  signal?: AbortSignal
  /**
   * Optional client-side timeout for API calls.
   * When reached, the request aborts and callers may fall back to offline data.
   */
  timeoutMs?: number
}

export async function runFinanceFeasibility(
  request: FinanceFeasibilityRequest,
  options: FinanceFeasibilityOptions = {},
): Promise<FinanceScenarioSummary> {
  const headers = applyIdentityHeaders({
    'Content-Type': 'application/json',
  })

  try {
    const response = await fetch(
      buildUrl('api/v1/finance/feasibility', apiBaseUrl),
      {
        method: 'POST',
        headers,
        body: JSON.stringify(toPayload(request)),
        signal: options.signal,
      },
    )

    if (!response.ok) {
      const message = await response.text()
      throw new Error(
        message ||
          `Finance feasibility request failed with status ${response.status}`,
      )
    }

    const payload = (await response.json()) as FinanceFeasibilityResponsePayload
    return mapResponse(payload)
  } catch (error) {
    if (error instanceof DOMException && error.name === 'AbortError') {
      throw error
    }
    if (error instanceof TypeError) {
      console.warn(
        '[finance] feasibility request failed, using offline fallback data',
        error,
      )
      return createFinanceFallbackSummary(request)
    }
    throw error
  }
}

export function findResult(
  summary: FinanceScenarioSummary,
  name: string,
): FinanceResultItem | undefined {
  return summary.results.find((result) => result.name === name)
}

export interface FinanceScenarioListParams {
  projectId?: number | string
  finProjectId?: number
}

function scaleFixed(
  value: string | null | undefined,
  multiplier: number,
): string {
  if (typeof value !== 'string') return '0.00'
  const parsed = Number(value)
  if (!Number.isFinite(parsed)) return value
  return (parsed * multiplier).toFixed(2)
}

function setResultValue(
  summary: FinanceScenarioSummary,
  key: string,
  value: string,
) {
  const target = key.trim().toLowerCase()
  const match = summary.results.find(
    (result) => result.name.trim().toLowerCase() === target,
  )
  if (match) {
    match.value = value
    return
  }
  summary.results.push({
    name: key,
    value,
    unit: 'currency',
    metadata: { currency: summary.currency ?? 'SGD' },
  })
}

function createFinanceFallbackScenarioList(
  params: FinanceScenarioListParams,
): FinanceScenarioSummary[] {
  const base = cloneFinanceSummary(FINANCE_FALLBACK_SUMMARY)
  if (params.projectId !== undefined && params.projectId !== null) {
    base.projectId = params.projectId as typeof base.projectId
  }
  if (typeof params.finProjectId === 'number') {
    base.finProjectId = params.finProjectId
  }

  const scenarioA = cloneFinanceSummary(base)
  scenarioA.scenarioId = 0
  scenarioA.scenarioName = 'Scenario A'
  scenarioA.isPrimary = true
  scenarioA.escalatedCost = scaleFixed(base.escalatedCost, 1)
  setResultValue(scenarioA, 'NPV', '375863.00')
  setResultValue(scenarioA, 'IRR', '0.0688')

  const scenarioB = cloneFinanceSummary(base)
  scenarioB.scenarioId = -1
  scenarioB.scenarioName = 'Scenario B'
  scenarioB.isPrimary = false
  scenarioB.escalatedCost = scaleFixed(base.escalatedCost, 1.045)
  setResultValue(scenarioB, 'NPV', '1270733.00')
  setResultValue(scenarioB, 'IRR', '0.1091')

  const scenarioC = cloneFinanceSummary(base)
  scenarioC.scenarioId = -2
  scenarioC.scenarioName = 'Scenario C'
  scenarioC.isPrimary = false
  scenarioC.escalatedCost = scaleFixed(base.escalatedCost, 0.955)
  setResultValue(scenarioC, 'NPV', '4160673.00')
  setResultValue(scenarioC, 'IRR', '-0.0745')

  const variants = [
    { scenario: scenarioA, multiplier: 1 },
    { scenario: scenarioB, multiplier: 1.045 },
    { scenario: scenarioC, multiplier: 0.955 },
  ]

  for (const { scenario, multiplier } of variants) {
    if (scenario.capitalStack) {
      scenario.capitalStack.total = scaleFixed(
        scenario.capitalStack.total,
        multiplier,
      )
      scenario.capitalStack.equityTotal = scaleFixed(
        scenario.capitalStack.equityTotal,
        multiplier,
      )
      scenario.capitalStack.debtTotal = scaleFixed(
        scenario.capitalStack.debtTotal,
        multiplier,
      )
      scenario.capitalStack.otherTotal = scaleFixed(
        scenario.capitalStack.otherTotal,
        multiplier,
      )
      scenario.capitalStack.slices = scenario.capitalStack.slices.map(
        (slice) => ({
          ...slice,
          amount: scaleFixed(slice.amount, multiplier),
        }),
      )
    }
    if (scenario.drawdownSchedule) {
      scenario.drawdownSchedule.totalEquity = scaleFixed(
        scenario.drawdownSchedule.totalEquity,
        multiplier,
      )
      scenario.drawdownSchedule.totalDebt = scaleFixed(
        scenario.drawdownSchedule.totalDebt,
        multiplier,
      )
      scenario.drawdownSchedule.peakDebtBalance = scaleFixed(
        scenario.drawdownSchedule.peakDebtBalance,
        multiplier,
      )
      scenario.drawdownSchedule.finalDebtBalance = scaleFixed(
        scenario.drawdownSchedule.finalDebtBalance,
        multiplier,
      )
      scenario.drawdownSchedule.entries = scenario.drawdownSchedule.entries.map(
        (entry) => ({
          ...entry,
          equityDraw: scaleFixed(entry.equityDraw, multiplier),
          debtDraw: scaleFixed(entry.debtDraw, multiplier),
          totalDraw: scaleFixed(entry.totalDraw, multiplier),
          cumulativeEquity: scaleFixed(entry.cumulativeEquity, multiplier),
          cumulativeDebt: scaleFixed(entry.cumulativeDebt, multiplier),
          outstandingDebt: scaleFixed(entry.outstandingDebt, multiplier),
        }),
      )
    }
  }

  return [scenarioA, scenarioB, scenarioC]
}

export async function listFinanceScenarios(
  params: FinanceScenarioListParams = {},
  options: FinanceFeasibilityOptions = {},
): Promise<FinanceScenarioSummary[]> {
  const headers = applyIdentityHeaders({
    'Content-Type': 'application/json',
  })

  const timeoutMs =
    typeof options.timeoutMs === 'number' && options.timeoutMs > 0
      ? options.timeoutMs
      : 2500
  const timeoutController = new AbortController()
  const timeoutId = setTimeout(() => {
    timeoutController.abort()
  }, timeoutMs)

  let composedSignal: AbortSignal | undefined
  const incomingSignal = options.signal
  const timeoutSignal = timeoutController.signal
  if (incomingSignal) {
    if (typeof AbortSignal !== 'undefined' && 'any' in AbortSignal) {
      composedSignal = (
        AbortSignal as unknown as { any: (s: AbortSignal[]) => AbortSignal }
      ).any([incomingSignal, timeoutSignal])
    } else {
      const bridge = new AbortController()
      const abortBridge = () => bridge.abort()
      incomingSignal.addEventListener('abort', abortBridge, { once: true })
      timeoutSignal.addEventListener('abort', abortBridge, { once: true })
      composedSignal = bridge.signal
    }
  } else {
    composedSignal = timeoutSignal
  }

  const query = new URLSearchParams()
  if (typeof params.projectId === 'number') {
    query.set('project_id', params.projectId.toString())
  } else if (typeof params.projectId === 'string' && params.projectId.trim()) {
    query.set('project_id', params.projectId.trim())
  }
  if (typeof params.finProjectId === 'number') {
    query.set('fin_project_id', params.finProjectId.toString())
  }

  const querySuffix = query.toString()
  try {
    const response = await fetch(
      buildUrl(
        `api/v1/finance/scenarios${querySuffix ? `?${querySuffix}` : ''}`,
        apiBaseUrl,
      ),
      {
        method: 'GET',
        headers,
        signal: composedSignal,
      },
    )

    if (!response.ok) {
      const message = await response.text()
      if (response.status >= 500) {
        console.warn(
          `[finance] scenario list request failed (server ${response.status}), using offline fallback data`,
          message,
        )
        return createFinanceFallbackScenarioList(params)
      }
      throw new Error(
        message ||
          `Finance scenario list request failed with status ${response.status}`,
      )
    }

    const payload =
      (await response.json()) as FinanceFeasibilityResponsePayload[]
    return Array.isArray(payload) ? payload.map(mapResponse) : []
  } catch (error) {
    if (error instanceof DOMException && error.name === 'AbortError') {
      const timedOut =
        timeoutController.signal.aborted && !options.signal?.aborted
      if (!timedOut) {
        throw error
      }
      console.warn(
        `[finance] scenario list request timed out after ${timeoutMs}ms, using offline fallback data`,
      )
      return createFinanceFallbackScenarioList(params)
    }
    // Use fallback data for network errors (TypeError) or API auth errors (401/403)
    const isNetworkError = error instanceof TypeError
    const isAuthError =
      error instanceof Error &&
      (error.message.includes('401') ||
        error.message.includes('403') ||
        error.message.includes('restricted') ||
        error.message.includes('owner'))
    if (isNetworkError || isAuthError) {
      console.warn(
        `[finance] scenario list request failed (${isNetworkError ? 'network' : 'auth'}), using offline fallback data`,
        error,
      )
      return createFinanceFallbackScenarioList(params)
    }
    throw error
  } finally {
    clearTimeout(timeoutId)
  }
}

export async function updateConstructionLoan(
  scenarioId: number,
  input: ConstructionLoanInput,
  options: FinanceFeasibilityOptions = {},
): Promise<FinanceScenarioSummary> {
  if (scenarioId == null || Number.isNaN(Number(scenarioId))) {
    throw new Error('scenarioId is required to update the construction loan')
  }

  const headers = applyIdentityHeaders({
    'Content-Type': 'application/json',
  })

  const loanPayload = toConstructionLoanPayload(input)
  if (!loanPayload) {
    throw new Error('constructionLoan configuration is required')
  }

  const body: ConstructionLoanUpdateRequestPayload = {
    construction_loan: loanPayload,
  }

  const response = await fetch(
    buildUrl(
      `api/v1/finance/scenarios/${scenarioId}/construction-loan`,
      apiBaseUrl,
    ),
    {
      method: 'PATCH',
      headers,
      body: JSON.stringify(body),
      signal: options.signal,
    },
  )

  if (!response.ok) {
    const message = await response.text()
    throw new Error(
      message ||
        `Construction loan update failed with status ${response.status}`,
    )
  }

  const payload = (await response.json()) as FinanceFeasibilityResponsePayload
  return mapResponse(payload)
}

export async function updateFinanceScenario(
  scenarioId: number,
  input: FinanceScenarioUpdateInput,
  options: FinanceFeasibilityOptions = {},
): Promise<FinanceScenarioSummary> {
  if (!Number.isFinite(Number(scenarioId))) {
    throw new Error('scenarioId is required to update a finance scenario')
  }
  const headers = applyIdentityHeaders({
    'Content-Type': 'application/json',
  })
  const body: Record<string, unknown> = {}
  if (input.scenarioName !== undefined) {
    body['scenario_name'] = input.scenarioName
  }
  if (input.description !== undefined) {
    body['description'] = input.description
  }
  if (input.isPrimary !== undefined) {
    body['is_primary'] = input.isPrimary
  }
  const response = await fetch(
    buildUrl(`api/v1/finance/scenarios/${scenarioId}`, apiBaseUrl),
    {
      method: 'PATCH',
      headers,
      body: JSON.stringify(body),
      signal: options.signal,
    },
  )
  if (!response.ok) {
    const message = await response.text()
    throw new Error(
      message ||
        `Finance scenario update failed with status ${response.status}`,
    )
  }
  const payload = (await response.json()) as FinanceFeasibilityResponsePayload
  return mapResponse(payload)
}

export async function deleteFinanceScenario(
  scenarioId: number,
  options: FinanceFeasibilityOptions = {},
): Promise<void> {
  if (!Number.isFinite(Number(scenarioId))) {
    throw new Error('scenarioId is required to delete a finance scenario')
  }
  const headers = applyIdentityHeaders({
    'Content-Type': 'application/json',
  })
  const response = await fetch(
    buildUrl(`api/v1/finance/scenarios/${scenarioId}`, apiBaseUrl),
    {
      method: 'DELETE',
      headers,
      signal: options.signal,
    },
  )
  if (!response.ok) {
    const message = await response.text()
    throw new Error(
      message ||
        `Finance scenario delete failed with status ${response.status}`,
    )
  }
}

export async function exportFinanceScenarioCsv(
  scenarioId: number,
  options: FinanceFeasibilityOptions = {},
): Promise<Blob> {
  if (!Number.isFinite(Number(scenarioId))) {
    throw new Error('scenarioId is required to export a finance scenario')
  }
  const headers = applyIdentityHeaders({})
  const url = buildUrl(
    `api/v1/finance/export?scenario_id=${scenarioId}`,
    apiBaseUrl,
  )
  const response = await fetch(url, {
    method: 'GET',
    headers,
    signal: options.signal,
  })
  if (!response.ok) {
    const message = await response.text()
    throw new Error(
      message ||
        `Finance scenario export failed with status ${response.status}`,
    )
  }
  return await response.blob()
}

export async function runScenarioSensitivity(
  scenarioId: number,
  bands: SensitivityBandInput[],
  options: FinanceFeasibilityOptions = {},
): Promise<FinanceScenarioSummary> {
  if (!Number.isFinite(Number(scenarioId))) {
    throw new Error('scenarioId is required to rerun sensitivity analysis')
  }
  if (!Array.isArray(bands) || bands.length === 0) {
    throw new Error('At least one sensitivity band must be supplied')
  }

  const headers = applyIdentityHeaders({
    'Content-Type': 'application/json',
  })

  const body = {
    sensitivity_bands: bands.map(toSensitivityBandPayload),
  }

  const response = await fetch(
    buildUrl(`api/v1/finance/scenarios/${scenarioId}/sensitivity`, apiBaseUrl),
    {
      method: 'POST',
      headers,
      body: JSON.stringify(body),
      signal: options.signal,
    },
  )

  if (!response.ok) {
    const message = await response.text()
    throw new Error(
      message || `Sensitivity rerun failed with status ${response.status}`,
    )
  }

  const payload = (await response.json()) as FinanceFeasibilityResponsePayload
  return mapResponse(payload)
}
