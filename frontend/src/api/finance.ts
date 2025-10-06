const rawApiBaseUrl =
  import.meta.env.VITE_API_BASE_URL ??
  import.meta.env.VITE_API_URL ??
  import.meta.env.VITE_API_BASE ??
  null

function normaliseBaseUrl(value: string | undefined | null): string {
  if (typeof value !== 'string') {
    return '/'
  }
  const trimmed = value.trim()
  return trimmed === '' ? '/' : trimmed
}

function resolveDefaultRole(): string | null {
  const candidates = [
    import.meta.env.VITE_API_ROLE,
    typeof window !== 'undefined'
      ? window.localStorage.getItem('app:api-role') ?? undefined
      : undefined,
    'admin',
  ] as Array<string | undefined>

  const candidate = candidates.find(
    (value) => typeof value === 'string' && value.trim().length > 0,
  )

  return candidate ? candidate.trim() : null
}

function buildUrl(path: string, base: string): string {
  if (/^https?:/i.test(path)) {
    return path
  }

  const trimmed = path.startsWith('/') ? path.slice(1) : path
  const root = normaliseBaseUrl(base)

  if (/^https?:/i.test(root)) {
    const normalisedRoot = root.endsWith('/') ? root : `${root}/`
    return new URL(trimmed, normalisedRoot).toString()
  }

  const normalisedRoot = root.endsWith('/') ? root : `${root}/`
  return `${normalisedRoot}${trimmed}`
}

const apiBaseUrl = normaliseBaseUrl(rawApiBaseUrl)

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
}

export interface FinanceFeasibilityRequest {
  projectId: number
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

export interface FinanceScenarioSummary {
  scenarioId: number
  projectId: number
  finProjectId: number
  scenarioName: string
  currency: string
  escalatedCost: string
  costIndex: CostIndexProvenance
  results: FinanceResultItem[]
  dscrTimeline: DscrEntry[]
  capitalStack: CapitalStackSummary | null
  drawdownSchedule: DrawdownSchedule | null
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
  }
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
}

function toPayload(
  request: FinanceFeasibilityRequest,
): FinanceFeasibilityRequestPayload {
  const { scenario } = request
  return {
    project_id: request.projectId,
    project_name: request.projectName,
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
              typeof slice.trancheOrder === 'number' ? slice.trancheOrder : undefined,
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

function mapResponse(
  payload: FinanceFeasibilityResponsePayload,
): FinanceScenarioSummary {
  const resultsSource = Array.isArray(payload.results) ? payload.results : []
  const dscrTimelineSource = Array.isArray(payload.dscr_timeline)
    ? payload.dscr_timeline
    : []

  return {
    scenarioId: payload.scenario_id,
    projectId: payload.project_id,
    finProjectId: payload.fin_project_id,
    scenarioName: payload.scenario_name,
    currency: payload.currency,
    escalatedCost: payload.escalated_cost,
    costIndex: mapCostIndex(payload.cost_index),
    results: resultsSource.map(mapResult),
    dscrTimeline: dscrTimelineSource.map(mapDscrEntry),
    capitalStack: mapCapitalStack(payload.capital_stack ?? null),
    drawdownSchedule: mapDrawdown(payload.drawdown_schedule ?? null),
  }
}

export interface FinanceFeasibilityOptions {
  signal?: AbortSignal
}

export async function runFinanceFeasibility(
  request: FinanceFeasibilityRequest,
  options: FinanceFeasibilityOptions = {},
): Promise<FinanceScenarioSummary> {
  const headers: Record<string, string> = {
    'Content-Type': 'application/json',
  }

  const defaultRole = resolveDefaultRole()
  if (defaultRole) {
    headers['X-Role'] = defaultRole
  }

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
}

export function findResult(
  summary: FinanceScenarioSummary,
  name: string,
): FinanceResultItem | undefined {
  return summary.results.find((result) => result.name === name)
}

export interface FinanceScenarioListParams {
  projectId?: number
  finProjectId?: number
}

export async function listFinanceScenarios(
  params: FinanceScenarioListParams = {},
  options: FinanceFeasibilityOptions = {},
): Promise<FinanceScenarioSummary[]> {
  const headers: Record<string, string> = {
    'Content-Type': 'application/json',
  }

  const defaultRole = resolveDefaultRole()
  if (defaultRole) {
    headers['X-Role'] = defaultRole
  }

  const query = new URLSearchParams()
  if (typeof params.projectId === 'number') {
    query.set('project_id', params.projectId.toString())
  }
  if (typeof params.finProjectId === 'number') {
    query.set('fin_project_id', params.finProjectId.toString())
  }

  const querySuffix = query.toString()
  const response = await fetch(
    buildUrl(
      `api/v1/finance/scenarios${querySuffix ? `?${querySuffix}` : ''}`,
      apiBaseUrl,
    ),
    {
      method: 'GET',
      headers,
      signal: options.signal,
    },
  )

  if (!response.ok) {
    const message = await response.text()
    throw new Error(
      message ||
        `Finance scenario list request failed with status ${response.status}`,
    )
  }

  const payload = (await response.json()) as FinanceFeasibilityResponsePayload[]
  return Array.isArray(payload) ? payload.map(mapResponse) : []
}
