import { buildSimpleUrl, toNumberOrNull } from './utils'

const buildUrl = buildSimpleUrl

// Phase types matching backend PhaseType enum
export type PhaseType =
  | 'demolition'
  | 'site_preparation'
  | 'foundation'
  | 'structure'
  | 'envelope'
  | 'mep_rough_in'
  | 'interior_fit_out'
  | 'external_works'
  | 'commissioning'
  | 'handover'
  | 'heritage_restoration'
  | 'tenant_renovation'
  | 'facade_upgrade'
  | 'services_upgrade'
  | 'mixed_use_integration'

export type PhaseStatus =
  | 'not_started'
  | 'planning'
  | 'in_progress'
  | 'on_hold'
  | 'completed'
  | 'cancelled'

export type DependencyType =
  | 'finish_to_start'
  | 'start_to_start'
  | 'finish_to_finish'
  | 'start_to_finish'

export type HeritageClassification =
  | 'national_monument'
  | 'conservation_building'
  | 'heritage_site'
  | 'traditional_area'
  | 'none'

export type OccupancyStatus =
  | 'vacant'
  | 'partially_occupied'
  | 'fully_occupied'
  | 'mixed_use_active'

export interface DevelopmentPhase {
  id: number
  projectId: string
  name: string
  phaseType: PhaseType
  status: PhaseStatus
  sequenceOrder: number
  plannedStartDate: string | null
  plannedEndDate: string | null
  actualStartDate: string | null
  actualEndDate: string | null
  budgetAmount: number | null
  actualCostAmount: number | null
  description: string | null
  heritageClassification: HeritageClassification
  heritageApprovalRequired: boolean
  heritageApprovalStatus: string | null
  occupancyStatus: OccupancyStatus
  tenantCoordinationRequired: boolean
  createdAt: string
  updatedAt: string
}

export interface PhaseDependency {
  id: number
  predecessorPhaseId: number
  successorPhaseId: number
  dependencyType: DependencyType
  lagDays: number
}

export interface GanttTask {
  id: string
  name: string
  phaseType: PhaseType
  status: PhaseStatus
  startDate: string
  endDate: string
  duration: number
  progress: number
  dependencies: string[]
  isCritical: boolean
  isHeritage: boolean
  hasTenantCoordination: boolean
  color: string
  budgetAmount: number | null
  actualCostAmount: number | null
}

export interface GanttChart {
  projectId: string
  projectName: string
  generatedAt: string
  tasks: GanttTask[]
  projectStartDate: string | null
  projectEndDate: string | null
  totalDuration: number
  criticalPathDuration: number
}

export interface CriticalPathResult {
  projectId: string
  criticalPath: string[]
  totalDuration: number
  criticalPhases: Array<{
    phaseId: number
    name: string
    earlyStart: number
    earlyFinish: number
    lateStart: number
    lateFinish: number
    float: number
  }>
  nonCriticalPhases: Array<{
    phaseId: number
    name: string
    float: number
  }>
}

export interface HeritageTracker {
  projectId: string
  heritageClassification: HeritageClassification
  overallApprovalStatus: string
  phases: Array<{
    phaseId: number
    name: string
    heritageClassification: HeritageClassification
    approvalRequired: boolean
    approvalStatus: string | null
    specialConsiderations: string[]
  }>
  requiredApprovals: string[]
  preservationRisks: string[]
  recommendations: string[]
}

export interface TenantRelocation {
  id: number
  phaseId: number
  tenantName: string
  currentUnit: string
  relocationType: string
  status: string
  notificationDate: string | null
  plannedMoveDate: string | null
  actualMoveDate: string | null
  temporaryLocation: string | null
  compensationAmount: number | null
  notes: string | null
}

export interface TenantCoordinationSummary {
  projectId: string
  totalTenants: number
  statusBreakdown: Record<string, number>
  relocations: TenantRelocation[]
  upcomingMoves: TenantRelocation[]
  overdueNotifications: TenantRelocation[]
  timeline: Array<{
    date: string
    event: string
    tenantName: string
    status: string
  }>
  warnings: string[]
}

function mapPhase(payload: Record<string, unknown>): DevelopmentPhase {
  return {
    id: Number(payload.id ?? 0),
    projectId: String(payload.project_id ?? ''),
    name: String(payload.name ?? ''),
    phaseType: String(payload.phase_type ?? 'site_preparation') as PhaseType,
    status: String(payload.status ?? 'not_started') as PhaseStatus,
    sequenceOrder: Number(payload.sequence_order ?? 0),
    plannedStartDate:
      typeof payload.planned_start_date === 'string'
        ? payload.planned_start_date
        : null,
    plannedEndDate:
      typeof payload.planned_end_date === 'string'
        ? payload.planned_end_date
        : null,
    actualStartDate:
      typeof payload.actual_start_date === 'string'
        ? payload.actual_start_date
        : null,
    actualEndDate:
      typeof payload.actual_end_date === 'string'
        ? payload.actual_end_date
        : null,
    budgetAmount: toNumberOrNull(payload.budget_amount),
    actualCostAmount: toNumberOrNull(payload.actual_cost_amount),
    description:
      typeof payload.description === 'string' ? payload.description : null,
    heritageClassification: String(
      payload.heritage_classification ?? 'none',
    ) as HeritageClassification,
    heritageApprovalRequired: Boolean(payload.heritage_approval_required),
    heritageApprovalStatus:
      typeof payload.heritage_approval_status === 'string'
        ? payload.heritage_approval_status
        : null,
    occupancyStatus: String(
      payload.occupancy_status ?? 'vacant',
    ) as OccupancyStatus,
    tenantCoordinationRequired: Boolean(payload.tenant_coordination_required),
    createdAt: String(payload.created_at ?? ''),
    updatedAt: String(payload.updated_at ?? ''),
  }
}

function mapGanttTask(payload: Record<string, unknown>): GanttTask {
  return {
    id: String(payload.id ?? ''),
    name: String(payload.name ?? ''),
    phaseType: String(payload.phase_type ?? 'site_preparation') as PhaseType,
    status: String(payload.status ?? 'not_started') as PhaseStatus,
    startDate: String(payload.start_date ?? ''),
    endDate: String(payload.end_date ?? ''),
    duration: Number(payload.duration ?? 0),
    progress: Number(payload.progress ?? 0),
    dependencies: Array.isArray(payload.dependencies)
      ? payload.dependencies.map(String)
      : [],
    isCritical: Boolean(payload.is_critical),
    isHeritage: Boolean(payload.is_heritage),
    hasTenantCoordination: Boolean(payload.has_tenant_coordination),
    color: String(payload.color ?? '#3b82f6'),
    budgetAmount: toNumberOrNull(payload.budget_amount),
    actualCostAmount: toNumberOrNull(payload.actual_cost_amount),
  }
}

function mapGanttChart(payload: Record<string, unknown>): GanttChart {
  const tasks = Array.isArray(payload.tasks)
    ? (payload.tasks as Record<string, unknown>[]).map(mapGanttTask)
    : []

  return {
    projectId: String(payload.project_id ?? ''),
    projectName: String(payload.project_name ?? ''),
    generatedAt: String(payload.generated_at ?? ''),
    tasks,
    projectStartDate:
      typeof payload.project_start_date === 'string'
        ? payload.project_start_date
        : null,
    projectEndDate:
      typeof payload.project_end_date === 'string'
        ? payload.project_end_date
        : null,
    totalDuration: Number(payload.total_duration ?? 0),
    criticalPathDuration: Number(payload.critical_path_duration ?? 0),
  }
}

function mapTenantRelocation(
  payload: Record<string, unknown>,
): TenantRelocation {
  return {
    id: Number(payload.id ?? 0),
    phaseId: Number(payload.phase_id ?? 0),
    tenantName: String(payload.tenant_name ?? ''),
    currentUnit: String(payload.current_unit ?? ''),
    relocationType: String(payload.relocation_type ?? ''),
    status: String(payload.status ?? ''),
    notificationDate:
      typeof payload.notification_date === 'string'
        ? payload.notification_date
        : null,
    plannedMoveDate:
      typeof payload.planned_move_date === 'string'
        ? payload.planned_move_date
        : null,
    actualMoveDate:
      typeof payload.actual_move_date === 'string'
        ? payload.actual_move_date
        : null,
    temporaryLocation:
      typeof payload.temporary_location === 'string'
        ? payload.temporary_location
        : null,
    compensationAmount: toNumberOrNull(payload.compensation_amount),
    notes: typeof payload.notes === 'string' ? payload.notes : null,
  }
}

function mapTenantCoordinationSummary(
  payload: Record<string, unknown>,
): TenantCoordinationSummary {
  const relocations = Array.isArray(payload.relocations)
    ? (payload.relocations as Record<string, unknown>[]).map(
        mapTenantRelocation,
      )
    : []
  const upcomingMoves = Array.isArray(payload.upcoming_moves)
    ? (payload.upcoming_moves as Record<string, unknown>[]).map(
        mapTenantRelocation,
      )
    : []
  const overdueNotifications = Array.isArray(payload.overdue_notifications)
    ? (payload.overdue_notifications as Record<string, unknown>[]).map(
        mapTenantRelocation,
      )
    : []

  return {
    projectId: String(payload.project_id ?? ''),
    totalTenants: Number(payload.total_tenants ?? 0),
    statusBreakdown:
      typeof payload.status_breakdown === 'object' &&
      payload.status_breakdown !== null
        ? (payload.status_breakdown as Record<string, number>)
        : {},
    relocations,
    upcomingMoves,
    overdueNotifications,
    timeline: Array.isArray(payload.timeline)
      ? (payload.timeline as Record<string, unknown>[]).map((t) => ({
          date: String(t.date ?? ''),
          event: String(t.event ?? ''),
          tenantName: String(t.tenant_name ?? ''),
          status: String(t.status ?? ''),
        }))
      : [],
    warnings: Array.isArray(payload.warnings)
      ? payload.warnings.map(String)
      : [],
  }
}

function mapHeritageTracker(payload: Record<string, unknown>): HeritageTracker {
  return {
    projectId: String(payload.project_id ?? ''),
    heritageClassification: String(
      payload.heritage_classification ?? 'none',
    ) as HeritageClassification,
    overallApprovalStatus: String(payload.overall_approval_status ?? ''),
    phases: Array.isArray(payload.phases)
      ? (payload.phases as Record<string, unknown>[]).map((p) => ({
          phaseId: Number(p.phase_id ?? 0),
          name: String(p.name ?? ''),
          heritageClassification: String(
            p.heritage_classification ?? 'none',
          ) as HeritageClassification,
          approvalRequired: Boolean(p.approval_required),
          approvalStatus:
            typeof p.approval_status === 'string' ? p.approval_status : null,
          specialConsiderations: Array.isArray(p.special_considerations)
            ? p.special_considerations.map(String)
            : [],
        }))
      : [],
    requiredApprovals: Array.isArray(payload.required_approvals)
      ? payload.required_approvals.map(String)
      : [],
    preservationRisks: Array.isArray(payload.preservation_risks)
      ? payload.preservation_risks.map(String)
      : [],
    recommendations: Array.isArray(payload.recommendations)
      ? payload.recommendations.map(String)
      : [],
  }
}

function mapCriticalPath(payload: Record<string, unknown>): CriticalPathResult {
  return {
    projectId: String(payload.project_id ?? ''),
    criticalPath: Array.isArray(payload.critical_path)
      ? payload.critical_path.map(String)
      : [],
    totalDuration: Number(payload.total_duration ?? 0),
    criticalPhases: Array.isArray(payload.critical_phases)
      ? (payload.critical_phases as Record<string, unknown>[]).map((p) => ({
          phaseId: Number(p.phase_id ?? 0),
          name: String(p.name ?? ''),
          earlyStart: Number(p.early_start ?? 0),
          earlyFinish: Number(p.early_finish ?? 0),
          lateStart: Number(p.late_start ?? 0),
          lateFinish: Number(p.late_finish ?? 0),
          float: Number(p.float ?? 0),
        }))
      : [],
    nonCriticalPhases: Array.isArray(payload.non_critical_phases)
      ? (payload.non_critical_phases as Record<string, unknown>[]).map((p) => ({
          phaseId: Number(p.phase_id ?? 0),
          name: String(p.name ?? ''),
          float: Number(p.float ?? 0),
        }))
      : [],
  }
}

// API Functions
export async function fetchProjectPhases(
  projectId: string,
  signal?: AbortSignal,
): Promise<DevelopmentPhase[]> {
  const response = await fetch(
    buildUrl(`/api/v1/projects/${projectId}/phases`),
    { signal },
  )
  if (!response.ok) {
    throw new Error('Failed to load project phases')
  }
  const payload = (await response.json()) as Record<string, unknown>[]
  return payload.map(mapPhase)
}

export async function fetchGanttChart(
  projectId: string,
  signal?: AbortSignal,
): Promise<GanttChart> {
  const response = await fetch(
    buildUrl(`/api/v1/projects/${projectId}/gantt`),
    { signal },
  )
  if (!response.ok) {
    throw new Error('Failed to load Gantt chart')
  }
  const payload = (await response.json()) as Record<string, unknown>
  return mapGanttChart(payload)
}

export async function fetchCriticalPath(
  projectId: string,
  signal?: AbortSignal,
): Promise<CriticalPathResult> {
  const response = await fetch(
    buildUrl(`/api/v1/projects/${projectId}/critical-path`),
    { signal },
  )
  if (!response.ok) {
    throw new Error('Failed to load critical path')
  }
  const payload = (await response.json()) as Record<string, unknown>
  return mapCriticalPath(payload)
}

export async function fetchHeritageTracker(
  projectId: string,
  signal?: AbortSignal,
): Promise<HeritageTracker> {
  const response = await fetch(
    buildUrl(`/api/v1/projects/${projectId}/heritage`),
    { signal },
  )
  if (!response.ok) {
    throw new Error('Failed to load heritage tracker')
  }
  const payload = (await response.json()) as Record<string, unknown>
  return mapHeritageTracker(payload)
}

export async function fetchTenantCoordination(
  projectId: string,
  signal?: AbortSignal,
): Promise<TenantCoordinationSummary> {
  const response = await fetch(
    buildUrl(`/api/v1/projects/${projectId}/tenant-coordination`),
    { signal },
  )
  if (!response.ok) {
    throw new Error('Failed to load tenant coordination')
  }
  const payload = (await response.json()) as Record<string, unknown>
  return mapTenantCoordinationSummary(payload)
}

export interface CreatePhasePayload {
  name: string
  phaseType: PhaseType
  sequenceOrder: number
  plannedStartDate?: string | null
  plannedEndDate?: string | null
  budgetAmount?: number | null
  description?: string | null
  heritageClassification?: HeritageClassification
  heritageApprovalRequired?: boolean
  occupancyStatus?: OccupancyStatus
  tenantCoordinationRequired?: boolean
}

export async function createPhase(
  projectId: string,
  payload: CreatePhasePayload,
  signal?: AbortSignal,
): Promise<DevelopmentPhase> {
  const body = {
    name: payload.name,
    phase_type: payload.phaseType,
    sequence_order: payload.sequenceOrder,
    planned_start_date: payload.plannedStartDate,
    planned_end_date: payload.plannedEndDate,
    budget_amount: payload.budgetAmount,
    description: payload.description,
    heritage_classification: payload.heritageClassification ?? 'none',
    heritage_approval_required: payload.heritageApprovalRequired ?? false,
    occupancy_status: payload.occupancyStatus ?? 'vacant',
    tenant_coordination_required: payload.tenantCoordinationRequired ?? false,
  }

  const response = await fetch(
    buildUrl(`/api/v1/projects/${projectId}/phases`),
    {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(body),
      signal,
    },
  )

  if (!response.ok) {
    throw new Error('Failed to create phase')
  }

  const data = (await response.json()) as Record<string, unknown>
  return mapPhase(data)
}

export interface UpdatePhasePayload {
  name?: string
  status?: PhaseStatus
  plannedStartDate?: string | null
  plannedEndDate?: string | null
  actualStartDate?: string | null
  actualEndDate?: string | null
  budgetAmount?: number | null
  actualCostAmount?: number | null
  description?: string | null
  heritageApprovalStatus?: string | null
}

export async function updatePhase(
  projectId: string,
  phaseId: number,
  payload: UpdatePhasePayload,
  signal?: AbortSignal,
): Promise<DevelopmentPhase> {
  const body: Record<string, unknown> = {}
  if (payload.name !== undefined) body.name = payload.name
  if (payload.status !== undefined) body.status = payload.status
  if (payload.plannedStartDate !== undefined)
    body.planned_start_date = payload.plannedStartDate
  if (payload.plannedEndDate !== undefined)
    body.planned_end_date = payload.plannedEndDate
  if (payload.actualStartDate !== undefined)
    body.actual_start_date = payload.actualStartDate
  if (payload.actualEndDate !== undefined)
    body.actual_end_date = payload.actualEndDate
  if (payload.budgetAmount !== undefined)
    body.budget_amount = payload.budgetAmount
  if (payload.actualCostAmount !== undefined)
    body.actual_cost_amount = payload.actualCostAmount
  if (payload.description !== undefined) body.description = payload.description
  if (payload.heritageApprovalStatus !== undefined)
    body.heritage_approval_status = payload.heritageApprovalStatus

  const response = await fetch(
    buildUrl(`/api/v1/projects/${projectId}/phases/${phaseId}`),
    {
      method: 'PATCH',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(body),
      signal,
    },
  )

  if (!response.ok) {
    throw new Error('Failed to update phase')
  }

  const data = (await response.json()) as Record<string, unknown>
  return mapPhase(data)
}
