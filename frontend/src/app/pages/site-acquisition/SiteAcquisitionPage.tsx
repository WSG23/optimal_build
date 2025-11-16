import { useCallback, useEffect, useMemo, useRef, useState, type CSSProperties } from 'react'
import { createPortal } from 'react-dom'
import { Link } from '../../../router'
import {
  capturePropertyForDevelopment,
  fetchChecklistSummary,
  fetchPropertyChecklist,
  fetchConditionAssessment,
  fetchConditionAssessmentHistory,
  fetchScenarioAssessments,
  fetchPreviewJob,
  refreshPreviewJob,
  listPreviewJobs,
  exportConditionReport,
  saveConditionAssessment,
  updateChecklistItem,
  OFFLINE_PROPERTY_ID,
  DEFAULT_SCENARIO_ORDER,
  type ChecklistItem,
  type ChecklistSummary,
  type ConditionAssessment,
  type ConditionAssessmentUpsertRequest,
  type ConditionAttachment,
  type DevelopmentScenario,
  type SiteAcquisitionResult,
  type DeveloperPreviewJob,
  type DeveloperAssetOptimization,
  type GeometryDetailLevel,
  type DeveloperColorLegendEntry,
} from '../../../api/siteAcquisition'
import { Preview3DViewer } from '../../components/site-acquisition/Preview3DViewer'
import {
  normalisePreviewLayer,
  normaliseLegendEntry,
  type PreviewLayerMetadata,
  type PreviewLegendEntry,
} from './previewMetadata'

const SCENARIO_OPTIONS: Array<{
  value: DevelopmentScenario
  label: string
  description: string
  icon: string
}> = [
  {
    value: 'raw_land',
    label: 'New Construction',
    description: 'Raw land development with ground-up construction',
    icon: '🏗️',
  },
  {
    value: 'existing_building',
    label: 'Renovation',
    description: 'Existing building renovation and modernization',
    icon: '🔨',
  },
  {
    value: 'heritage_property',
    label: 'Heritage Integration',
    description: 'Heritage-protected property with conservation requirements',
    icon: '🏛️',
  },
  {
    value: 'underused_asset',
    label: 'Adaptive Reuse',
    description: 'Underutilized asset repositioning and value-add',
    icon: '♻️',
  },
  {
    value: 'mixed_use_redevelopment',
    label: 'Mixed-Use Redevelopment',
    description: 'Complex mixed-use project with residential, commercial, and retail components',
    icon: '🏙️',
  },
]

const CONDITION_RATINGS = ['A', 'B', 'C', 'D', 'E']
const CONDITION_RISK_LEVELS = ['low', 'moderate', 'elevated', 'high', 'critical']
const DEFAULT_CONDITION_SYSTEMS = [
  'Structural frame & envelope',
  'Mechanical & electrical systems',
  'Compliance & envelope maintenance',
]
const HISTORY_FETCH_LIMIT = 10
const PREVIEW_DETAIL_OPTIONS: GeometryDetailLevel[] = ['medium', 'simple']
const PREVIEW_DETAIL_LABELS: Record<GeometryDetailLevel, string> = {
  medium: 'Medium (octagonal, setbacks, floor lines)',
  simple: 'Simple (fast box geometry)',
}

type QuickAnalysisSnapshot = {
  propertyId: string
  generatedAt: string
  scenarios: SiteAcquisitionResult['quickAnalysis']['scenarios']
  comparison: ScenarioComparisonDatum[]
}

const QUICK_ANALYSIS_HISTORY_LIMIT = 5

const OFFLINE_CHECKLIST_TEMPLATES: Array<{
  developmentScenario: DevelopmentScenario
  category: ChecklistItem['category']
  itemTitle: string
  itemDescription?: string
  priority: ChecklistItem['priority']
  requiresProfessional: boolean
  professionalType?: string | null
  typicalDurationDays?: number | null
  displayOrder: number
}> = [
  {
    developmentScenario: 'raw_land',
    category: 'title_verification',
    itemTitle: 'Confirm land ownership and title status',
    itemDescription:
      'Retrieve SLA title extracts and confirm that there are no caveats or encumbrances on the parcel.',
    priority: 'critical',
    requiresProfessional: true,
    professionalType: 'Conveyancing lawyer',
    typicalDurationDays: 5,
    displayOrder: 10,
  },
  {
    developmentScenario: 'raw_land',
    category: 'zoning_compliance',
    itemTitle: 'Validate URA master plan parameters',
    itemDescription:
      'Cross-check zoning, plot ratio, and allowable uses against intended development outcomes.',
    priority: 'critical',
    requiresProfessional: false,
    typicalDurationDays: 4,
    displayOrder: 20,
  },
  {
    developmentScenario: 'raw_land',
    category: 'environmental_assessment',
    itemTitle: 'Screen for environmental and soil constraints',
    itemDescription:
      'Review PUB drainage, flood susceptibility, soil conditions, and adjacent environmental protections.',
    priority: 'high',
    requiresProfessional: true,
    professionalType: 'Geotechnical engineer',
    typicalDurationDays: 7,
    displayOrder: 30,
  },
  {
    developmentScenario: 'raw_land',
    category: 'access_rights',
    itemTitle: 'Confirm legal site access and right-of-way',
    itemDescription:
      'Validate ingress/egress arrangements with LTA and adjacent land owners for temporary works.',
    priority: 'medium',
    requiresProfessional: true,
    professionalType: 'Traffic consultant',
    typicalDurationDays: 6,
    displayOrder: 40,
  },
  {
    developmentScenario: 'existing_building',
    category: 'structural_survey',
    itemTitle: 'Commission structural integrity assessment',
    itemDescription:
      'Carry out intrusive and non-intrusive inspections to determine retrofitting effort.',
    priority: 'critical',
    requiresProfessional: true,
    professionalType: 'Structural engineer',
    typicalDurationDays: 14,
    displayOrder: 10,
  },
  {
    developmentScenario: 'existing_building',
    category: 'utility_capacity',
    itemTitle: 'Benchmark utility upgrade requirements',
    itemDescription:
      'Review existing electrical, water, and gas supply against target load profiles.',
    priority: 'high',
    requiresProfessional: true,
    professionalType: 'M&E engineer',
    typicalDurationDays: 5,
    displayOrder: 20,
  },
  {
    developmentScenario: 'existing_building',
    category: 'zoning_compliance',
    itemTitle: 'Validate change-of-use requirements',
    itemDescription:
      'Confirm URA and BCA approvals required for intended repositioning program.',
    priority: 'high',
    requiresProfessional: false,
    typicalDurationDays: 3,
    displayOrder: 30,
  },
  {
    developmentScenario: 'existing_building',
    category: 'environmental_assessment',
    itemTitle: 'Assess asbestos and hazardous material presence',
    itemDescription:
      'Undertake sampling programme before any strip-out or demolition work proceeds.',
    priority: 'medium',
    requiresProfessional: true,
    professionalType: 'Environmental consultant',
    typicalDurationDays: 10,
    displayOrder: 40,
  },
  {
    developmentScenario: 'heritage_property',
    category: 'heritage_constraints',
    itemTitle: 'Confirm conservation requirements with URA',
    itemDescription:
      'Document façade retention, material preservation, and permissible alteration scope.',
    priority: 'critical',
    requiresProfessional: true,
    professionalType: 'Heritage architect',
    typicalDurationDays: 7,
    displayOrder: 10,
  },
  {
    developmentScenario: 'heritage_property',
    category: 'structural_survey',
    itemTitle: 'Heritage structural reinforcement study',
    itemDescription:
      'Evaluate load paths and necessary strengthening to achieve code compliance without damaging heritage elements.',
    priority: 'high',
    requiresProfessional: true,
    professionalType: 'Structural engineer',
    typicalDurationDays: 12,
    displayOrder: 20,
  },
  {
    developmentScenario: 'heritage_property',
    category: 'zoning_compliance',
    itemTitle: 'Assess conservation overlay with planning parameters',
    itemDescription:
      'Check whether conservation overlays restrict development intensity or allowable uses.',
    priority: 'high',
    requiresProfessional: false,
    typicalDurationDays: 5,
    displayOrder: 30,
  },
  {
    developmentScenario: 'heritage_property',
    category: 'access_rights',
    itemTitle: 'Coordinate logistics with surrounding stakeholders',
    itemDescription:
      'Identify staging areas, hoarding approvals, and historic streetscape protection measures.',
    priority: 'medium',
    requiresProfessional: false,
    typicalDurationDays: 4,
    displayOrder: 40,
  },
  {
    developmentScenario: 'underused_asset',
    category: 'utility_capacity',
    itemTitle: 'Determine retrofit M&E upgrade scope',
    itemDescription:
      'Right-size mechanical plant, vertical transportation, and ICT backbone for the new programme.',
    priority: 'high',
    requiresProfessional: true,
    professionalType: 'Building services engineer',
    typicalDurationDays: 8,
    displayOrder: 10,
  },
  {
    developmentScenario: 'underused_asset',
    category: 'environmental_assessment',
    itemTitle: 'Perform indoor environmental quality audit',
    itemDescription:
      'Quantify remediation required for mould, humidity, and ventilation gaps from prolonged underuse.',
    priority: 'medium',
    requiresProfessional: true,
    professionalType: 'Environmental specialist',
    typicalDurationDays: 6,
    displayOrder: 20,
  },
  {
    developmentScenario: 'underused_asset',
    category: 'access_rights',
    itemTitle: 'Validate access control and fire egress updates',
    itemDescription:
      'Ensure adaptive reuse complies with SCDF requirements and workplace safety codes.',
    priority: 'high',
    requiresProfessional: true,
    professionalType: 'Fire engineer',
    typicalDurationDays: 5,
    displayOrder: 30,
  },
  {
    developmentScenario: 'mixed_use_redevelopment',
    category: 'zoning_compliance',
    itemTitle: 'Confirm mixed-use allowable combination',
    itemDescription:
      'Reconcile residential, commercial, and retail programme with masterplan mix and strata limitations.',
    priority: 'critical',
    requiresProfessional: false,
    typicalDurationDays: 6,
    displayOrder: 10,
  },
  {
    developmentScenario: 'mixed_use_redevelopment',
    category: 'utility_capacity',
    itemTitle: 'Integrate district cooling and energy sharing options',
    itemDescription:
      'Assess utility providers\' capacity and incentives for precinct-scale systems.',
    priority: 'high',
    requiresProfessional: true,
    professionalType: 'Energy consultant',
    typicalDurationDays: 9,
    displayOrder: 20,
  },
  {
    developmentScenario: 'mixed_use_redevelopment',
    category: 'structural_survey',
    itemTitle: 'Phase-by-phase structural staging plan',
    itemDescription:
      'Evaluate demolition, retention, and staging needed to keep operations running during redevelopment.',
    priority: 'high',
    requiresProfessional: true,
    professionalType: 'Structural engineer',
    typicalDurationDays: 15,
    displayOrder: 30,
  },
  {
    developmentScenario: 'mixed_use_redevelopment',
    category: 'heritage_constraints',
    itemTitle: 'Coordinate heritage façade integration',
    itemDescription:
      'Identify conserved elements that must be retained and methods to blend with new podium.',
    priority: 'medium',
    requiresProfessional: true,
    professionalType: 'Conservation architect',
    typicalDurationDays: 10,
    displayOrder: 40,
  },
]

const SCENARIO_METRIC_PRIORITY: readonly string[] = [
  'plot_ratio',
  'potential_gfa_sqm',
  'gfa_uplift_sqm',
  'occupancy_pct',
  'annual_noi',
  'valuation_cap_rate',
  'potential_rent_uplift_pct',
  'target_lease_term_years',
  'estimated_capex',
  'conservation_status',
]

const SCENARIO_METRIC_LABELS: Record<string, string> = {
  plot_ratio: 'Plot ratio',
  potential_gfa_sqm: 'Potential GFA (sqm)',
  gfa_uplift_sqm: 'GFA uplift (sqm)',
  occupancy_pct: 'Occupancy',
  annual_noi: 'Annual NOI',
  valuation_cap_rate: 'Cap rate',
  potential_rent_uplift_pct: 'Rent uplift',
  target_lease_term_years: 'Lease term (yrs)',
  estimated_capex: 'Estimated CAPEX',
  conservation_status: 'Conservation status',
}

function buildOfflineChecklistItems(
  propertyId: string,
  scenarios: DevelopmentScenario[] | null,
): ChecklistItem[] {
  const scenarioSet = new Set<DevelopmentScenario>(scenarios ?? [])
  if (scenarioSet.size === 0) {
    DEFAULT_SCENARIO_ORDER.forEach((scenario) => scenarioSet.add(scenario))
  }

  const scenarioRank = new Map(
    DEFAULT_SCENARIO_ORDER.map((scenario, index) => [scenario, index]),
  )

  const selectedTemplates = OFFLINE_CHECKLIST_TEMPLATES.filter((template) =>
    scenarioSet.has(template.developmentScenario),
  )

  selectedTemplates.sort((a, b) => {
    const scenarioDiff =
      (scenarioRank.get(a.developmentScenario) ?? Number.MAX_SAFE_INTEGER) -
      (scenarioRank.get(b.developmentScenario) ?? Number.MAX_SAFE_INTEGER)
    if (scenarioDiff !== 0) {
      return scenarioDiff
    }
    const aOrder = a.displayOrder ?? 0
    const bOrder = b.displayOrder ?? 0
    return aOrder - bOrder
  })

  return selectedTemplates.map((template, index) => ({
    id: `${template.developmentScenario}-${index}-${propertyId}`,
    propertyId,
    developmentScenario: template.developmentScenario,
    category: template.category,
    itemTitle: template.itemTitle,
    itemDescription: template.itemDescription,
    status: 'pending',
    priority: template.priority,
    assignedTo: null,
    dueDate: null,
    completedAt: null,
    notes: null,
    requiresProfessional: template.requiresProfessional,
    professionalType: template.professionalType ?? null,
    typicalDurationDays: template.typicalDurationDays ?? null,
    displayOrder: template.displayOrder,
    createdAt: new Date().toISOString(),
    updatedAt: new Date().toISOString(),
  }))
}

type AssessmentDraftSystem = {
  name: string
  rating: string
  score: string
  notes: string
  recommendedActions: string
}

type ConditionAssessmentDraft = {
  scenario: DevelopmentScenario | 'all'
  overallRating: string
  overallScore: string
  riskLevel: string
  summary: string
  scenarioContext: string
  systems: AssessmentDraftSystem[]
  recommendedActionsText: string
  inspectorName: string
  recordedAtLocal: string
  attachmentsText: string
}

type ScenarioComparisonKey = 'all' | DevelopmentScenario

type ScenarioComparisonMetric = {
  key: string
  label: string
  value: string
}

type ScenarioComparisonDatum = {
  key: ScenarioComparisonKey
  label: string
  icon: string
  quickHeadline: string | null
  quickMetrics: ScenarioComparisonMetric[]
  conditionRating: string | null
  conditionScore: number | null
  riskLevel: string | null
  checklistCompleted: number | null
  checklistTotal: number | null
  checklistPercent: number | null
  insights: ConditionInsightView[]
  primaryInsight: ConditionInsightView | null
  recommendedAction: string | null
  recordedAt: string | null
  inspectorName: string | null
  source: 'manual' | 'heuristic'
}

type QuickAnalysisEntry =
  SiteAcquisitionResult['quickAnalysis']['scenarios'][number]

function buildAssessmentDraft(
  assessment: ConditionAssessment | null,
  activeScenario: DevelopmentScenario | 'all',
): ConditionAssessmentDraft {
  const targetScenario =
    assessment?.scenario ?? (activeScenario === 'all' ? 'all' : activeScenario)
  const systemsFromAssessment = assessment?.systems ?? []

  const systems: AssessmentDraftSystem[] = (
    systemsFromAssessment.length > 0
      ? systemsFromAssessment
      : DEFAULT_CONDITION_SYSTEMS.map((name) => ({
          name,
          rating: 'B',
          score: 70,
          notes: '',
          recommendedActions: '',
        }))
  ).map((system) => ({
    name: system.name,
    rating: system.rating,
    score: String(system.score ?? 0),
    notes: system.notes ?? '',
    recommendedActions: Array.isArray(system.recommendedActions)
      ? system.recommendedActions.join('\n')
      : '',
  }))

  const recordedAtLocal = formatDateTimeLocalInput(assessment?.recordedAt ?? null)
  const attachmentsText = (assessment?.attachments ?? [])
    .map((attachment) =>
      attachment.url ? `${attachment.label} | ${attachment.url}` : attachment.label,
    )
    .join('\n')

  return {
    scenario: targetScenario,
    overallRating: assessment?.overallRating ?? 'B',
    overallScore: String(assessment?.overallScore ?? 75),
    riskLevel: assessment?.riskLevel ?? 'moderate',
    summary: assessment?.summary ?? '',
    scenarioContext: assessment?.scenarioContext ?? '',
    systems,
    recommendedActionsText: assessment?.recommendedActions
      ? assessment.recommendedActions.join('\n')
      : '',
    inspectorName: assessment?.inspectorName ?? '',
    recordedAtLocal,
    attachmentsText,
  }
}

function formatCategoryName(category: string): string {
  return category
    .split('_')
    .map((word) => word.charAt(0).toUpperCase() + word.slice(1))
    .join(' ')
}

function computeChecklistSummary(
  items: ChecklistItem[],
  propertyId: string,
): ChecklistSummary {
  const totals = {
    total: items.length,
    completed: 0,
    inProgress: 0,
    pending: 0,
    notApplicable: 0,
  }

  const byCategoryStatus: Record<
    string,
    {
      total: number
      completed: number
      inProgress: number
      pending: number
      notApplicable: number
    }
  > = {}

  items.forEach((item) => {
    switch (item.status) {
      case 'completed':
        totals.completed += 1
        break
      case 'in_progress':
        totals.inProgress += 1
        break
      case 'not_applicable':
        totals.notApplicable += 1
        break
      default:
        totals.pending += 1
        break
    }

    const categoryEntry =
      byCategoryStatus[item.category] ?? {
        total: 0,
        completed: 0,
        inProgress: 0,
        pending: 0,
        notApplicable: 0,
      }

    categoryEntry.total += 1
    if (item.status === 'completed') {
      categoryEntry.completed += 1
    } else if (item.status === 'in_progress') {
      categoryEntry.inProgress += 1
    } else if (item.status === 'not_applicable') {
      categoryEntry.notApplicable += 1
    } else {
      categoryEntry.pending += 1
    }

    byCategoryStatus[item.category] = categoryEntry
  })

  const completionPercentage =
    totals.total > 0 ? Math.round((totals.completed / totals.total) * 100) : 0

  return {
    propertyId,
    total: totals.total,
    completed: totals.completed,
    inProgress: totals.inProgress,
    pending: totals.pending,
    notApplicable: totals.notApplicable,
    completionPercentage,
    byCategoryStatus,
  }
}

function toTitleCase(value: string): string {
  return value
    .split(/[\s_-]+/)
    .filter(Boolean)
    .map((token) => token.charAt(0).toUpperCase() + token.slice(1).toLowerCase())
    .join(' ')
}

export function SiteAcquisitionPage() {
  const [latitude, setLatitude] = useState('1.3000')
  const [longitude, setLongitude] = useState('103.8500')
  const [selectedScenarios, setSelectedScenarios] = useState<DevelopmentScenario[]>([])
  const [isCapturing, setIsCapturing] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [capturedProperty, setCapturedProperty] = useState<SiteAcquisitionResult | null>(null)
  const [previewJob, setPreviewJob] = useState<DeveloperPreviewJob | null>(null)
  const [previewDetailLevel, setPreviewDetailLevel] =
    useState<GeometryDetailLevel>('medium')
  const [isRefreshingPreview, setIsRefreshingPreview] = useState(false)
  const [previewLayerMetadata, setPreviewLayerMetadata] = useState<
    PreviewLayerMetadata[]
  >([])
  const [previewLayerVisibility, setPreviewLayerVisibility] = useState<
    Record<string, boolean>
  >({})
  const [previewFocusLayerId, setPreviewFocusLayerId] = useState<string | null>(
    null,
  )
  const [isPreviewMetadataLoading, setIsPreviewMetadataLoading] = useState(false)
  const [previewMetadataError, setPreviewMetadataError] = useState<string | null>(
    null,
  )
  const [legendEntries, setLegendEntries] = useState<PreviewLegendEntry[]>([])
  const legendBaselineRef = useRef<PreviewLegendEntry[]>([])

  // Checklist state
  const [checklistItems, setChecklistItems] = useState<ChecklistItem[]>([])
  const [checklistSummary, setChecklistSummary] = useState<ChecklistSummary | null>(null)
  const [isLoadingChecklist, setIsLoadingChecklist] = useState(false)
  const [selectedCategory, setSelectedCategory] = useState<string | null>(null)
  const [availableChecklistScenarios, setAvailableChecklistScenarios] = useState<
    DevelopmentScenario[]
  >([])
  const [activeScenario, setActiveScenario] = useState<DevelopmentScenario | 'all'>('all')
  const [conditionAssessment, setConditionAssessment] =
    useState<ConditionAssessment | null>(null)
  const [isLoadingCondition, setIsLoadingCondition] = useState(false)
  const [isEditingAssessment, setIsEditingAssessment] = useState(false)
  const [assessmentEditorMode, setAssessmentEditorMode] = useState<'new' | 'edit'>('edit')
  const [assessmentDraft, setAssessmentDraft] = useState<ConditionAssessmentDraft>(() =>
    buildAssessmentDraft(null, 'all'),
  )
  const [isSavingAssessment, setIsSavingAssessment] = useState(false)
  const [assessmentSaveMessage, setAssessmentSaveMessage] = useState<string | null>(
    null,
  )
  const [assessmentHistory, setAssessmentHistory] = useState<ConditionAssessment[]>([])
  const [isLoadingAssessmentHistory, setIsLoadingAssessmentHistory] = useState(false)
  const [assessmentHistoryError, setAssessmentHistoryError] = useState<string | null>(
    null,
  )
  const [historyViewMode, setHistoryViewMode] = useState<'timeline' | 'compare'>(
    'timeline',
  )
  const historyRequestIdRef = useRef(0)
  const [scenarioAssessments, setScenarioAssessments] = useState<ConditionAssessment[]>(
    [],
  )
  const [isLoadingScenarioAssessments, setIsLoadingScenarioAssessments] =
    useState(false)
  const [scenarioAssessmentsError, setScenarioAssessmentsError] = useState<string | null>(
    null,
  )
  const scenarioAssessmentsRequestIdRef = useRef(0)
  const [scenarioComparisonBase, setScenarioComparisonBase] =
    useState<DevelopmentScenario | null>(null)
  const [isExportingReport, setIsExportingReport] = useState(false)
  const [reportExportMessage, setReportExportMessage] = useState<string | null>(null)
  const propertyId = capturedProperty?.propertyId ?? null
  const previewViewerMetadataUrl =
    previewJob?.metadataUrl ?? capturedProperty?.visualization?.previewMetadataUrl ?? null
  const colorLegendEntries = useMemo(() => {
    if (legendEntries.length > 0) {
      return legendEntries
    }
    return capturedProperty?.visualization?.colorLegend ?? []
  }, [capturedProperty?.visualization?.colorLegend, legendEntries])
  const legendPayloadForPreview = useMemo<DeveloperColorLegendEntry[]>(
    () =>
      colorLegendEntries.map((entry) => ({
        assetType: entry.assetType,
        label: entry.label,
        color: entry.color,
        description: entry.description,
      })),
    [colorLegendEntries],
  )
  const legendHasPendingChanges = useMemo(() => {
    if (!legendBaselineRef.current.length && !colorLegendEntries.length) {
      return false
    }
    try {
      return (
        JSON.stringify(colorLegendEntries) !==
        JSON.stringify(legendBaselineRef.current)
      )
    } catch {
      return true
    }
  }, [colorLegendEntries])

  useEffect(() => {
    if (!capturedProperty?.previewJobs?.length) {
      setPreviewJob(null)
      return
    }
    setPreviewJob(capturedProperty.previewJobs[0])
  }, [capturedProperty?.previewJobs])

  useEffect(() => {
    if (!capturedProperty?.propertyId || capturedProperty.previewJobs?.length) {
      return
    }
    let cancelled = false
    listPreviewJobs(capturedProperty.propertyId).then((jobs) => {
      if (!cancelled && jobs.length) {
        setPreviewJob(jobs[0])
      }
    })
    return () => {
      cancelled = true
    }
  }, [capturedProperty?.propertyId, capturedProperty?.previewJobs])

  useEffect(() => {
    const activeStatuses = new Set(['queued', 'processing'])
    if (!previewJob || !activeStatuses.has(previewJob.status.toLowerCase())) {
      return
    }
    const controller = new AbortController()
    let cancelled = false
    let timer: number | undefined

    const poll = async () => {
      try {
        const latest = await fetchPreviewJob(previewJob.id, controller.signal)
        if (!latest || cancelled) {
          return
        }
        setPreviewJob(latest)
        if (activeStatuses.has(latest.status.toLowerCase())) {
          timer = window.setTimeout(poll, 5000)
        }
      } catch {
        if (!cancelled) {
          timer = window.setTimeout(poll, 5000)
        }
      }
    }

    timer = window.setTimeout(poll, 4000)

    return () => {
      cancelled = true
      controller.abort()
      if (timer !== undefined) {
        window.clearTimeout(timer)
      }
    }
  }, [previewJob, previewJob?.id, previewJob?.status])

  useEffect(() => {
    if (previewJob?.geometryDetailLevel) {
      setPreviewDetailLevel(previewJob.geometryDetailLevel)
    } else {
      setPreviewDetailLevel('medium')
    }
  }, [previewJob?.geometryDetailLevel])

  useEffect(() => {
    if (!capturedProperty?.propertyId) {
      setLegendEntries([])
      legendBaselineRef.current = []
      return
    }
    const baseLegend = (capturedProperty.visualization?.colorLegend ?? []).map(
      (entry) => ({ ...entry }),
    )
    setLegendEntries(baseLegend)
    legendBaselineRef.current = baseLegend
  }, [capturedProperty?.propertyId, capturedProperty?.visualization?.colorLegend])

  useEffect(() => {
    if (!previewViewerMetadataUrl) {
      setPreviewLayerMetadata([])
      setPreviewLayerVisibility({})
      setPreviewFocusLayerId(null)
      setPreviewMetadataError(null)
      setIsPreviewMetadataLoading(false)
      return
    }
    const controller = new AbortController()
    let cancelled = false

    async function loadMetadata() {
      setIsPreviewMetadataLoading(true)
      setPreviewMetadataError(null)
      try {
        const response = await fetch(previewViewerMetadataUrl, {
          signal: controller.signal,
          cache: 'reload',
        })
        if (!response.ok) {
          throw new Error(`Metadata fetch failed (${response.status})`)
        }
        const payload = (await response.json()) as {
          layers?: Array<Record<string, unknown>>
          color_legend?: Array<Record<string, unknown>>
        }
        if (cancelled) {
          return
        }
        const layers = Array.isArray(payload.layers)
          ? payload.layers
              .map((layer) => normalisePreviewLayer(layer))
              .filter((layer): layer is PreviewLayerMetadata => layer !== null)
          : []
        setPreviewLayerMetadata(layers)
        setPreviewLayerVisibility((prev) => {
          if (!layers.length) {
            return {}
          }
          return layers.reduce<Record<string, boolean>>((acc, layer) => {
            acc[layer.id] = prev[layer.id] !== undefined ? prev[layer.id] : true
            return acc
          }, {})
        })
        setPreviewFocusLayerId((current) => {
          if (!current) {
            return null
          }
          return layers.some((layer) => layer.id === current) ? current : null
        })
        const legend = Array.isArray(payload.color_legend)
          ? payload.color_legend
              .map((entry) => normaliseLegendEntry(entry))
              .filter((entry): entry is PreviewLegendEntry => entry !== null)
          : []
        const clonedLegend = legend.map((entry) => ({ ...entry }))
        setLegendEntries(clonedLegend)
        legendBaselineRef.current = clonedLegend
      } catch (metaError) {
        if (cancelled || controller.signal.aborted) {
          return
        }
        console.error('Failed to load preview metadata:', metaError)
        setPreviewMetadataError(
          metaError instanceof Error
            ? metaError.message
            : 'Unable to load preview metadata.',
        )
        setPreviewLayerMetadata([])
        setPreviewLayerVisibility({})
        setPreviewFocusLayerId(null)
      } finally {
        if (!cancelled) {
          setIsPreviewMetadataLoading(false)
        }
      }
    }

    loadMetadata()

    return () => {
      cancelled = true
      controller.abort()
    }
  }, [previewViewerMetadataUrl, previewJob?.id, previewJob?.finishedAt])

  const handleRefreshPreview = useCallback(async () => {
    if (!previewJob) {
      return
    }
    setIsRefreshingPreview(true)
    const refreshed = await refreshPreviewJob(
      previewJob.id,
      previewDetailLevel,
      legendPayloadForPreview,
    )
    if (refreshed) {
      setPreviewJob(refreshed)
    }
    setIsRefreshingPreview(false)
  }, [legendPayloadForPreview, previewDetailLevel, previewJob])
  const hiddenLayerCount = useMemo(
    () =>
      previewLayerMetadata.filter(
        (layer) => previewLayerVisibility[layer.id] === false,
      ).length,
    [previewLayerMetadata, previewLayerVisibility],
  )
  const handleToggleLayerVisibility = useCallback((layerId: string) => {
    setPreviewLayerVisibility((prev) => {
      const next = { ...prev }
      const currentVisible = next[layerId] !== false
      next[layerId] = !currentVisible
      return next
    })
  }, [])
  const handleSoloPreviewLayer = useCallback(
    (layerId: string) => {
      setPreviewLayerVisibility(
        previewLayerMetadata.reduce<Record<string, boolean>>((acc, layer) => {
          acc[layer.id] = layer.id === layerId
          return acc
        }, {}),
      )
      setPreviewFocusLayerId(layerId)
    },
    [previewLayerMetadata],
  )
  const handleShowAllLayers = useCallback(() => {
    setPreviewLayerVisibility(
      previewLayerMetadata.reduce<Record<string, boolean>>((acc, layer) => {
        acc[layer.id] = true
        return acc
      }, {}),
    )
    setPreviewFocusLayerId(null)
  }, [previewLayerMetadata])
  const handleFocusLayer = useCallback((layerId: string) => {
    setPreviewFocusLayerId((current) => (current === layerId ? null : layerId))
  }, [])
  const handleResetLayerFocus = useCallback(() => {
    setPreviewFocusLayerId(null)
  }, [])
  const handleLegendEntryChange = useCallback(
    (
      assetType: string,
      field: 'label' | 'color' | 'description',
      value: string,
    ) => {
      setLegendEntries((prev) => {
        if (!prev.length) {
          return prev
        }
        return prev.map((entry) => {
          if (entry.assetType !== assetType) {
            return entry
          }
          if (field === 'description') {
            const nextDescription = value.trim() === '' ? null : value
            return { ...entry, description: nextDescription }
          }
          return { ...entry, [field]: value }
        })
      })
    },
    [],
  )
  const handleLegendReset = useCallback(() => {
    const baseline = legendBaselineRef.current
    setLegendEntries(baseline.map((entry) => ({ ...entry })))
  }, [])
  const [isHistoryModalOpen, setHistoryModalOpen] = useState(false)
  const [quickAnalysisHistory, setQuickAnalysisHistory] = useState<
    QuickAnalysisSnapshot[]
  >([])
  const [isQuickAnalysisHistoryOpen, setQuickAnalysisHistoryOpen] = useState(false)
  useEffect(() => {
    if (quickAnalysisHistory.length === 0 && isQuickAnalysisHistoryOpen) {
      setQuickAnalysisHistoryOpen(false)
    }
  }, [quickAnalysisHistory.length, isQuickAnalysisHistoryOpen])

  const scenarioLookup = useMemo(
    () => new Map(SCENARIO_OPTIONS.map((option) => [option.value, option])),
    [],
  )

  const loadAssessmentHistory = useCallback(
    async (options?: { silent?: boolean }) => {
      const requestId = historyRequestIdRef.current + 1
      historyRequestIdRef.current = requestId

      if (!propertyId) {
        setAssessmentHistory([])
        setAssessmentHistoryError(null)
        setIsLoadingAssessmentHistory(false)
        return
      }

      if (!options?.silent) {
        setIsLoadingAssessmentHistory(true)
      }
      try {
        const entries = await fetchConditionAssessmentHistory(
          propertyId,
          activeScenario,
          HISTORY_FETCH_LIMIT,
        )
        if (historyRequestIdRef.current === requestId) {
          setAssessmentHistory(entries)
          setAssessmentHistoryError(null)
        }
      } catch (error) {
        console.error('Failed to fetch condition assessment history:', error)
        if (historyRequestIdRef.current === requestId) {
          setAssessmentHistory([])
          setAssessmentHistoryError('Unable to load inspection history.')
        }
      } finally {
        if (!options?.silent && historyRequestIdRef.current === requestId) {
          setIsLoadingAssessmentHistory(false)
        }
      }
    },
    [propertyId, activeScenario],
  )

  const loadScenarioAssessments = useCallback(
    async (options?: { silent?: boolean }) => {
      const requestId = scenarioAssessmentsRequestIdRef.current + 1
      scenarioAssessmentsRequestIdRef.current = requestId

      if (!propertyId) {
        setScenarioAssessments([])
        setScenarioAssessmentsError(null)
        setIsLoadingScenarioAssessments(false)
        return
      }

      if (!options?.silent) {
        setIsLoadingScenarioAssessments(true)
      }
      try {
        const assessments = await fetchScenarioAssessments(propertyId)
        if (scenarioAssessmentsRequestIdRef.current === requestId) {
          setScenarioAssessments(assessments)
          setScenarioAssessmentsError(null)
        }
      } catch (error) {
        console.error('Failed to fetch scenario assessments:', error)
        if (scenarioAssessmentsRequestIdRef.current === requestId) {
          setScenarioAssessments([])
          setScenarioAssessmentsError('Unable to load scenario overrides.')
        }
      } finally {
        if (
          !options?.silent &&
          scenarioAssessmentsRequestIdRef.current === requestId
        ) {
          setIsLoadingScenarioAssessments(false)
        }
      }
    },
    [propertyId],
  )

  useEffect(() => {
    void loadAssessmentHistory()
  }, [loadAssessmentHistory])

  useEffect(() => {
    void loadScenarioAssessments()
  }, [loadScenarioAssessments])

  useEffect(() => {
    setHistoryViewMode('timeline')
  }, [propertyId])

  useEffect(() => {
    if (!isHistoryModalOpen && !isEditingAssessment) {
      return
    }

    const handleKeyDown = (event: KeyboardEvent) => {
      if (event.key === 'Escape') {
        event.preventDefault()
        if (isEditingAssessment) {
          setIsEditingAssessment(false)
        } else if (isHistoryModalOpen) {
          setHistoryModalOpen(false)
        }
      }
    }

    const originalOverflow = document.body.style.overflow
    window.addEventListener('keydown', handleKeyDown)
    document.body.style.overflow = 'hidden'

    return () => {
      window.removeEventListener('keydown', handleKeyDown)
      document.body.style.overflow = originalOverflow
    }
  }, [isHistoryModalOpen, isEditingAssessment])

  // Load checklist when property is captured
  useEffect(() => {
    async function loadChecklist() {
      if (!capturedProperty) {
        setChecklistItems([])
        setChecklistSummary(null)
        setAvailableChecklistScenarios([])
        setActiveScenario('all')
        setSelectedCategory(null)
        setConditionAssessment(null)
        return
      }

      setIsLoadingChecklist(true)
      try {
        if (capturedProperty.propertyId === OFFLINE_PROPERTY_ID) {
          const offlineItems = buildOfflineChecklistItems(
            capturedProperty.propertyId,
            capturedProperty.quickAnalysis.scenarios.map(
              (scenario) => scenario.scenario,
            ),
          )
          const sortedOffline = [...offlineItems].sort((a, b) => {
            const orderA = a.displayOrder ?? Number.MAX_SAFE_INTEGER
            const orderB = b.displayOrder ?? Number.MAX_SAFE_INTEGER
            if (orderA !== orderB) {
              return orderA - orderB
            }
            return a.itemTitle.localeCompare(b.itemTitle)
          })
          setChecklistItems(sortedOffline)
          const offlineScenarios = Array.from(
            new Set(sortedOffline.map((item) => item.developmentScenario)),
          )
          setAvailableChecklistScenarios(offlineScenarios)
          setActiveScenario(offlineScenarios.length === 1 ? offlineScenarios[0] : 'all')
          setChecklistSummary(
            computeChecklistSummary(sortedOffline, capturedProperty.propertyId),
          )
          setSelectedCategory(null)
          return
        }

        const [items, summary] = await Promise.all([
          fetchPropertyChecklist(capturedProperty.propertyId),
          fetchChecklistSummary(capturedProperty.propertyId),
        ])
        const sortedItems = [...items].sort((a, b) => {
          const orderA = a.displayOrder ?? Number.MAX_SAFE_INTEGER
          const orderB = b.displayOrder ?? Number.MAX_SAFE_INTEGER
          if (orderA !== orderB) {
            return orderA - orderB
          }
          return a.itemTitle.localeCompare(b.itemTitle)
        })
        setChecklistItems(sortedItems)
        if (sortedItems.length === 0) {
          const fallbackItems = buildOfflineChecklistItems(
            capturedProperty.propertyId,
            capturedProperty.quickAnalysis.scenarios.map(
              (scenario) => scenario.scenario,
            ),
          )
          if (fallbackItems.length > 0) {
            const sortedFallback = [...fallbackItems].sort((a, b) => {
              const orderA = a.displayOrder ?? Number.MAX_SAFE_INTEGER
              const orderB = b.displayOrder ?? Number.MAX_SAFE_INTEGER
              if (orderA !== orderB) {
                return orderA - orderB
              }
              return a.itemTitle.localeCompare(b.itemTitle)
            })
            setChecklistItems(sortedFallback)
            setChecklistSummary(
              computeChecklistSummary(sortedFallback, capturedProperty.propertyId),
            )
            const fallbackScenarios = Array.from(
              new Set(sortedFallback.map((item) => item.developmentScenario)),
            )
            setAvailableChecklistScenarios(fallbackScenarios)
            setActiveScenario(
              fallbackScenarios.length === 1 ? fallbackScenarios[0] : 'all',
            )
            setSelectedCategory(null)
            return
          }
        }
        setChecklistSummary(summary)
        const scenarioSet = new Set<DevelopmentScenario>()
        sortedItems.forEach((item) => {
          if (scenarioLookup.has(item.developmentScenario)) {
            scenarioSet.add(item.developmentScenario)
          }
        })
        const scenarios = Array.from(scenarioSet)
        setAvailableChecklistScenarios(scenarios)
        setActiveScenario((prev: 'all' | DevelopmentScenario) => {
          if (scenarios.length === 0) {
            return 'all'
          }
          if (prev !== 'all' && scenarios.includes(prev)) {
            return prev
          }
          if (scenarios.length === 1) {
            return scenarios[0]
          }
          return 'all'
        })
        setSelectedCategory(null)
      } catch (err) {
        console.error('Failed to load checklist:', err)
      } finally {
        setIsLoadingChecklist(false)
      }
    }

    loadChecklist()
  }, [capturedProperty, scenarioLookup])

  const filteredChecklistItems = useMemo(
    () =>
      activeScenario === 'all'
        ? checklistItems
        : checklistItems.filter(
            (item) => item.developmentScenario === activeScenario,
          ),
    [checklistItems, activeScenario],
  )

  const displaySummary = useMemo(() => {
    if (!capturedProperty) {
      return null
    }
    if (activeScenario === 'all' && checklistSummary) {
      return checklistSummary
    }
    return computeChecklistSummary(filteredChecklistItems, capturedProperty.propertyId)
  }, [activeScenario, capturedProperty, checklistSummary, filteredChecklistItems])

  const activeScenarioDetails = useMemo(
    () => (activeScenario === 'all' ? null : scenarioLookup.get(activeScenario)),
    [activeScenario, scenarioLookup],
  )

  const quickAnalysis = capturedProperty?.quickAnalysis ?? null
  const quickAnalysisScenarios = useMemo(() => {
    const scenarios = quickAnalysis?.scenarios ?? []
    return Array.isArray(scenarios) ? scenarios : []
  }, [quickAnalysis])
  const comparisonScenarios =
    activeScenario === 'all'
      ? quickAnalysisScenarios
      : quickAnalysisScenarios.filter(
          (scenario) => scenario.scenario === activeScenario,
        )
  const scenarioOverrideEntries = useMemo(
    () =>
      scenarioAssessments.filter(
        (
          assessment,
        ): assessment is ConditionAssessment & {
          scenario: DevelopmentScenario
        } => assessment.scenario !== null,
      ),
    [scenarioAssessments],
  )
  const scenarioFilterOptions = useMemo(() => {
    const collected = new Set<DevelopmentScenario>()
    availableChecklistScenarios.forEach((scenario) => collected.add(scenario))
    quickAnalysisScenarios.forEach((scenario) =>
      collected.add(scenario.scenario as DevelopmentScenario),
    )
    scenarioOverrideEntries.forEach((assessment) =>
      collected.add(assessment.scenario),
    )
    return Array.from(collected)
  }, [availableChecklistScenarios, quickAnalysisScenarios, scenarioOverrideEntries])
  const scenarioFocusOptions = useMemo(
    () =>
      ['all', ...scenarioFilterOptions] as Array<
        'all' | DevelopmentScenario
      >,
    [scenarioFilterOptions],
  )
  const scenarioChecklistProgress = useMemo(() => {
    const progress: Record<string, { total: number; completed: number }> = {}
    checklistItems.forEach((item) => {
      const key = item.developmentScenario
      if (!progress[key]) {
        progress[key] = { total: 0, completed: 0 }
      }
      progress[key].total += 1
      if (item.status === 'completed') {
        progress[key].completed += 1
      }
    })
    return progress
  }, [checklistItems])
  const convertAssessmentInsights = useCallback(
    (assessment: ConditionAssessment | null | undefined): ConditionInsightView[] => {
      if (!assessment?.insights) {
        return []
      }
      return assessment.insights.map((insight, index) => ({
        id: insight.id || `assessment-insight-${index}`,
        severity: normaliseInsightSeverity(insight.severity),
        title: insight.title,
        detail: insight.detail,
        specialist: insight.specialist ?? null,
      }))
    },
    [],
  )
  const scenarioAssessmentsMap = useMemo(() => {
    const map = new Map<DevelopmentScenario, ConditionAssessment>()
    scenarioAssessments.forEach((assessment) => {
      if (assessment.scenario && assessment.scenario !== 'all') {
        map.set(assessment.scenario, assessment)
      }
    })
    if (
      conditionAssessment &&
      conditionAssessment.scenario &&
      conditionAssessment.scenario !== 'all'
    ) {
      map.set(
        conditionAssessment.scenario,
        conditionAssessment,
      )
    }
    return map
  }, [scenarioAssessments, conditionAssessment])
  const formatScenarioLabel = useCallback(
    (scenario: ConditionAssessment['scenario']) => {
      if (!scenario || (typeof scenario === 'string' && scenario === 'all')) {
        return 'All scenarios'
      }
      const entry = scenarioLookup.get(scenario as DevelopmentScenario)
      if (entry) {
        return entry.label
      }
      return formatCategoryName(String(scenario))
    },
    [scenarioLookup],
  )
  const scenarioComparisonRef = useRef<HTMLDivElement | null>(null)
  const comparisonSnapshotSignatureRef = useRef<string | null>(null)
  const formatNumberMetric = useCallback(
    (value: number | null | undefined, options?: Intl.NumberFormatOptions) => {
      if (value === null || value === undefined || Number.isNaN(value)) {
        return '—'
      }
      const formatter = new Intl.NumberFormat('en-SG', {
        maximumFractionDigits: 1,
        ...options,
      })
      return formatter.format(value)
    },
    [],
  )
  const formatCurrency = useCallback(
    (value: number | null | undefined) => {
      if (value === null || value === undefined || Number.isNaN(value)) {
        return '—'
      }
      return new Intl.NumberFormat('en-SG', {
        style: 'currency',
        currency: 'SGD',
        maximumFractionDigits: 0,
      }).format(value)
    },
    [],
  )
  const formatMetricLabel = useCallback((key: string) => {
    if (SCENARIO_METRIC_LABELS[key]) {
      return SCENARIO_METRIC_LABELS[key]
    }
    return key
      .split('_')
      .map((segment) => segment.charAt(0).toUpperCase() + segment.slice(1))
      .join(' ')
  }, [])
  const formatScenarioMetricValue = useCallback(
    (key: string, value: unknown) => {
      if (value === null || value === undefined || value === '') {
        return '—'
      }
      const numeric = safeNumber(value)
      if (numeric !== null) {
        if (key.includes('_pct') || key.endsWith('_rate')) {
          return `${formatNumberMetric(numeric * 100, { maximumFractionDigits: 1 })}%`
        }
        if (key.includes('_sqm')) {
          return `${formatNumberMetric(numeric, { maximumFractionDigits: 0 })} sqm`
        }
        if (
          key === 'annual_noi' ||
          key === 'estimated_capex' ||
          key === 'average_psf_price' ||
          key === 'average_monthly_rent'
        ) {
          return formatCurrency(numeric)
        }
        if (key.includes('_count')) {
          return formatNumberMetric(numeric, { maximumFractionDigits: 0 })
        }
        if (key === 'target_lease_term_years') {
          return `${formatNumberMetric(numeric, { maximumFractionDigits: 1 })} yrs`
        }
        return formatNumberMetric(numeric, { maximumFractionDigits: 2 })
      }
      const text = String(value)
      return text.charAt(0).toUpperCase() + text.slice(1)
    },
    [formatCurrency, formatNumberMetric],
  )
  const summariseScenarioMetrics = useCallback(
    (metrics: Record<string, unknown> | null | undefined): ScenarioComparisonMetric[] => {
      if (!metrics) {
        return []
      }
      const selected: string[] = []
      for (const key of SCENARIO_METRIC_PRIORITY) {
        const value = metrics[key]
        if (value !== null && value !== undefined && value !== '') {
          selected.push(key)
        }
        if (selected.length >= 3) {
          break
        }
      }
      if (selected.length < 3) {
        for (const key of Object.keys(metrics)) {
          if (selected.length >= 3) {
            break
          }
          if (
            metrics[key] !== null &&
            metrics[key] !== undefined &&
            metrics[key] !== '' &&
            !selected.includes(key)
          ) {
            selected.push(key)
          }
        }
      }
      return selected.map((key) => ({
        key,
        label: formatMetricLabel(key),
        value: String(metrics[key]),
      }))
    },
    [formatMetricLabel],
  )
  const formatTimestamp = useCallback((value: string) => {
    const parsed = new Date(value)
    if (Number.isNaN(parsed.getTime())) {
      return value
    }
    return new Intl.DateTimeFormat('en-SG', {
      dateStyle: 'medium',
      timeStyle: 'short',
    }).format(parsed)
  }, [])
  const handleScenarioComparisonScroll = useCallback(() => {
    scenarioComparisonRef.current?.scrollIntoView({
      behavior: 'smooth',
      block: 'start',
    })
  }, [])

  const buildFeasibilitySignals = useCallback(
    (entry: QuickAnalysisEntry) => {
      const opportunities: string[] = []
      const risks: string[] = []
      const metrics = entry.metrics ?? {}

      const metric = (key: string) => safeNumber(metrics[key])

      switch (entry.scenario) {
        case 'raw_land': {
          const potentialGfa = metric('potential_gfa_sqm')
          const siteArea = metric('site_area_sqm')
          const plotRatio = metric('plot_ratio')
          if (potentialGfa && siteArea) {
            opportunities.push(
              `Potential GFA of ${formatNumberMetric(potentialGfa, {
                maximumFractionDigits: 0,
              })} sqm`,
            )
          }
          if (!plotRatio) {
            risks.push('Plot ratio unavailable — confirm URA control parameters.')
          }
          if (!siteArea) {
            risks.push('Site area missing — gather survey or title data.')
          }
          if (capturedProperty?.buildEnvelope) {
            const { maxBuildableGfaSqm, additionalPotentialGfaSqm, allowablePlotRatio } =
              capturedProperty.buildEnvelope
            if (maxBuildableGfaSqm) {
              opportunities.push(
                `Zoning envelope supports ≈ ${formatNumberMetric(maxBuildableGfaSqm, {
                  maximumFractionDigits: 0,
                })} sqm of GFA.`,
              )
            }
            if (additionalPotentialGfaSqm && additionalPotentialGfaSqm > 0) {
              opportunities.push(
                `Estimated uplift of ${formatNumberMetric(additionalPotentialGfaSqm, {
                  maximumFractionDigits: 0,
                })} sqm available under current controls.`,
              )
            } else if (additionalPotentialGfaSqm !== null && additionalPotentialGfaSqm !== undefined) {
              risks.push('No additional GFA headroom — optimisation required before submission.')
            }
            if (!plotRatio && allowablePlotRatio) {
              opportunities.push(
                `Plot ratio cap ${formatNumberMetric(allowablePlotRatio, {
                  maximumFractionDigits: 2,
                })} still allows refinement.`,
              )
            }
          }
          break
        }
        case 'existing_building': {
          const uplift = metric('gfa_uplift_sqm')
          const averagePsf = metric('average_psf_price')
          if (uplift && uplift > 0) {
            opportunities.push(
              `Unlock ≈ ${formatNumberMetric(uplift, {
                maximumFractionDigits: 0,
              })} sqm of additional GFA.`,
            )
          } else {
            risks.push('Limited GFA uplift — focus on retrofit efficiency.')
          }
          if (!averagePsf) {
            risks.push('No recent transaction comps — check market data sources.')
          }
          break
        }
        case 'heritage_property': {
          const heritageRisk = (metrics['heritage_risk'] ?? '').toString().toLowerCase()
          if (heritageRisk === 'high') {
            risks.push('High heritage risk — expect conservation dialogue.')
          } else if (heritageRisk === 'medium') {
            risks.push('Moderate heritage constraints — document mitigation plan.')
          } else {
            opportunities.push('Heritage considerations manageable based on current data.')
          }
          break
        }
        case 'underused_asset': {
          const mrtCount = metric('nearby_mrt_count')
          const averageRent = metric('average_monthly_rent')
          const buildingHeight = metric('building_height_m')
          if (mrtCount && mrtCount > 0) {
            opportunities.push(`${mrtCount} MRT stations support reuse potential.`)
          } else {
            risks.push('Limited transit access — budget for last-mile improvements.')
          }
          if (buildingHeight && buildingHeight < 20) {
            opportunities.push('Low-rise profile — vertical expansion is feasible.')
          }
          if (!averageRent) {
            risks.push('Missing rental comps — collect updated leasing benchmarks.')
          }
          break
        }
        case 'mixed_use_redevelopment': {
          const plotRatio = metric('plot_ratio')
          const useGroups = Array.isArray(metrics['use_groups'])
            ? (metrics['use_groups'] as string[])
            : []
          if (plotRatio && plotRatio > 0) {
            opportunities.push(`Zoning plot ratio ${plotRatio} supports higher density.`)
          }
          if (useGroups.length) {
            opportunities.push(`Permitted uses include: ${useGroups.join(', ')}.`)
          }
          if (!plotRatio) {
            risks.push('Plot ratio not defined — confirm with URA before design.')
          }
          break
        }
        default: {
          if (entry.notes.length) {
            opportunities.push(...entry.notes)
          }
        }
      }

      if (capturedProperty?.optimizations?.length) {
        const lead = capturedProperty.optimizations[0]
        const mixLabel = lead.assetType.replace(/_/g, ' ')
        opportunities.push(
          `${mixLabel.charAt(0).toUpperCase()}${mixLabel.slice(1)} holds ${formatNumberMetric(lead.allocationPct, {
            maximumFractionDigits: 0,
          })}% of the suggested programme, aligning with the current envelope.`,
        )
      }

      return { opportunities, risks }
    },
    [formatNumberMetric, capturedProperty],
  )
  const propertyInfoSummary = capturedProperty?.propertyInfo ?? null
  const zoningSummary = capturedProperty?.uraZoning ?? null
  const nearestMrtStation =
    capturedProperty?.nearbyAmenities?.mrtStations?.[0] ?? null
  const nearestBusStop =
    capturedProperty?.nearbyAmenities?.busStops?.[0] ?? null

  const propertyOverviewCards = useMemo(() => {
    if (!capturedProperty) {
      return []
    }

    const info = propertyInfoSummary
    const zoning = zoningSummary
    const envelope = capturedProperty.buildEnvelope
    const visualization = capturedProperty.visualization ?? {
      status: 'placeholder',
      previewAvailable: false,
      notes: [],
      conceptMeshUrl: null,
      previewMetadataUrl: null,
      thumbnailUrl: null,
      cameraOrbitHint: null,
      previewSeed: null,
      previewJobId: null,
      massingLayers: [],
      colorLegend: [],
    }
    const optimizations = capturedProperty.optimizations ?? []
    const financialSummary = capturedProperty.financialSummary
    const heritageContext = capturedProperty.heritageContext

    const formatArea = (value: number | null | undefined) => {
      if (value === null || value === undefined) {
        return '—'
      }
      const precision = value >= 1000 ? 0 : 2
      return `${formatNumberMetric(value, { maximumFractionDigits: precision })} sqm`
    }

    const formatHeight = (value: number | null | undefined) => {
      if (value === null || value === undefined) {
        return '—'
      }
      return `${formatNumberMetric(value, { maximumFractionDigits: 1 })} m`
    }

    const formatPlotRatio = (value: number | null | undefined) => {
      if (value === null || value === undefined) {
        return '—'
      }
      return formatNumberMetric(value, { maximumFractionDigits: 2 })
    }

    const formatSiteCoverage = (value: number | null | undefined) => {
      if (value === null || value === undefined) {
        return '—'
      }
      let percent = value
      if (percent <= 1) {
        percent = percent * 100
      }
      return `${formatNumberMetric(percent, {
        maximumFractionDigits: percent >= 100 ? 0 : 1,
      })}%`
    }

    const formatDistance = (value: number | null | undefined) => {
      if (value === null || value === undefined) {
        return '—'
      }
      if (value >= 1000) {
        return `${formatNumberMetric(value / 1000, {
          maximumFractionDigits: 1,
        })} km`
      }
      return `${formatNumberMetric(value, { maximumFractionDigits: 0 })} m`
    }

    const formatDate = (value: string | null | undefined) => {
      if (!value) {
        return '—'
      }
      const parsed = new Date(value)
      if (Number.isNaN(parsed.getTime())) {
        return value
      }
      return new Intl.DateTimeFormat('en-SG', {
        year: 'numeric',
        month: 'short',
        day: 'numeric',
      }).format(parsed)
    }

    const cards: Array<{
      title: string
      subtitle?: string | null
      items: Array<{ label: string; value: string }>
      tags?: string[]
      note?: string | null
    }> = []

    cards.push({
      title: 'Location & tenure',
      items: [
        {
          label: 'Address',
          value: capturedProperty.address.fullAddress || '—',
        },
        {
          label: 'District',
          value: capturedProperty.address.district || '—',
        },
        {
          label: 'Tenure',
          value: info?.tenure ?? '—',
        },
        {
          label: 'Completion year',
          value: info?.completionYear
            ? formatNumberMetric(info.completionYear, {
                maximumFractionDigits: 0,
              })
            : '—',
        },
      ],
    })

    cards.push({
      title: 'Build envelope',
      subtitle: envelope.zoneDescription ?? envelope.zoneCode ?? 'Zoning envelope preview',
      items: [
        { label: 'Zone code', value: envelope.zoneCode ?? '—' },
        {
          label: 'Allowable plot ratio',
          value: formatPlotRatio(envelope.allowablePlotRatio),
        },
        { label: 'Site area', value: formatArea(envelope.siteAreaSqm) },
        {
          label: 'Max buildable GFA',
          value: formatArea(envelope.maxBuildableGfaSqm),
        },
        {
          label: 'Current GFA',
          value: formatArea(envelope.currentGfaSqm),
        },
        {
          label: 'Additional potential',
          value: formatArea(envelope.additionalPotentialGfaSqm),
        },
      ],
      note: envelope.assumptions?.length ? envelope.assumptions[0] : null,
    })

    if (heritageContext) {
      const riskLabel = heritageContext.risk
        ? heritageContext.risk.toUpperCase()
        : 'UNKNOWN'
      const overlay = heritageContext.overlay

      const heritageItems: Array<{ label: string; value: string }> = [
        {
          label: 'Risk level',
          value: riskLabel,
        },
      ]

      if (overlay?.name) {
        heritageItems.push({ label: 'Overlay name', value: overlay.name })
      }
      if (overlay?.source) {
        heritageItems.push({ label: 'Source', value: overlay.source })
      }
      if (overlay?.heritagePremiumPct != null) {
        heritageItems.push({
          label: 'Premium (optimiser)',
          value: `${formatNumberMetric(overlay.heritagePremiumPct, {
            maximumFractionDigits: overlay.heritagePremiumPct >= 100 ? 0 : 1,
          })}%`,
        })
      }
      if (heritageContext.constraints.length) {
        heritageItems.push({
          label: 'Key constraints',
          value: heritageContext.constraints.slice(0, 2).join(' • '),
        })
      }

      cards.push({
        title: 'Heritage context',
        subtitle: overlay?.name ?? 'Heritage assessment',
        items: heritageItems,
        tags: heritageContext.flag ? [riskLabel] : undefined,
        note: heritageContext.assumption ?? heritageContext.notes[0] ?? null,
      })
    }

    if (previewJob) {
      const statusLabel = previewJob.status.toUpperCase()
      const statusLower = previewJob.status.toLowerCase()
      const previewItems: Array<{ label: string; value: string }> = [
        { label: 'Status', value: statusLabel },
        { label: 'Scenario', value: previewJob.scenario },
        {
          label: 'Requested',
          value: previewJob.requestedAt ? formatTimestamp(previewJob.requestedAt) : '—',
        },
      ]
      if (previewJob.startedAt) {
        previewItems.push({
          label: 'Started',
          value: formatTimestamp(previewJob.startedAt),
        })
      }
      if (previewJob.finishedAt) {
        previewItems.push({
          label: 'Finished',
          value: formatTimestamp(previewJob.finishedAt),
        })
      }
      if (previewJob.previewUrl) {
        previewItems.push({ label: 'Preview URL', value: previewJob.previewUrl })
      }
      if (previewJob.metadataUrl) {
        previewItems.push({ label: 'Metadata', value: previewJob.metadataUrl })
      }
      if (previewJob.thumbnailUrl) {
        previewItems.push({ label: 'Thumbnail', value: previewJob.thumbnailUrl })
      }
      if (previewJob.assetVersion) {
        previewItems.push({ label: 'Asset version', value: previewJob.assetVersion })
      }
      if (previewJob.message) {
        previewItems.push({ label: 'Notes', value: previewJob.message })
      }

      let previewNote: string | null = previewJob.message ?? null
      if (!previewNote) {
        if (statusLower === 'ready') {
          previewNote = 'Concept mesh ready for review.'
        } else if (statusLower === 'failed') {
          previewNote = 'Preview generation failed — try refreshing.'
        } else if (statusLower === 'expired') {
          previewNote = 'Preview expired — refresh to regenerate assets.'
        } else {
          previewNote = 'Preview job processing — status updates every few seconds.'
        }
      }

      cards.push({
        title: 'Preview generation',
        subtitle: `Job ${previewJob.id.slice(0, 8)}…`,
        items: previewItems,
        tags: [statusLabel],
        note: previewNote,
      })
    }

    if (optimizations.length > 0) {
      const formatAllocation = (plan: DeveloperAssetOptimization) => {
        const segments: string[] = [
          `${formatNumberMetric(plan.allocationPct, { maximumFractionDigits: 0 })}%`,
        ]
        if (plan.allocatedGfaSqm != null) {
          segments.push(
            `${formatNumberMetric(
              plan.allocatedGfaSqm >= 1000
                ? plan.allocatedGfaSqm / 1000
                : plan.allocatedGfaSqm,
              {
                maximumFractionDigits: plan.allocatedGfaSqm >= 1000 ? 1 : 0,
              },
            )}${plan.allocatedGfaSqm >= 1000 ? 'k' : ''} sqm`,
          )
        }
        if (plan.niaEfficiency != null) {
          segments.push(
            `NIA ${formatNumberMetric(plan.niaEfficiency * 100, {
              maximumFractionDigits: plan.niaEfficiency * 100 >= 100 ? 0 : 1,
            })}%`,
          )
        }
        if (plan.targetFloorHeightM != null) {
          segments.push(
            `${formatNumberMetric(plan.targetFloorHeightM, {
              maximumFractionDigits: 1,
            })} m floor height`,
          )
        }
        if (plan.parkingRatioPer1000Sqm != null) {
          segments.push(
            `${formatNumberMetric(plan.parkingRatioPer1000Sqm, {
              maximumFractionDigits: 1,
            })} lots / 1,000 sqm`,
          )
        }
        if (plan.estimatedRevenueSgd != null && plan.estimatedRevenueSgd > 0) {
          segments.push(
            `Rev ≈ $${formatNumberMetric(plan.estimatedRevenueSgd / 1_000_000, {
              maximumFractionDigits: 1,
            })}M`,
          )
        }
        if (plan.estimatedCapexSgd != null && plan.estimatedCapexSgd > 0) {
          segments.push(
            `CAPEX ≈ $${formatNumberMetric(plan.estimatedCapexSgd / 1_000_000, {
              maximumFractionDigits: 1,
            })}M`,
          )
        }
        if (plan.riskLevel) {
          const riskLabel = `${plan.riskLevel.charAt(0).toUpperCase()}${plan.riskLevel.slice(1)}`
          segments.push(
            `${riskLabel} risk${
              plan.absorptionMonths ? ` · ~${formatNumberMetric(plan.absorptionMonths, { maximumFractionDigits: 0 })}m absorption` : ''
            }`,
          )
        }
        return segments.join(' • ')
      }

      cards.push({
        title: 'Recommended asset mix',
        subtitle: 'Initial allocation guidance',
        items: optimizations.map((plan) => ({
          label: plan.assetType,
          value: formatAllocation(plan),
        })),
        note:
          optimizations.find((plan) => plan.notes.length)?.notes[0] ??
          'Adjust allocations as feasibility modelling matures.',
      })
    }

    const financeNote =
      financialSummary.notes.length > 0
        ? financialSummary.notes[0]
        : 'Sync with finance modelling to validate programme-level cash flows.'

    const financialItems: Array<{ label: string; value: string }> = [
      {
        label: 'Total estimated revenue',
        value:
          financialSummary.totalEstimatedRevenueSgd != null
            ? `$${formatNumberMetric(
                financialSummary.totalEstimatedRevenueSgd / 1_000_000,
                { maximumFractionDigits: 1 },
              )}M`
            : '—',
      },
      {
        label: 'Total estimated capex',
        value:
          financialSummary.totalEstimatedCapexSgd != null
            ? `$${formatNumberMetric(
                financialSummary.totalEstimatedCapexSgd / 1_000_000,
                { maximumFractionDigits: 1 },
              )}M`
            : '—',
      },
      {
        label: 'Dominant risk',
        value:
          financialSummary.dominantRiskProfile
            ? financialSummary.dominantRiskProfile.replace('_', ' ')
            : '—',
      },
    ]

    const financeBlueprint = financialSummary.financeBlueprint
    if (financeBlueprint?.capitalStructure.length) {
      const baseScenario =
        financeBlueprint.capitalStructure.find((entry) => entry.scenario === 'Base Case') ??
        financeBlueprint.capitalStructure[0]
      financialItems.push({
        label: 'Capital stack (base)',
        value: `${formatNumberMetric(baseScenario.debtPct, {
          maximumFractionDigits: 0,
        })}% debt / ${formatNumberMetric(baseScenario.equityPct, {
          maximumFractionDigits: 0,
        })}% equity`,
      })
    }
    if (financeBlueprint?.debtFacilities.length) {
      const constructionLoan = financeBlueprint.debtFacilities.find(
        (facility) => facility.facilityType.toLowerCase().includes('construction'),
      )
      if (constructionLoan) {
        financialItems.push({
          label: 'Construction loan rate',
          value: constructionLoan.interestRate,
        })
      }
    }

    cards.push({
      title: 'Financial snapshot',
      subtitle: 'Optimisation-derived rollup',
      items: financialItems,
      note: financeNote,
    })

    if (visualization) {
      const visualizationItems: Array<{ label: string; value: string }> = [
        {
          label: 'Preview status',
          value: visualization.previewAvailable ? 'High-fidelity preview ready' : 'Waiting on Phase 2B visuals',
        },
        {
          label: 'Status flag',
          value: visualization.status ? visualization.status.replace(/_/g, ' ') : 'Pending',
        },
        {
          label: 'Concept mesh',
          value: visualization.conceptMeshUrl ?? 'Stub not generated yet',
        },
        {
          label: 'Camera orbit hint',
          value: visualization.cameraOrbitHint
            ? `${formatNumberMetric(visualization.cameraOrbitHint.theta ?? 0, {
                  maximumFractionDigits: 0,
                })}° / ${formatNumberMetric(visualization.cameraOrbitHint.phi ?? 0, {
                  maximumFractionDigits: 0,
                })}°`
            : '—',
        },
      ]

      if (visualization.massingLayers?.length > 0) {
        const primaryLayer = visualization.massingLayers[0]
        const layerLabel = primaryLayer.assetType
          .replace(/[_-]/g, ' ')
          .replace(/\b\w/g, (match) => match.toUpperCase())
        const heightValue =
          primaryLayer.estimatedHeightM != null
            ? `${formatNumberMetric(primaryLayer.estimatedHeightM, {
                maximumFractionDigits: 0,
              })} m`
            : '—'
        visualizationItems.push({
          label: 'Primary massing',
          value: `${layerLabel} · ${heightValue}`,
        })
      }

      if (colorLegendEntries.length > 0) {
        const legendPreview = colorLegendEntries
          .slice(0, 3)
          .map((entry) => entry.label)
          .join(', ')
        visualizationItems.push({
          label: 'Colour legend',
          value: legendPreview || '—',
        })
      }

      cards.push({
        title: 'Visualization readiness',
        subtitle: visualization.previewAvailable ? 'Preview ready' : 'Preview in progress',
        items: visualizationItems,
        note: visualization.notes?.length ? visualization.notes[0] : null,
      })
    }

    cards.push({
      title: 'Site metrics',
      items: [
        { label: 'Site area', value: formatArea(info?.siteAreaSqm) },
        { label: 'Approved GFA', value: formatArea(info?.gfaApproved) },
        { label: 'Building height', value: formatHeight(info?.buildingHeight) },
        {
          label: 'Plot ratio',
          value: formatPlotRatio(zoning?.plotRatio),
        },
      ],
    })

    cards.push({
      title: 'Zoning & planning',
      subtitle:
        zoning?.zoneDescription ??
        zoning?.zoneCode ??
        'Zoning details unavailable',
      items: [
        {
          label: 'Building height limit',
          value: formatHeight(zoning?.buildingHeightLimit),
        },
        {
          label: 'Site coverage',
          value:
            zoning?.siteCoverage !== null && zoning?.siteCoverage !== undefined
              ? formatSiteCoverage(zoning.siteCoverage)
              : '—',
        },
        {
          label: 'Special conditions',
          value: zoning?.specialConditions ?? '—',
        },
      ],
      tags: zoning?.useGroups ?? [],
    })

    cards.push({
      title: 'Market & connectivity',
      items: [
        {
          label: 'Existing use',
          value:
            capturedProperty.existingUse && capturedProperty.existingUse.trim()
              ? capturedProperty.existingUse
              : '—',
        },
        {
          label: 'Last transaction',
          value:
            info?.lastTransactionDate || info?.lastTransactionPrice
              ? [
                  formatDate(info?.lastTransactionDate),
                  info?.lastTransactionPrice
                    ? formatCurrency(info.lastTransactionPrice)
                    : null,
                ]
                  .filter(Boolean)
                  .join(' · ')
              : '—',
        },
        {
          label: 'Nearest MRT',
          value: nearestMrtStation
            ? `${nearestMrtStation.name} (${formatDistance(
                nearestMrtStation.distanceM,
              )})`
            : '—',
        },
        {
          label: 'Nearest bus stop',
          value: nearestBusStop
            ? `${nearestBusStop.name} (${formatDistance(
                nearestBusStop.distanceM,
              )})`
            : '—',
        },
      ],
      note: `Lat ${formatNumberMetric(
        capturedProperty.coordinates.latitude,
        { maximumFractionDigits: 6 },
      )}, Lon ${formatNumberMetric(capturedProperty.coordinates.longitude, {
        maximumFractionDigits: 6,
      })}`,
    })

    return cards
  }, [
    capturedProperty,
    formatCurrency,
    formatNumberMetric,
    formatTimestamp,
    propertyInfoSummary,
    zoningSummary,
    nearestBusStop,
    nearestMrtStation,
    previewJob,
    colorLegendEntries,
  ])

  const layerBreakdown = useMemo(() => {
    const layers = capturedProperty?.visualization?.massingLayers ?? []
    if (!layers.length) {
      return []
    }

    const legendLookup = new Map(
      colorLegendEntries.map((entry) => [entry.assetType.toLowerCase(), entry]),
    )

    const formatAreaValue = (value: number | null | undefined) => {
      if (value === null || value === undefined) {
        return '—'
      }
      const precision = value >= 1000 ? 0 : 2
      return `${formatNumberMetric(value, { maximumFractionDigits: precision })} sqm`
    }

    const formatHeightValue = (value: number | null | undefined) => {
      if (value === null || value === undefined) {
        return '—'
      }
      return `${formatNumberMetric(value, { maximumFractionDigits: 1 })} m`
    }

    return layers.map((layer, index) => {
      const legend = legendLookup.get(layer.assetType.toLowerCase())
      const allocationValue =
        layer.allocationPct !== null && layer.allocationPct !== undefined
          ? `${formatNumberMetric(layer.allocationPct, { maximumFractionDigits: 0 })}%`
          : '—'

      // Use legend label if available, otherwise title-case asset type
      const displayLabel = legend?.label ?? toTitleCase(layer.assetType)

      const subtitle = allocationValue !== '—'
        ? `${toTitleCase(layer.assetType)} · ${allocationValue}`
        : toTitleCase(layer.assetType)

      return {
        id: `${layer.assetType}-${index}`,
        label: displayLabel,
        subtitle,
        color: legend?.color ?? layer.color ?? '#4f46e5',
        description: legend?.description ?? null,
        metrics: [
          { label: 'Allocation', value: allocationValue },
          { label: 'GFA', value: formatAreaValue(layer.gfaSqm) },
          { label: 'NIA', value: formatAreaValue(layer.niaSqm) },
          { label: 'Height', value: formatHeightValue(layer.estimatedHeightM) },
        ],
      }
    })
  }, [colorLegendEntries, capturedProperty?.visualization?.massingLayers, formatNumberMetric])

  useEffect(() => {
    if (scenarioOverrideEntries.length === 0) {
      if (scenarioComparisonBase !== null) {
        setScenarioComparisonBase(null)
      }
      return
    }
    if (
      !scenarioComparisonBase ||
      !scenarioOverrideEntries.some(
        (assessment) => assessment.scenario === scenarioComparisonBase,
      )
    ) {
      setScenarioComparisonBase(scenarioOverrideEntries[0].scenario)
    }
  }, [scenarioOverrideEntries, scenarioComparisonBase])

  const baseScenarioAssessment = useMemo(() => {
    if (scenarioOverrideEntries.length === 0) {
      return null
    }
    if (!scenarioComparisonBase) {
      return scenarioOverrideEntries[0]
    }
    return (
      scenarioOverrideEntries.find(
        (assessment) => assessment.scenario === scenarioComparisonBase,
      ) ?? scenarioOverrideEntries[0]
    )
  }, [scenarioOverrideEntries, scenarioComparisonBase])

  const scenarioComparisonEntries = useMemo(() => {
    if (!baseScenarioAssessment) {
      return []
    }
    return scenarioOverrideEntries.filter(
      (assessment) => assessment.scenario !== baseScenarioAssessment.scenario,
    )
  }, [scenarioOverrideEntries, baseScenarioAssessment])
  const feasibilitySignals = useMemo(() => {
    if (!quickAnalysisScenarios.length) {
      return []
    }
    return quickAnalysisScenarios.map((entry) => {
      const scenario =
        typeof entry.scenario === 'string' && entry.scenario
          ? (entry.scenario as DevelopmentScenario)
          : 'raw_land'
      const label = scenarioLookup.get(scenario)?.label ?? formatScenarioLabel(scenario)
      const signals = buildFeasibilitySignals(entry)
      return {
        scenario,
        label,
        opportunities: signals.opportunities,
        risks: signals.risks,
      }
    })
  }, [
    quickAnalysisScenarios,
    scenarioLookup,
    buildFeasibilitySignals,
    formatScenarioLabel,
  ])

  const describeRatingChange = useCallback(
    (current: string, reference: string) => {
      const currentIndex = CONDITION_RATINGS.indexOf(current)
      const referenceIndex = CONDITION_RATINGS.indexOf(reference)
      if (currentIndex === -1 || referenceIndex === -1) {
        if (current === reference) {
          return { text: 'Rating unchanged.', tone: 'neutral' as const }
        }
        return {
          text: `Rating changed from ${reference} to ${current}.`,
          tone: 'neutral' as const,
        }
      }
      if (currentIndex === referenceIndex) {
        return { text: 'Rating unchanged.', tone: 'neutral' as const }
      }
      if (currentIndex < referenceIndex) {
        return {
          text: `Rating improved from ${reference} to ${current}.`,
          tone: 'positive' as const,
        }
      }
      return {
        text: `Rating declined from ${reference} to ${current}.`,
        tone: 'negative' as const,
      }
    },
    [],
  )

  const describeRiskChange = useCallback(
    (current: string, reference: string) => {
      const currentIndex = CONDITION_RISK_LEVELS.indexOf(current)
      const referenceIndex = CONDITION_RISK_LEVELS.indexOf(reference)
      if (currentIndex === -1 || referenceIndex === -1) {
        if (current === reference) {
          return { text: 'Risk level unchanged.', tone: 'neutral' as const }
        }
        return {
          text: `Risk level changed from ${reference} to ${current}.`,
          tone: 'neutral' as const,
        }
      }
      if (currentIndex === referenceIndex) {
        return { text: 'Risk level unchanged.', tone: 'neutral' as const }
      }
      if (currentIndex < referenceIndex) {
        return {
          text: `Risk eased from ${reference} to ${current}.`,
          tone: 'positive' as const,
        }
      }
      return {
        text: `Risk intensified from ${reference} to ${current}.`,
        tone: 'negative' as const,
      }
    },
    [],
  )

  const latestAssessmentEntry = useMemo(
    () => (assessmentHistory.length > 0 ? assessmentHistory[0] : null),
    [assessmentHistory],
  )
  const previousAssessmentEntry = useMemo(
    () => (assessmentHistory.length > 1 ? assessmentHistory[1] : null),
    [assessmentHistory],
  )
  const systemComparisons = useMemo(() => {
    if (!latestAssessmentEntry && !previousAssessmentEntry) {
      return []
    }
    const names = new Set<string>()
    ;(latestAssessmentEntry?.systems ?? []).forEach((system) => {
      names.add(system.name)
    })
    ;(previousAssessmentEntry?.systems ?? []).forEach((system) => {
      names.add(system.name)
    })
    return Array.from(names).map((name) => {
      const latestSystem =
        latestAssessmentEntry?.systems.find((system) => system.name === name) ?? null
      const previousSystem =
        previousAssessmentEntry?.systems.find((system) => system.name === name) ?? null
      const scoreDelta =
        latestSystem && previousSystem
          ? latestSystem.score - previousSystem.score
          : undefined
      return {
        name,
        latest: latestSystem,
        previous: previousSystem,
        scoreDelta,
      }
    })
  }, [latestAssessmentEntry, previousAssessmentEntry])
  const systemComparisonMap = useMemo(
    () => new Map(systemComparisons.map((entry) => [entry.name, entry])),
    [systemComparisons],
  )
  const systemTrendInsights = useMemo(() => {
    if (systemComparisons.length === 0) {
      return []
    }
    const insights = systemComparisons
      .map((entry) => {
        if (!entry.latest) {
          return null
        }
        const delta =
          typeof entry.scoreDelta === 'number' && Number.isFinite(entry.scoreDelta)
            ? entry.scoreDelta
            : null
        const severity = classifySystemSeverity(entry.latest.rating, delta)
        if (severity === 'neutral') {
          return null
        }
        const previousRating = entry.previous?.rating ?? null
        const previousScore =
          typeof entry.previous?.score === 'number' ? entry.previous.score : null
        let detail: string
        if (delta !== null && delta !== 0 && previousRating && previousScore !== null) {
          const deltaLabel = formatScoreDelta(delta)
          detail = `${entry.name} ${deltaLabel} vs last inspection (${previousRating} · ${previousScore}/100 → ${entry.latest.rating} · ${entry.latest.score}/100).`
        } else if (delta !== null && delta !== 0) {
          const deltaLabel = formatScoreDelta(delta)
          detail = `${entry.name} ${deltaLabel}; now ${entry.latest.rating} · ${entry.latest.score}/100.`
        } else if (previousRating) {
          detail = `${entry.name} holds at ${entry.latest.rating} · ${entry.latest.score}/100 (was ${previousRating}).`
        } else {
          detail = `${entry.name} recorded as ${entry.latest.rating} · ${entry.latest.score}/100.`
        }
        return {
          id: `trend-${slugify(entry.name)}`,
          severity,
          title: buildSystemInsightTitle(entry.name, severity, delta),
          detail,
          specialist: systemSpecialistHint(entry.name),
        }
      })
      .filter((value): value is ConditionInsightView => value !== null)

    insights.sort((a, b) => {
      const severityRank = insightSeverityOrder[a.severity] - insightSeverityOrder[b.severity]
      if (severityRank !== 0) {
        return severityRank
      }
      return a.title.localeCompare(b.title)
    })

    return insights.slice(0, 3)
  }, [systemComparisons])
  const backendInsightViews = useMemo<ConditionInsightView[]>(() => {
    if (!conditionAssessment?.insights) {
      return []
    }
    return conditionAssessment.insights.map((insight, index) => ({
      id: insight.id || `backend-${index}`,
      severity: normaliseInsightSeverity(insight.severity),
      title: insight.title,
      detail: insight.detail,
      specialist: insight.specialist ?? null,
    }))
  }, [conditionAssessment?.insights])
  const combinedConditionInsights = useMemo<ConditionInsightView[]>(() => {
    const merged = new Map<string, ConditionInsightView>()
    backendInsightViews.forEach((insight, index) => {
      const key = insight.id || `backend-${index}`
      merged.set(key, { ...insight, id: key })
    })
    systemTrendInsights.forEach((insight) => {
      merged.set(insight.id, insight)
    })
    return Array.from(merged.values())
  }, [backendInsightViews, systemTrendInsights])
  const backendInsightCount = backendInsightViews.length
  const trendInsightCount = systemTrendInsights.length
  const insightSubtitle =
    backendInsightCount > 0 && trendInsightCount > 0
      ? 'Heuristic insights combined with inspection deltas.'
      : backendInsightCount > 0
      ? 'Heuristic insights generated from property data and specialist playbooks.'
      : 'Inspection deltas compared with previous assessments.'
  const scenarioComparisonData = useMemo<ScenarioComparisonDatum[]>(() => {
    const scenarioOrder = new Map(
      DEFAULT_SCENARIO_ORDER.map((scenario, index) => [scenario, index]),
    )
    const keys = new Set<ScenarioComparisonKey>()
    keys.add('all')
    quickAnalysisScenarios.forEach((scenario) => {
      if (typeof scenario.scenario === 'string') {
        keys.add(scenario.scenario as DevelopmentScenario)
      }
    })
    Object.keys(scenarioChecklistProgress).forEach((scenario) => {
      keys.add(scenario as DevelopmentScenario)
    })
    scenarioAssessments.forEach((assessment) => {
      if (assessment.scenario) {
        keys.add(assessment.scenario)
      }
    })

    const sorted = Array.from(keys).sort((a, b) => {
      if (a === 'all') return -1
      if (b === 'all') return 1
      return (scenarioOrder.get(a) ?? 999) - (scenarioOrder.get(b) ?? 999)
    })

    return sorted.map((scenarioKey) => {
      const isAll = scenarioKey === 'all'
      const option = !isAll
        ? scenarioLookup.get(scenarioKey as DevelopmentScenario)
        : null
      const label = isAll
        ? 'All scenarios'
        : option?.label ?? formatScenarioLabel(scenarioKey as DevelopmentScenario)
      const icon = isAll ? '🌐' : option?.icon ?? '🏗️'

      let quickHeadline: string | null = null
      let quickMetrics: ScenarioComparisonMetric[] = []
      if (isAll) {
        const scenarioCount = Math.max(sorted.length - 1, 0)
        quickHeadline = `Aggregate across ${scenarioCount} tracked scenarios.`
        if (displaySummary) {
          quickMetrics = [
            {
              key: 'checklist',
              label: 'Checklist',
              value: `${displaySummary.completed}/${displaySummary.total}`,
            },
            {
              key: 'completion',
              label: 'Completion',
              value: `${displaySummary.completionPercentage}%`,
            },
          ]
        }
      } else {
        const quickEntry = quickAnalysisScenarios.find(
          (entry) => entry.scenario === scenarioKey,
        )
        quickHeadline = quickEntry?.headline ?? null
        quickMetrics = summariseScenarioMetrics(quickEntry?.metrics ?? {})
      }

      const checklistEntry = isAll
        ? displaySummary
        : scenarioChecklistProgress[scenarioKey as DevelopmentScenario]
      const checklistCompleted =
        typeof checklistEntry?.completed === 'number'
          ? checklistEntry.completed
          : null
      const checklistTotal =
        typeof checklistEntry?.total === 'number' ? checklistEntry.total : null
      const checklistPercent =
        checklistCompleted !== null &&
        checklistTotal &&
        checklistTotal > 0
          ? Math.round((checklistCompleted / checklistTotal) * 100)
          : null

      let conditionEntry: ConditionAssessment | null = null
      if (isAll) {
        if (
          conditionAssessment &&
          (!conditionAssessment.scenario || conditionAssessment.scenario === 'all')
        ) {
          conditionEntry = conditionAssessment
        }
      } else {
        const mapped = scenarioAssessmentsMap.get(
          scenarioKey as DevelopmentScenario,
        )
        if (mapped) {
          conditionEntry = mapped
        } else if (conditionAssessment?.scenario === scenarioKey) {
          conditionEntry = conditionAssessment
        }
      }

      const insights = isAll
        ? combinedConditionInsights
        : convertAssessmentInsights(conditionEntry)
      const sortedInsights = [...insights].sort((a, b) => {
        const rankA = insightSeverityOrder[a.severity]
        const rankB = insightSeverityOrder[b.severity]
        if (rankA !== rankB) {
          return rankA - rankB
        }
        return a.title.localeCompare(b.title)
      })
      const primaryInsight = sortedInsights[0] ?? null

      const conditionRating = conditionEntry?.overallRating ?? null
      const conditionScore =
        typeof conditionEntry?.overallScore === 'number'
          ? conditionEntry.overallScore
          : typeof conditionEntry?.overallScore === 'string'
          ? Number(conditionEntry.overallScore)
          : null
      const riskLevel = conditionEntry?.riskLevel ?? null
      const recommendedAction = isAll
        ? conditionAssessment?.recommendedActions?.[0] ?? null
        : conditionEntry?.recommendedActions?.[0] ?? null
      const inspectorName =
        conditionEntry?.inspectorName ??
        (isAll ? conditionAssessment?.inspectorName ?? null : null)
      const recordedAt =
        conditionEntry?.recordedAt ??
        (isAll ? conditionAssessment?.recordedAt ?? null : null)
      const source: 'manual' | 'heuristic' =
        conditionEntry && conditionEntry.recordedAt ? 'manual' : 'heuristic'

      return {
        key: scenarioKey,
        label,
        icon,
        quickHeadline,
        quickMetrics,
        conditionRating,
        conditionScore,
        riskLevel,
        checklistCompleted,
        checklistTotal,
        checklistPercent,
        insights,
        primaryInsight,
        recommendedAction,
        recordedAt,
        inspectorName,
        source,
      }
    })
  }, [
    quickAnalysisScenarios,
    scenarioChecklistProgress,
    scenarioAssessments,
    scenarioAssessmentsMap,
    conditionAssessment,
    combinedConditionInsights,
    displaySummary,
    scenarioLookup,
    formatScenarioLabel,
    summariseScenarioMetrics,
    convertAssessmentInsights,
  ])
  const scenarioComparisonTableRows = useMemo(
    () => scenarioComparisonData.filter((row) => row.key !== 'all'),
    [scenarioComparisonData],
  )
  const scenarioComparisonVisible = scenarioComparisonTableRows.length > 0
  useEffect(() => {
    if (!capturedProperty || !capturedProperty.quickAnalysis) {
      if (comparisonSnapshotSignatureRef.current !== null) {
        comparisonSnapshotSignatureRef.current = null
        setQuickAnalysisHistory([])
      }
      return
    }
    if (scenarioComparisonData.length === 0) {
      return
    }

    const comparisonSnapshot = scenarioComparisonData.map((row, index) => ({
      ...row,
      quickMetrics: row.quickMetrics.map((metric) => ({ ...metric })),
      insights: row.insights.map((insight, insightIndex) => ({
        ...insight,
        id: insight.id || `snapshot-${index}-${insightIndex}`,
      })),
      primaryInsight: row.primaryInsight ? { ...row.primaryInsight } : null,
    }))

    const signatureParts = [
      capturedProperty.propertyId,
      capturedProperty.quickAnalysis.generatedAt,
      ...comparisonSnapshot.map((row) =>
        [
          row.key,
          row.conditionRating ?? '',
          row.conditionScore ?? '',
          row.riskLevel ?? '',
          row.quickMetrics.map((metric) => `${metric.label}:${metric.value ?? ''}`).join(
            ',',
          ),
          row.primaryInsight?.id ?? '',
          row.recommendedAction ?? '',
        ].join('#'),
      ),
    ]
    const signature = signatureParts.join('|')
    if (comparisonSnapshotSignatureRef.current === signature) {
      return
    }
    comparisonSnapshotSignatureRef.current = signature

    const snapshot: QuickAnalysisSnapshot = {
      propertyId: capturedProperty.propertyId,
      generatedAt: capturedProperty.quickAnalysis.generatedAt,
      scenarios: capturedProperty.quickAnalysis.scenarios,
      comparison: comparisonSnapshot,
    }

    setQuickAnalysisHistory((previous) => {
      const sameProperty = previous.filter(
        (entry) => entry.propertyId === snapshot.propertyId,
      )
      const withoutTimestamp = sameProperty.filter(
        (entry) => entry.generatedAt !== snapshot.generatedAt,
      )
      return [snapshot, ...withoutTimestamp].slice(0, QUICK_ANALYSIS_HISTORY_LIMIT)
    })
  }, [capturedProperty, scenarioComparisonData])
  const activeScenarioSummary = useMemo(() => {
    const targetKey: ScenarioComparisonKey =
      activeScenario === 'all' ? 'all' : (activeScenario as DevelopmentScenario)
    const row = scenarioComparisonData.find((entry) => entry.key === targetKey)
    if (!row) {
      const scenarioCount = Math.max(scenarioFocusOptions.length - 1, 0)
      return {
        label: targetKey === 'all' ? 'All scenarios' : formatScenarioLabel(targetKey),
        headline:
          scenarioCount > 0
            ? `${scenarioCount} tracked scenarios`
            : 'No scenarios selected yet',
        detail: null as string | null,
      }
    }

    const headline =
      row.quickHeadline ??
      (row.conditionRating
        ? `Condition ${row.conditionRating}${
            row.conditionScore !== null ? ` · ${row.conditionScore}/100` : ''
          }`
        : 'Scenario summary unavailable')
    const detailMetric = row.quickMetrics[0]
    const detail = detailMetric
      ? `${detailMetric.label}: ${detailMetric.value}`
      : null

    return {
      label: row.label,
      headline,
      detail,
    }
  }, [
    activeScenario,
    scenarioComparisonData,
    scenarioFocusOptions.length,
    formatScenarioLabel,
  ])
  const recommendedActionDiff = useMemo(() => {
    if (!latestAssessmentEntry || !previousAssessmentEntry) {
      return { newActions: [], clearedActions: [] }
    }
    const latestSet = new Set(latestAssessmentEntry.recommendedActions)
    const previousSet = new Set(previousAssessmentEntry.recommendedActions)
    const newActions = Array.from(latestSet).filter((action) => !previousSet.has(action))
    const clearedActions = Array.from(previousSet).filter(
      (action) => !latestSet.has(action),
    )
    return { newActions, clearedActions }
  }, [latestAssessmentEntry, previousAssessmentEntry])
  const comparisonSummary = useMemo(() => {
    if (!latestAssessmentEntry || !previousAssessmentEntry) {
      return null
    }
    const scoreDelta = latestAssessmentEntry.overallScore - previousAssessmentEntry.overallScore
    const latestRatingIndex = CONDITION_RATINGS.indexOf(latestAssessmentEntry.overallRating)
    const previousRatingIndex = CONDITION_RATINGS.indexOf(previousAssessmentEntry.overallRating)
    let ratingTrend: 'improved' | 'declined' | 'same' | 'changed' = 'same'
    if (latestRatingIndex !== -1 && previousRatingIndex !== -1) {
      if (latestRatingIndex < previousRatingIndex) {
        ratingTrend = 'improved'
      } else if (latestRatingIndex > previousRatingIndex) {
        ratingTrend = 'declined'
      } else {
        ratingTrend = 'same'
      }
    } else if (latestAssessmentEntry.overallRating !== previousAssessmentEntry.overallRating) {
      ratingTrend = 'changed'
    }
    const latestRiskIndex = CONDITION_RISK_LEVELS.indexOf(latestAssessmentEntry.riskLevel)
    const previousRiskIndex = CONDITION_RISK_LEVELS.indexOf(previousAssessmentEntry.riskLevel)
    let riskTrend: 'improved' | 'declined' | 'same' | 'changed' = 'same'
    if (latestRiskIndex !== -1 && previousRiskIndex !== -1) {
      if (latestRiskIndex < previousRiskIndex) {
        riskTrend = 'improved'
      } else if (latestRiskIndex > previousRiskIndex) {
        riskTrend = 'declined'
      } else {
        riskTrend = 'same'
      }
    } else if (latestAssessmentEntry.riskLevel !== previousAssessmentEntry.riskLevel) {
      riskTrend = 'changed'
    }
    return {
      scoreDelta,
      ratingTrend,
      riskTrend,
      ratingChanged: latestAssessmentEntry.overallRating !== previousAssessmentEntry.overallRating,
      riskChanged: latestAssessmentEntry.riskLevel !== previousAssessmentEntry.riskLevel,
    }
  }, [latestAssessmentEntry, previousAssessmentEntry])
  const formatRecordedTimestamp = useCallback((timestamp?: string | null) => {
    if (!timestamp) {
      return 'Draft assessment'
    }
    const parsed = new Date(timestamp)
    if (Number.isNaN(parsed.getTime())) {
      return timestamp
    }
    return parsed.toLocaleString()
  }, [])

  useEffect(() => {
    setSelectedCategory(null)
  }, [activeScenario])

  useEffect(() => {
    let cancelled = false
    async function loadConditionAssessment() {
      if (!capturedProperty) {
        setConditionAssessment(null)
        return
      }
      setIsLoadingCondition(true)
      try {
        const assessment = await fetchConditionAssessment(
          capturedProperty.propertyId,
          activeScenario,
        )
        if (!cancelled) {
          setConditionAssessment(assessment)
        }
      } catch (error) {
        if (!cancelled) {
          console.error('Failed to fetch condition assessment:', error)
          setConditionAssessment(null)
        }
      } finally {
        if (!cancelled) {
          setIsLoadingCondition(false)
        }
      }
    }

    loadConditionAssessment()
    return () => {
      cancelled = true
    }
  }, [capturedProperty, activeScenario])

  useEffect(() => {
    if (!capturedProperty) {
      setAssessmentDraft(buildAssessmentDraft(null, 'all'))
      setAssessmentEditorMode('edit')
      setIsEditingAssessment(false)
      return
    }

    if (!isEditingAssessment) {
      // When not editing, sync the draft with the current assessment
      const baseDraft = buildAssessmentDraft(conditionAssessment, activeScenario)
      // Use current timestamp since any save creates a new history entry
      const nowLocal = formatDateTimeLocalInput(new Date().toISOString())
      setAssessmentDraft({
        ...baseDraft,
        recordedAtLocal: nowLocal,
      })
    }
  }, [
    capturedProperty,
    conditionAssessment,
    activeScenario,
    isEditingAssessment,
    assessmentEditorMode,
  ])

  function handleAssessmentFieldChange(
    field: keyof ConditionAssessmentDraft,
    value: string,
  ) {
    setAssessmentDraft((prev) => ({
      ...prev,
      [field]: value,
    }))
  }

  function handleAssessmentSystemChange(
    index: number,
    field: keyof AssessmentDraftSystem,
    value: string,
  ) {
    setAssessmentDraft((prev) => {
      const systems = [...prev.systems]
      systems[index] = {
        ...systems[index],
        [field]: value,
      }
      return { ...prev, systems }
    })
  }

  async function handleAssessmentSubmit(
    event: React.FormEvent<HTMLFormElement>,
  ) {
    event.preventDefault()
    if (!capturedProperty) {
      return
    }

    setIsSavingAssessment(true)
    setAssessmentSaveMessage(null)

    try {
      const systemsPayload: ConditionAssessmentUpsertRequest['systems'] = assessmentDraft.systems.map(
        (system) => {
          const parsedScore = Number(system.score)
          const scoreValue = Number.isNaN(parsedScore) ? 0 : parsedScore
          return {
            name: system.name,
            rating: system.rating,
            score: scoreValue,
            notes: system.notes,
            recommendedActions: system.recommendedActions
              .split('\n')
              .map((line) => line.trim())
              .filter((line) => line.length > 0),
          }
        },
      )

      const parsedOverallScore = Number(assessmentDraft.overallScore)
      const overallScoreValue = Number.isNaN(parsedOverallScore)
        ? 0
        : parsedOverallScore

      const inspectorNameValue = assessmentDraft.inspectorName.trim()
      const recordedAtIso = convertLocalToISO(assessmentDraft.recordedAtLocal)
      const attachmentsPayload = parseAttachmentsText(assessmentDraft.attachmentsText)

      const payload: ConditionAssessmentUpsertRequest = {
        scenario: assessmentDraft.scenario,
        overallRating: assessmentDraft.overallRating,
        overallScore: overallScoreValue,
        riskLevel: assessmentDraft.riskLevel,
        summary: assessmentDraft.summary,
        scenarioContext:
          assessmentDraft.scenarioContext.trim() === ''
            ? undefined
            : assessmentDraft.scenarioContext,
        systems: systemsPayload,
        recommendedActions: assessmentDraft.recommendedActionsText
          .split('\n')
          .map((line) => line.trim())
          .filter((line) => line.length > 0),
        attachments: attachmentsPayload,
      }

      if (inspectorNameValue) {
        payload.inspectorName = inspectorNameValue
      }
      if (recordedAtIso) {
        payload.recordedAt = recordedAtIso
      }

      const saved = await saveConditionAssessment(
        capturedProperty.propertyId,
        payload,
      )

      if (saved) {
        const refreshed = await fetchConditionAssessment(
          capturedProperty.propertyId,
          activeScenario,
        )
        setConditionAssessment(refreshed)
        setAssessmentDraft(buildAssessmentDraft(refreshed, activeScenario))
        await loadAssessmentHistory({ silent: true })
        await loadScenarioAssessments({ silent: true })
        setAssessmentSaveMessage('Inspection saved successfully.')
        closeAssessmentEditor()
      } else {
        setAssessmentSaveMessage('Unable to save inspection data. Please try again.')
      }
    } catch (error) {
      console.error('Failed to save inspection assessment:', error)
      setAssessmentSaveMessage('Unable to save inspection data. Please try again.')
    } finally {
      setIsSavingAssessment(false)
    }
  }

  function resetAssessmentDraft() {
    const nowLocal = formatDateTimeLocalInput(new Date().toISOString())

    if (assessmentEditorMode === 'new') {
      const baseDraft = buildAssessmentDraft(null, activeScenario)
      setAssessmentDraft({
        ...baseDraft,
        inspectorName: '',
        recordedAtLocal: nowLocal,
        attachmentsText: '',
      })
    } else {
      // For 'edit' mode, get the source assessment to reset to
      let sourceAssessment: ConditionAssessment | null = null
      if (activeScenario === 'all' && latestAssessmentEntry) {
        sourceAssessment = latestAssessmentEntry
      } else {
        sourceAssessment = conditionAssessment
      }
      const baseDraft = buildAssessmentDraft(sourceAssessment, activeScenario)
      // Use current timestamp since saving creates a new history entry
      setAssessmentDraft({
        ...baseDraft,
        recordedAtLocal: nowLocal,
      })
    }
    setAssessmentSaveMessage(null)
  }

  function openAssessmentEditor(mode: 'new' | 'edit') {
    if (!capturedProperty) {
      return
    }
    const targetScenario = activeScenario === 'all' ? 'all' : activeScenario
    const nowLocal = formatDateTimeLocalInput(new Date().toISOString())

    if (mode === 'new') {
      const baseDraft = buildAssessmentDraft(null, targetScenario)
      setAssessmentDraft({
        ...baseDraft,
        inspectorName: '',
        recordedAtLocal: nowLocal,
        attachmentsText: '',
      })
    } else {
      let sourceAssessment: ConditionAssessment | null = null
      if (activeScenario === 'all' && latestAssessmentEntry) {
        sourceAssessment = latestAssessmentEntry
      } else {
        sourceAssessment = conditionAssessment
      }
      const scenarioForDraft: DevelopmentScenario | 'all' =
        (sourceAssessment?.scenario as DevelopmentScenario | null | undefined) ??
        (activeScenario as DevelopmentScenario | 'all')
      const baseDraft = buildAssessmentDraft(sourceAssessment, scenarioForDraft)
      // When editing, use current timestamp since saving creates a new history entry
      setAssessmentDraft({
        ...baseDraft,
        recordedAtLocal: nowLocal,
      })
    }
    setAssessmentEditorMode(mode)
    setAssessmentSaveMessage(null)
    setIsEditingAssessment(true)
  }

  function closeAssessmentEditor() {
    setIsEditingAssessment(false)
    setAssessmentEditorMode('edit')
  }

  function toggleScenario(scenario: DevelopmentScenario) {
    setSelectedScenarios((prev) =>
      prev.includes(scenario)
        ? prev.filter((s) => s !== scenario)
        : [...prev, scenario]
    )
  }

  const buildAssetMixStorageKey = (propertyId: string) =>
    `developer-asset-mix:${propertyId}`

  async function handleCapture(e: React.FormEvent) {
    e.preventDefault()
    const lat = parseFloat(latitude)
    const lon = parseFloat(longitude)

    if (isNaN(lat) || isNaN(lon)) {
      setError('Please enter valid coordinates')
      return
    }

    if (selectedScenarios.length === 0) {
      setError('Please select at least one development scenario')
      return
    }

    setIsCapturing(true)
    setError(null)

    try {
      const result = await capturePropertyForDevelopment({
        latitude: lat,
        longitude: lon,
        developmentScenarios: selectedScenarios,
        previewDetailLevel,
      })

      setCapturedProperty(result)
      setPreviewJob(result.previewJobs?.[0] ?? null)
      if (result.propertyId) {
        try {
          const propertyLabel =
            result.propertyInfo?.propertyName?.trim() ||
            result.address?.fullAddress?.trim() ||
            null
          sessionStorage.setItem(
            buildAssetMixStorageKey(result.propertyId),
            JSON.stringify({
              optimizations: result.optimizations,
              buildEnvelope: result.buildEnvelope,
              financialSummary: result.financialSummary,
              visualization: result.visualization,
              propertyInfo: result.propertyInfo,
              address: result.address,
              metadata: {
                propertyId: result.propertyId,
                propertyName: propertyLabel,
                capturedAt: result.timestamp ?? new Date().toISOString(),
              },
            }),
          )
        } catch (storageError) {
          console.warn('Unable to persist asset mix snapshot', storageError)
        }
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to capture property')
    } finally {
      setIsCapturing(false)
    }
  }

  async function handleChecklistUpdate(
    itemId: string,
    newStatus: 'pending' | 'in_progress' | 'completed' | 'not_applicable',
  ) {
    const updated = await updateChecklistItem(itemId, { status: newStatus })
    if (updated) {
      // Update local state
      setChecklistItems((prev) =>
        prev.map((item) => (item.id === itemId ? updated : item)),
      )

      // Reload summary
      if (capturedProperty) {
        const summary = await fetchChecklistSummary(capturedProperty.propertyId)
        setChecklistSummary(summary)
      }
    }
  }

  async function handleReportExport(format: 'json' | 'pdf') {
    if (!capturedProperty) {
      return
    }
    try {
      setIsExportingReport(true)
      setReportExportMessage(null)
      const { blob, filename } = await exportConditionReport(
        capturedProperty.propertyId,
        format,
      )
      const downloadUrl = URL.createObjectURL(blob)
      const link = document.createElement('a')
      link.href = downloadUrl
      link.download = filename
      document.body.appendChild(link)
      link.click()
      document.body.removeChild(link)
      URL.revokeObjectURL(downloadUrl)
      setReportExportMessage(
        format === 'pdf'
          ? 'Condition report downloaded (PDF).'
          : 'Condition report downloaded (JSON).',
      )
    } catch (error) {
      const message =
        error instanceof Error
          ? error.message
          : 'Unable to download condition report.'
      console.error('Failed to export condition report:', error)
      setReportExportMessage(message)
    } finally {
      setIsExportingReport(false)
    }
  }

  const InspectionHistoryContent = () => (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
      <div
        style={{
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'flex-start',
          gap: '1rem',
          flexWrap: 'wrap',
        }}
      >
        <div>
          <h3
            style={{
              margin: 0,
              fontSize: '1.0625rem',
              fontWeight: 600,
            }}
          >
            Inspection History
          </h3>
          <p
            style={{
              margin: '0.3rem 0 0',
              fontSize: '0.875rem',
              color: '#6e6e73',
              maxWidth: '480px',
            }}
          >
            Review the developer inspection timeline or compare the two most recent
            assessments side-by-side.
          </p>
        </div>
        <div style={{ display: 'flex', gap: '0.6rem', flexWrap: 'wrap' }}>
          <button
            type="button"
            onClick={() => setHistoryViewMode('timeline')}
            style={{
              border: '1px solid #1d1d1f',
              background: historyViewMode === 'timeline' ? '#1d1d1f' : 'white',
              color: historyViewMode === 'timeline' ? 'white' : '#1d1d1f',
              borderRadius: '9999px',
              padding: '0.4rem 0.9rem',
              fontSize: '0.8125rem',
              fontWeight: 600,
              cursor: 'pointer',
            }}
          >
            Timeline
          </button>
          <button
            type="button"
            onClick={() => setHistoryViewMode('compare')}
            style={{
              border: '1px solid #1d1d1f',
              background: historyViewMode === 'compare' ? '#1d1d1f' : 'white',
              color: historyViewMode === 'compare' ? 'white' : '#1d1d1f',
              borderRadius: '9999px',
              padding: '0.4rem 0.9rem',
              fontSize: '0.8125rem',
              fontWeight: 600,
              cursor: 'pointer',
            }}
          >
            Compare
          </button>
        </div>
      </div>
      {assessmentHistoryError ? (
        <p
          style={{
            margin: 0,
            fontSize: '0.85rem',
            color: '#c53030',
          }}
        >
          {assessmentHistoryError}
        </p>
      ) : isLoadingAssessmentHistory ? (
        <div
          style={{
            padding: '1.5rem',
            textAlign: 'center',
            color: '#6e6e73',
            background: '#f5f5f7',
            borderRadius: '10px',
          }}
        >
          <p style={{ margin: 0, fontSize: '0.9rem' }}>Loading inspection history...</p>
        </div>
      ) : assessmentHistory.length === 0 ? (
        <div
          style={{
            padding: '1.5rem',
            textAlign: 'center',
            color: '#6e6e73',
            background: '#f5f5f7',
            borderRadius: '10px',
          }}
        >
          <p style={{ margin: 0, fontSize: '0.9rem' }}>
            No developer inspections recorded yet.
          </p>
          <p style={{ margin: '0.35rem 0 0', fontSize: '0.8rem' }}>
            Save an inspection above to start the audit trail.
          </p>
        </div>
      ) : historyViewMode === 'timeline' ? (
        <div style={{ display: 'flex', flexDirection: 'column', gap: '0.9rem' }}>
          {assessmentHistory.map((entry, index) => {
            const key = `${entry.recordedAt ?? 'draft'}-${index}`
            const matchesScenario =
              activeScenario === 'all' ||
              !entry.scenario ||
              entry.scenario === activeScenario
            const recommendedPreview = entry.recommendedActions.slice(0, 2)
            const remainingActions =
              entry.recommendedActions.length - recommendedPreview.length
            return (
              <div
                key={key}
                style={{
                  border: '1px solid #e5e5e7',
                  borderLeft: `4px solid ${
                    index === 0 ? '#0a84ff' : matchesScenario ? '#34c759' : '#d2d2d7'
                  }`,
                  borderRadius: '10px',
                  padding: '1rem 1.25rem',
                  background: index === 0 ? '#f0f9ff' : '#ffffff',
                  display: 'flex',
                  flexDirection: 'column',
                  gap: '0.5rem',
                }}
              >
                <div
                  style={{
                    display: 'flex',
                    justifyContent: 'space-between',
                    alignItems: 'flex-start',
                    flexWrap: 'wrap',
                    gap: '0.5rem',
                  }}
                >
                  <div
                    style={{ display: 'flex', flexDirection: 'column', gap: '0.25rem' }}
                  >
                    <span
                      style={{
                        fontSize: '0.75rem',
                        fontWeight: 600,
                        letterSpacing: '0.08em',
                        textTransform: 'uppercase',
                        color: '#6e6e73',
                      }}
                    >
                      {index === 0 ? 'Most recent inspection' : `Inspection ${index + 1}`}
                    </span>
                    <span style={{ fontSize: '0.9375rem', fontWeight: 600 }}>
                      {formatScenarioLabel(entry.scenario)}
                    </span>
                  </div>
                  <div
                    style={{
                      display: 'flex',
                      flexDirection: 'column',
                      gap: '0.2rem',
                      alignItems: 'flex-end',
                    }}
                  >
                    <span style={{ fontSize: '0.85rem', color: '#6e6e73' }}>
                      {formatRecordedTimestamp(entry.recordedAt)}
                    </span>
                    <span style={{ fontSize: '0.78rem', color: '#6e6e73' }}>
                      Inspector:{' '}
                      <strong>{entry.inspectorName?.trim() || 'Not recorded'}</strong>
                    </span>
                  </div>
                </div>
                <p style={{ margin: 0, fontSize: '0.875rem', color: '#3a3a3c' }}>
                  {entry.summary || 'No notes recorded.'}
                </p>
                <div
                  style={{
                    display: 'flex',
                    flexWrap: 'wrap',
                    gap: '0.4rem',
                    fontSize: '0.8rem',
                    color: '#6e6e73',
                  }}
                >
                  <span>
                    Rating: <strong>{entry.overallRating}</strong>
                  </span>
                  <span>
                    Score: <strong>{entry.overallScore}/100</strong>
                  </span>
                  <span>
                    Risk level:{' '}
                    <strong style={{ textTransform: 'capitalize' }}>{entry.riskLevel}</strong>
                  </span>
                </div>
                {recommendedPreview.length > 0 && (
                  <div style={{ marginTop: '0.25rem' }}>
                    <span
                      style={{
                        fontSize: '0.75rem',
                        fontWeight: 600,
                        textTransform: 'uppercase',
                        color: '#6e6e73',
                        letterSpacing: '0.06em',
                      }}
                    >
                      Recommended actions
                    </span>
                    <ul style={{ margin: '0.35rem 0 0', paddingLeft: '1rem' }}>
                      {recommendedPreview.map((action, actionIndex) => (
                        <li key={`${key}-action-${actionIndex}`} style={{ fontSize: '0.85rem' }}>
                          {action}
                        </li>
                      ))}
                    </ul>
                    {remainingActions > 0 && (
                      <p style={{ margin: '0.35rem 0 0', fontSize: '0.75rem', color: '#6e6e73' }}>
                        +{remainingActions} more actions recorded in this inspection.
                      </p>
                    )}
                  </div>
                )}
                {entry.attachments.length > 0 && (
                  <div style={{ marginTop: '0.35rem' }}>
                    <span
                      style={{
                        fontSize: '0.75rem',
                        fontWeight: 600,
                        textTransform: 'uppercase',
                        color: '#6e6e73',
                        letterSpacing: '0.06em',
                      }}
                    >
                      Attachments
                    </span>
                    <ul style={{ margin: '0.35rem 0 0', paddingLeft: '1rem' }}>
                      {entry.attachments.map((attachment, attachmentIndex) => (
                        <li key={`${key}-attachment-${attachmentIndex}`} style={{ fontSize: '0.85rem' }}>
                          {attachment.url ? (
                            <a
                              href={attachment.url}
                              target="_blank"
                              rel="noreferrer"
                              style={{ color: '#0a84ff' }}
                            >
                              {attachment.label}
                            </a>
                          ) : (
                            attachment.label
                          )}
                        </li>
                      ))}
                    </ul>
                  </div>
                )}
              </div>
            )
          })}
        </div>
      ) : historyViewMode === 'compare' ? (
        <div style={{ display: 'flex', flexDirection: 'column', gap: '1.5rem' }}>
          {assessmentHistory.length < 2 ||
          !latestAssessmentEntry ||
          !previousAssessmentEntry ? (
            <div
              style={{
                padding: '1.5rem',
                textAlign: 'center',
                color: '#6e6e73',
                background: '#f5f5f7',
                borderRadius: '10px',
              }}
            >
              <p style={{ margin: 0, fontSize: '0.9rem' }}>
                Capture one more inspection to unlock comparison view.
              </p>
            </div>
          ) : scenarioComparisonVisible ? (
              <div ref={scenarioComparisonRef}>
                <details
                  open
                  style={{
                    border: '1px solid #e5e5e7',
                    borderRadius: '14px',
                    background: 'white',
                    overflow: 'hidden',
                  }}
                >
                  <summary
                  style={{
                    padding: '0.85rem 1rem',
                    fontSize: '0.85rem',
                    fontWeight: 600,
                    cursor: 'pointer',
                    listStyle: 'none',
                    outline: 'none',
                  }}
                >
                  Detailed comparison table
                </summary>
                <div style={{ borderTop: '1px solid #e5e5e7', overflowX: 'auto' }}>
                  <table
                    style={{
                      width: '100%',
                      borderCollapse: 'collapse',
                      minWidth: '960px',
                    }}
                  >
                    <thead style={{ background: '#ffffff' }}>
                      <tr>
                        <th
                          style={{
                            textAlign: 'left',
                            padding: '0.85rem 1rem',
                            fontSize: '0.75rem',
                            letterSpacing: '0.08em',
                            textTransform: 'uppercase',
                            color: '#6e6e73',
                            borderBottom: '1px solid #ebebf0',
                          }}
                        >
                          Scenario
                        </th>
                        <th
                          style={{
                            textAlign: 'left',
                            padding: '0.85rem 1rem',
                            fontSize: '0.75rem',
                            letterSpacing: '0.08em',
                            textTransform: 'uppercase',
                            color: '#6e6e73',
                            borderBottom: '1px solid #ebebf0',
                          }}
                        >
                          Quick headline
                        </th>
                        <th
                          style={{
                            textAlign: 'left',
                            padding: '0.85rem 1rem',
                            fontSize: '0.75rem',
                            letterSpacing: '0.08em',
                            textTransform: 'uppercase',
                            color: '#6e6e73',
                            borderBottom: '1px solid #ebebf0',
                          }}
                        >
                          Key metrics
                        </th>
                        <th
                          style={{
                            textAlign: 'left',
                            padding: '0.85rem 1rem',
                            fontSize: '0.75rem',
                            letterSpacing: '0.08em',
                            textTransform: 'uppercase',
                            color: '#6e6e73',
                            borderBottom: '1px solid #ebebf0',
                          }}
                        >
                          Condition
                        </th>
                        <th
                          style={{
                            textAlign: 'left',
                            padding: '0.85rem 1rem',
                            fontSize: '0.75rem',
                            letterSpacing: '0.08em',
                            textTransform: 'uppercase',
                            color: '#6e6e73',
                            borderBottom: '1px solid #ebebf0',
                          }}
                        >
                          Checklist
                        </th>
                        <th
                          style={{
                            textAlign: 'left',
                            padding: '0.85rem 1rem',
                            fontSize: '0.75rem',
                            letterSpacing: '0.08em',
                            textTransform: 'uppercase',
                            color: '#6e6e73',
                            borderBottom: '1px solid #ebebf0',
                          }}
                        >
                          Key insight
                        </th>
                        <th
                          style={{
                            textAlign: 'left',
                            padding: '0.85rem 1rem',
                            fontSize: '0.75rem',
                            letterSpacing: '0.08em',
                            textTransform: 'uppercase',
                            color: '#6e6e73',
                            borderBottom: '1px solid #ebebf0',
                          }}
                        >
                          Next action
                        </th>
                        <th
                          style={{
                            textAlign: 'left',
                            padding: '0.85rem 1rem',
                            fontSize: '0.75rem',
                            letterSpacing: '0.08em',
                            textTransform: 'uppercase',
                            color: '#6e6e73',
                            borderBottom: '1px solid #ebebf0',
                          }}
                        >
                          Inspector
                        </th>
                        <th
                          style={{
                            textAlign: 'left',
                            padding: '0.85rem 1rem',
                            fontSize: '0.75rem',
                            letterSpacing: '0.08em',
                            textTransform: 'uppercase',
                            color: '#6e6e73',
                            borderBottom: '1px solid #ebebf0',
                          }}
                        >
                          Source
                        </th>
                      </tr>
                    </thead>
                    <tbody>
                      {scenarioComparisonTableRows.map((row) => (
                        <tr key={`comparison-table-${row.key}`}>
                          <td
                            style={{
                              padding: '0.85rem 1rem',
                              borderBottom: '1px solid #f4f4f8',
                              whiteSpace: 'nowrap',
                            }}
                          >
                            <div
                              style={{
                                display: 'flex',
                                flexDirection: 'column',
                                gap: '0.2rem',
                                alignItems: 'flex-start',
                              }}
                            >
                              <span style={{ fontWeight: 600 }}>{row.label}</span>
                              {row.recordedAt && (
                                <span style={{ fontSize: '0.75rem', color: '#6b7280' }}>
                                  {formatRecordedTimestamp(row.recordedAt)}
                                </span>
                              )}
                            </div>
                          </td>
                          <td
                            style={{
                              padding: '0.85rem 1rem',
                              borderBottom: '1px solid #f4f4f8',
                              color: '#3a3a3c',
                              fontSize: '0.9rem',
                              maxWidth: '220px',
                            }}
                          >
                            {row.quickHeadline ?? '—'}
                          </td>
                          <td
                            style={{
                              padding: '0.85rem 1rem',
                              borderBottom: '1px solid #f4f4f8',
                              color: '#3a3a3c',
                              fontSize: '0.9rem',
                              maxWidth: '220px',
                            }}
                          >
                            {row.quickMetrics.length === 0 ? (
                              '—'
                            ) : (
                              <ul
                                style={{
                                  margin: 0,
                                  paddingLeft: '1.1rem',
                                  display: 'flex',
                                  flexDirection: 'column',
                                  gap: '0.2rem',
                                }}
                              >
                                {row.quickMetrics.map((metric) => (
                                  <li key={`${row.key}-${metric.label}`}>
                                    {metric.label}: {metric.value}
                                  </li>
                                ))}
                              </ul>
                            )}
                          </td>
                          <td
                            style={{
                              padding: '0.85rem 1rem',
                              borderBottom: '1px solid #f4f4f8',
                              color: '#3a3a3c',
                              fontSize: '0.9rem',
                              whiteSpace: 'nowrap',
                            }}
                          >
                            {row.conditionRating ? (
                              <div style={{ display: 'flex', flexDirection: 'column', gap: '0.2rem' }}>
                                <strong>{row.conditionRating}</strong>
                                <span>
                                  {row.conditionScore !== null ? `${row.conditionScore}/100` : '—'}{' '}
                                  {row.riskLevel ? `· ${row.riskLevel} risk` : ''}
                                </span>
                              </div>
                            ) : (
                              '—'
                            )}
                          </td>
                          <td
                            style={{
                              padding: '0.85rem 1rem',
                              borderBottom: '1px solid #f4f4f8',
                              color: '#3a3a3c',
                              fontSize: '0.9rem',
                              whiteSpace: 'nowrap',
                            }}
                          >
                            {row.checklistCompleted !== null && row.checklistTotal !== null
                              ? `${row.checklistCompleted}/${row.checklistTotal}` +
                                (row.checklistPercent !== null ? ` (${row.checklistPercent}%)` : '')
                              : '—'}
                          </td>
                          <td
                            style={{
                              padding: '0.85rem 1rem',
                              borderBottom: '1px solid #f4f4f8',
                              color: '#3a3a3c',
                              fontSize: '0.9rem',
                              maxWidth: '240px',
                            }}
                          >
                            {row.primaryInsight ? (
                              <>
                                <strong>{row.primaryInsight.title}</strong>
                                <div>{row.primaryInsight.detail}</div>
                              </>
                            ) : row.insights.length > 0 ? (
                              <div>{row.insights[0].title}</div>
                            ) : (
                              '—'
                            )}
                          </td>
                          <td
                            style={{
                              padding: '0.85rem 1rem',
                              borderBottom: '1px solid #f4f4f8',
                              color: '#3a3a3c',
                              fontSize: '0.9rem',
                              maxWidth: '200px',
                            }}
                          >
                            {row.recommendedAction ?? '—'}
                          </td>
                          <td
                            style={{
                              padding: '0.85rem 1rem',
                              borderBottom: '1px solid #f4f4f8',
                              color: '#3a3a3c',
                              fontSize: '0.9rem',
                              whiteSpace: 'nowrap',
                            }}
                          >
                            {row.inspectorName ?? '—'}
                          </td>
                          <td
                            style={{
                              padding: '0.85rem 1rem',
                              borderBottom: '1px solid #f4f4f8',
                              color: '#3a3a3c',
                              fontSize: '0.9rem',
                              whiteSpace: 'nowrap',
                            }}
                          >
                            {row.source === 'manual' ? 'Manual inspection' : 'Automated baseline'}
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </details>
              </div>
          ) : (
            <>
              {comparisonSummary && (
                <div
                  style={{
                    border: '1px solid #e5e5e7',
                    borderRadius: '12px',
                    padding: '1.5rem',
                    display: 'flex',
                    flexDirection: 'column',
                    gap: '0.75rem',
                    background: '#f0f9ff',
                  }}
                >
                  <div
                    style={{
                      display: 'flex',
                      justifyContent: 'space-between',
                      alignItems: 'flex-start',
                      flexWrap: 'wrap',
                      gap: '0.5rem',
                    }}
                  >
                    <span
                      style={{
                        fontSize: '0.75rem',
                        fontWeight: 600,
                        textTransform: 'uppercase',
                        letterSpacing: '0.08em',
                        color: '#0a84ff',
                      }}
                    >
                      Overall score
                    </span>
                    <span style={{ fontSize: '0.8125rem', color: '#6e6e73' }}>
                      {formatRecordedTimestamp(latestAssessmentEntry.recordedAt)}
                    </span>
                  </div>
                  <div
                    style={{
                      display: 'flex',
                      alignItems: 'baseline',
                      gap: '0.5rem',
                    }}
                  >
                    <span style={{ fontSize: '2rem', fontWeight: 700 }}>
                      {latestAssessmentEntry.overallScore}
                    </span>
                    <span style={{ fontSize: '0.85rem', color: '#1d1d1f' }}>/100</span>
                    <span
                      style={{
                        fontSize: '0.875rem',
                        fontWeight: 600,
                        color:
                          comparisonSummary.scoreDelta > 0
                            ? '#15803d'
                            : comparisonSummary.scoreDelta < 0
                            ? '#c53030'
                            : '#6e6e73',
                      }}
                    >
                      {comparisonSummary.scoreDelta > 0 ? '+' : ''}
                      {comparisonSummary.scoreDelta}
                    </span>
                  </div>
                  <p style={{ margin: 0, fontSize: '0.875rem', color: '#3a3a3c' }}>
                    {comparisonSummary.scoreDelta === 0
                      ? 'Overall score held steady vs previous inspection.'
                      : comparisonSummary.scoreDelta > 0
                      ? `Improved by ${comparisonSummary.scoreDelta} points from ${previousAssessmentEntry.overallScore}.`
                      : `Declined by ${Math.abs(
                          comparisonSummary.scoreDelta,
                        )} points from ${previousAssessmentEntry.overallScore}.`}
                  </p>
                  <p style={{ margin: 0, fontSize: '0.875rem', color: '#3a3a3c' }}>
                    {comparisonSummary.ratingChanged
                      ? `Rating ${
                          comparisonSummary.ratingTrend === 'improved'
                            ? 'improved'
                            : comparisonSummary.ratingTrend === 'declined'
                            ? 'declined'
                            : 'changed'
                        } from ${previousAssessmentEntry.overallRating} to ${latestAssessmentEntry.overallRating}.`
                      : 'Rating unchanged from previous inspection.'}
                  </p>
                  <p style={{ margin: 0, fontSize: '0.875rem', color: '#3a3a3c' }}>
                    {comparisonSummary.riskChanged
                      ? `Risk level ${
                          comparisonSummary.riskTrend === 'improved'
                            ? 'eased'
                            : comparisonSummary.riskTrend === 'declined'
                            ? 'intensified'
                            : 'changed'
                        } from ${previousAssessmentEntry.riskLevel} to ${latestAssessmentEntry.riskLevel}.`
                      : 'Risk level unchanged.'}
                  </p>
                </div>
              )}

              <div
                style={{
                  display: 'grid',
                  gap: '1rem',
                  gridTemplateColumns: 'repeat(auto-fit, minmax(260px, 1fr))',
                }}
              >
                <div
                  style={{
                    border: '1px solid #e5e5e7',
                    borderRadius: '10px',
                    padding: '1.25rem',
                    display: 'grid',
                    gap: '0.6rem',
                    background: '#f0f9ff',
                  }}
                >
                  <div
                    style={{
                      display: 'flex',
                      justifyContent: 'space-between',
                      alignItems: 'flex-start',
                      gap: '0.5rem',
                      flexWrap: 'wrap',
                    }}
                  >
                    <span
                      style={{
                        fontSize: '0.75rem',
                        fontWeight: 600,
                        textTransform: 'uppercase',
                        letterSpacing: '0.08em',
                        color: '#0a84ff',
                      }}
                    >
                      Current inspection
                    </span>
                    <span style={{ fontSize: '0.8125rem', color: '#6e6e73' }}>
                      {formatRecordedTimestamp(latestAssessmentEntry.recordedAt)}
                    </span>
                  </div>
                  <strong style={{ fontSize: '1rem', fontWeight: 600 }}>
                    {formatScenarioLabel(latestAssessmentEntry.scenario ?? null)}
                  </strong>
                  <span style={{ fontSize: '0.9rem', color: '#3a3a3c' }}>
                    Rating {latestAssessmentEntry.overallRating} · {latestAssessmentEntry.overallScore}
                    /100 · {latestAssessmentEntry.riskLevel} risk
                  </span>
                  {latestAssessmentEntry.summary && (
                    <p
                      style={{
                        margin: 0,
                        fontSize: '0.875rem',
                        color: '#3a3a3c',
                        lineHeight: 1.5,
                      }}
                    >
                      {latestAssessmentEntry.summary}
                    </p>
                  )}
                  <div
                    style={{
                      display: 'flex',
                      flexWrap: 'wrap',
                      gap: '0.6rem',
                      fontSize: '0.78rem',
                      color: '#475569',
                    }}
                  >
                    <span>
                      Inspector:{' '}
                      <strong>
                        {latestAssessmentEntry.inspectorName?.trim() || 'Not recorded'}
                      </strong>
                    </span>
                    <span
                      style={{
                        display: 'inline-flex',
                        alignItems: 'center',
                        gap: '0.3rem',
                        borderRadius: '9999px',
                        padding: '0.15rem 0.6rem',
                        fontWeight: 600,
                        letterSpacing: '0.05em',
                        textTransform: 'uppercase',
                        background: latestAssessmentEntry.recordedAt
                          ? '#dcfce7'
                          : 'rgba(37, 99, 235, 0.12)',
                        color: latestAssessmentEntry.recordedAt ? '#166534' : '#1d4ed8',
                      }}
                    >
                      {latestAssessmentEntry.recordedAt
                        ? 'Manual inspection'
                        : 'Automated baseline'}
                    </span>
                  </div>
                  {latestAssessmentEntry.attachments.length > 0 && (
                    <div>
                      <span
                        style={{
                          display: 'inline-block',
                          marginTop: '0.35rem',
                          fontSize: '0.75rem',
                          fontWeight: 600,
                          textTransform: 'uppercase',
                          color: '#6e6e73',
                          letterSpacing: '0.06em',
                        }}
                      >
                        Attachments
                      </span>
                      <ul style={{ margin: '0.3rem 0 0', paddingLeft: '1.2rem' }}>
                        {latestAssessmentEntry.attachments.map((attachment, index) => (
                          <li key={`latest-attachment-${index}`} style={{ fontSize: '0.85rem' }}>
                            {attachment.url ? (
                              <a
                                href={attachment.url}
                                target="_blank"
                                rel="noreferrer"
                                style={{ color: '#0a84ff' }}
                              >
                                {attachment.label}
                              </a>
                            ) : (
                              attachment.label
                            )}
                          </li>
                        ))}
                      </ul>
                    </div>
                  )}
                </div>
                <div
                  style={{
                    border: '1px solid #e5e5e7',
                    borderRadius: '10px',
                    padding: '1.25rem',
                    display: 'grid',
                    gap: '0.6rem',
                  }}
                >
                  <div
                    style={{
                      display: 'flex',
                      justifyContent: 'space-between',
                      alignItems: 'flex-start',
                      gap: '0.5rem',
                      flexWrap: 'wrap',
                    }}
                  >
                    <span
                      style={{
                        fontSize: '0.75rem',
                        fontWeight: 600,
                        textTransform: 'uppercase',
                        letterSpacing: '0.08em',
                        color: '#6e6e73',
                      }}
                    >
                      Previous inspection
                    </span>
                    <span style={{ fontSize: '0.8125rem', color: '#6e6e73' }}>
                      {formatRecordedTimestamp(previousAssessmentEntry.recordedAt)}
                    </span>
                  </div>
                  <strong style={{ fontSize: '1rem', fontWeight: 600 }}>
                    {formatScenarioLabel(previousAssessmentEntry.scenario ?? null)}
                  </strong>
                  <span style={{ fontSize: '0.9rem', color: '#3a3a3c' }}>
                    Rating {previousAssessmentEntry.overallRating} · {previousAssessmentEntry.overallScore}
                    /100 · {previousAssessmentEntry.riskLevel} risk
                  </span>
                  {previousAssessmentEntry.summary && (
                    <p
                      style={{
                        margin: 0,
                        fontSize: '0.875rem',
                        color: '#3a3a3c',
                        lineHeight: 1.5,
                      }}
                    >
                      {previousAssessmentEntry.summary}
                    </p>
                  )}
                  <div
                    style={{
                      display: 'flex',
                      flexWrap: 'wrap',
                      gap: '0.6rem',
                      fontSize: '0.78rem',
                      color: '#475569',
                    }}
                  >
                    <span>
                      Inspector:{' '}
                      <strong>
                        {previousAssessmentEntry.inspectorName?.trim() || 'Not recorded'}
                      </strong>
                    </span>
                    <span
                      style={{
                        display: 'inline-flex',
                        alignItems: 'center',
                        gap: '0.3rem',
                        borderRadius: '9999px',
                        padding: '0.15rem 0.6rem',
                        fontWeight: 600,
                        letterSpacing: '0.05em',
                        textTransform: 'uppercase',
                        background: previousAssessmentEntry.recordedAt
                          ? '#dcfce7'
                          : 'rgba(37, 99, 235, 0.12)',
                        color: previousAssessmentEntry.recordedAt ? '#166534' : '#1d4ed8',
                      }}
                    >
                      {previousAssessmentEntry.recordedAt
                        ? 'Manual inspection'
                        : 'Automated baseline'}
                    </span>
                  </div>
                  {previousAssessmentEntry.attachments.length > 0 && (
                    <div>
                      <span
                        style={{
                          display: 'inline-block',
                          marginTop: '0.35rem',
                          fontSize: '0.75rem',
                          fontWeight: 600,
                          textTransform: 'uppercase',
                          color: '#6e6e73',
                          letterSpacing: '0.06em',
                        }}
                      >
                        Attachments
                      </span>
                      <ul style={{ margin: '0.3rem 0 0', paddingLeft: '1.2rem' }}>
                        {previousAssessmentEntry.attachments.map((attachment, index) => (
                          <li key={`previous-attachment-${index}`} style={{ fontSize: '0.85rem' }}>
                            {attachment.url ? (
                              <a
                                href={attachment.url}
                                target="_blank"
                                rel="noreferrer"
                                style={{ color: '#0a84ff' }}
                              >
                                {attachment.label}
                              </a>
                            ) : (
                              attachment.label
                            )}
                          </li>
                        ))}
                      </ul>
                    </div>
                  )}
                </div>
              </div>

              <div
                style={{
                  border: '1px solid #e5e5e7',
                  borderRadius: '10px',
                  padding: '1.25rem',
                  display: 'flex',
                  flexDirection: 'column',
                  gap: '0.75rem',
                }}
              >
                <h4
                  style={{
                    margin: 0,
                    fontSize: '0.95rem',
                    fontWeight: 600,
                  }}
                >
                  System comparison
                </h4>
                <div
                  style={{
                    display: 'grid',
                    rowGap: '0.6rem',
                  }}
                >
                  <div
                    style={{
                      display: 'grid',
                      gridTemplateColumns: 'minmax(160px, 2fr) repeat(3, minmax(110px, 1fr))',
                      fontSize: '0.75rem',
                      fontWeight: 600,
                      textTransform: 'uppercase',
                      letterSpacing: '0.08em',
                      color: '#6e6e73',
                    }}
                  >
                    <span>System</span>
                    <span>Current</span>
                    <span>Previous</span>
                    <span>Delta Score</span>
                  </div>
                  {systemComparisons.map((entry) => {
                    const scoreDeltaValue =
                      typeof entry.scoreDelta === 'number' ? entry.scoreDelta : null
                    return (
                      <div
                        key={entry.name}
                        style={{
                          display: 'grid',
                          gridTemplateColumns:
                            'minmax(160px, 2fr) repeat(3, minmax(110px, 1fr))',
                          gap: '0.4rem',
                          alignItems: 'center',
                          fontSize: '0.85rem',
                          color: '#3a3a3c',
                        }}
                      >
                        <span style={{ fontWeight: 600 }}>{entry.name}</span>
                        <span>
                          {entry.latest
                            ? `${entry.latest.rating} · ${entry.latest.score}/100`
                            : '—'}
                        </span>
                        <span>
                          {entry.previous
                            ? `${entry.previous.rating} · ${entry.previous.score}/100`
                            : '—'}
                        </span>
                        <span
                          style={{
                            fontWeight: 600,
                            color:
                              !scoreDeltaValue || scoreDeltaValue === 0
                                ? '#6e6e73'
                                : scoreDeltaValue > 0
                                ? '#15803d'
                                : '#c53030',
                          }}
                        >
                          {scoreDeltaValue !== null && scoreDeltaValue > 0 ? '+' : ''}
                          {scoreDeltaValue ?? '—'}
                        </span>
                      </div>
                    )
                  })}
                </div>
              </div>

              <div
                style={{
                  border: '1px solid #e5e5e7',
                  borderRadius: '10px',
                  padding: '1.25rem',
                  display: 'flex',
                  flexDirection: 'column',
                  gap: '0.75rem',
                }}
              >
                <h4
                  style={{
                    margin: 0,
                    fontSize: '0.95rem',
                    fontWeight: 600,
                  }}
                >
                  Recommended actions
                </h4>
                <div
                  style={{
                    display: 'grid',
                    gap: '0.75rem',
                    gridTemplateColumns: 'repeat(auto-fit, minmax(220px, 1fr))',
                  }}
                >
                  <div>
                    <strong
                      style={{
                        fontSize: '0.85rem',
                        textTransform: 'uppercase',
                        letterSpacing: '0.05em',
                        color: '#15803d',
                      }}
                    >
                      New this cycle
                    </strong>
                    {recommendedActionDiff.newActions.length > 0 ? (
                      <ul
                        style={{
                          margin: '0.4rem 0 0',
                          paddingLeft: '1.1rem',
                          fontSize: '0.85rem',
                          color: '#3a3a3c',
                          lineHeight: 1.4,
                        }}
                      >
                        {recommendedActionDiff.newActions.map((action) => (
                          <li key={action}>{action}</li>
                        ))}
                      </ul>
                    ) : (
                      <p
                        style={{
                          margin: '0.35rem 0 0',
                          fontSize: '0.825rem',
                          color: '#6e6e73',
                        }}
                      >
                        No new actions added.
                      </p>
                    )}
                  </div>
                  <div>
                    <strong
                      style={{
                        fontSize: '0.85rem',
                        textTransform: 'uppercase',
                        letterSpacing: '0.05em',
                        color: '#c53030',
                      }}
                    >
                      Completed / removed
                    </strong>
                    {recommendedActionDiff.clearedActions.length > 0 ? (
                      <ul
                        style={{
                          margin: '0.4rem 0 0',
                          paddingLeft: '1.1rem',
                          fontSize: '0.85rem',
                          color: '#3a3a3c',
                          lineHeight: 1.4,
                        }}
                      >
                        {recommendedActionDiff.clearedActions.map((action) => (
                          <li key={action}>{action}</li>
                        ))}
                      </ul>
                    ) : (
                      <p
                        style={{
                          margin: '0.35rem 0 0',
                          fontSize: '0.825rem',
                          color: '#6e6e73',
                        }}
                      >
                        No actions closed out.
                      </p>
                    )}
                  </div>
                </div>
              </div>
            </>
          )}
        </div>
      ) : (
        <div
          style={{
            border: '1px solid #e5e5e7',
            borderRadius: '12px',
            overflow: 'hidden',
          }}
        >
          <table
            style={{
              width: '100%',
              borderCollapse: 'collapse',
              fontSize: '0.875rem',
              color: '#1d1d1f',
            }}
          >
            <thead>
              <tr style={{ background: '#f5f5f7' }}>
                <th
                  style={{
                    textAlign: 'left',
                    padding: '0.75rem 1rem',
                    borderBottom: '1px solid #e5e5e7',
                    fontWeight: 600,
                    fontSize: '0.8rem',
                    letterSpacing: '0.04em',
                    textTransform: 'uppercase',
                  }}
                >
                  Scenario
                </th>
                <th
                  style={{
                    textAlign: 'left',
                    padding: '0.75rem 1rem',
                    borderBottom: '1px solid #e5e5e7',
                    fontWeight: 600,
                    fontSize: '0.8rem',
                    letterSpacing: '0.04em',
                    textTransform: 'uppercase',
                  }}
                >
                  Recorded
                </th>
                <th
                  style={{
                    textAlign: 'left',
                    padding: '0.75rem 1rem',
                    borderBottom: '1px solid #e5e5e7',
                    fontWeight: 600,
                    fontSize: '0.8rem',
                    letterSpacing: '0.04em',
                    textTransform: 'uppercase',
                  }}
                >
                  Rating
                </th>
                <th
                  style={{
                    textAlign: 'left',
                    padding: '0.75rem 1rem',
                    borderBottom: '1px solid #e5e5e7',
                    fontWeight: 600,
                    fontSize: '0.8rem',
                    letterSpacing: '0.04em',
                    textTransform: 'uppercase',
                  }}
                >
                  Score
                </th>
                <th
                  style={{
                    textAlign: 'left',
                    padding: '0.75rem 1rem',
                    borderBottom: '1px solid #e5e5e7',
                    fontWeight: 600,
                    fontSize: '0.8rem',
                    letterSpacing: '0.04em',
                    textTransform: 'uppercase',
                  }}
                >
                  Risk
                </th>
                <th
                  style={{
                    textAlign: 'left',
                    padding: '0.75rem 1rem',
                    borderBottom: '1px solid #e5e5e7',
                    fontWeight: 600,
                    fontSize: '0.8rem',
                    letterSpacing: '0.04em',
                    textTransform: 'uppercase',
                  }}
                >
                  Summary
                </th>
              </tr>
            </thead>
            <tbody>
              {assessmentHistory.map((entry, index) => (
                <tr
                  key={`${entry.recordedAt ?? 'draft'}-${index}`}
                  style={{
                    background:
                      index === 0 ? 'rgba(10, 132, 255, 0.08)' : index === 1 ? '#ffffff' : '#fafafb',
                  }}
                >
                  <td style={{ padding: '0.75rem 1rem', borderBottom: '1px solid #f0f0f4' }}>
                    {formatScenarioLabel(entry.scenario)}
                  </td>
                  <td style={{ padding: '0.75rem 1rem', borderBottom: '1px solid #f0f0f4' }}>
                    {formatRecordedTimestamp(entry.recordedAt)}
                  </td>
                  <td style={{ padding: '0.75rem 1rem', borderBottom: '1px solid #f0f0f4' }}>
                    {entry.overallRating}
                  </td>
                  <td style={{ padding: '0.75rem 1rem', borderBottom: '1px solid #f0f0f4' }}>
                    {entry.overallScore}/100
                  </td>
                  <td
                    style={{
                      padding: '0.75rem 1rem',
                      borderBottom: '1px solid #f0f0f4',
                      textTransform: 'capitalize',
                    }}
                  >
                    {entry.riskLevel}
                  </td>
                  <td style={{ padding: '0.75rem 1rem', borderBottom: '1px solid #f0f0f4' }}>
                    {entry.summary || '—'}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  )

  const InlineInspectionHistorySummary = () => (
    <div
      style={{
        border: '1px solid #e5e5e7',
        borderRadius: '12px',
        padding: '1.5rem',
        display: 'flex',
        flexDirection: 'column',
        gap: '1rem',
      }}
    >
      <div
        style={{
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'flex-start',
          gap: '0.75rem',
          flexWrap: 'wrap',
        }}
      >
        <div>
          <h3
            style={{
              margin: 0,
              fontSize: '1.0625rem',
              fontWeight: 600,
            }}
          >
            Inspection History
          </h3>
          <p style={{ margin: '0.2rem 0 0', fontSize: '0.85rem', color: '#6e6e73' }}>
            Track developer inspections saved for this property.
          </p>
        </div>
        <button
          type="button"
          onClick={() => setHistoryModalOpen(true)}
          style={{
            borderRadius: '9999px',
            border: '1px solid #1d1d1f',
            background: '#1d1d1f',
            color: 'white',
            padding: '0.45rem 1rem',
            fontSize: '0.8rem',
            fontWeight: 600,
            cursor: 'pointer',
          }}
        >
          View timeline
        </button>
        <button
          type="button"
          onClick={() => openAssessmentEditor('new')}
          disabled={!capturedProperty}
          style={{
            borderRadius: '9999px',
            border: '1px solid #1d1d1f',
            background: 'white',
            color: '#1d1d1f',
            padding: '0.45rem 1rem',
            fontSize: '0.8rem',
            fontWeight: 600,
            cursor: capturedProperty ? 'pointer' : 'not-allowed',
            opacity: capturedProperty ? 1 : 0.6,
          }}
        >
          Log inspection
        </button>
      </div>
      {assessmentHistoryError ? (
        <p
          style={{
            margin: 0,
            fontSize: '0.85rem',
            color: '#c53030',
          }}
        >
          {assessmentHistoryError}
        </p>
      ) : isLoadingAssessmentHistory ? (
        <p style={{ margin: 0, fontSize: '0.9rem', color: '#6e6e73' }}>
          Loading inspection history...
        </p>
      ) : latestAssessmentEntry ? (
        <div
          style={{
            border: '1px solid #e5e5e7',
            borderRadius: '10px',
            padding: '1rem 1.1rem',
            background: '#f5f5f7',
            display: 'flex',
            flexDirection: 'column',
            gap: '0.4rem',
          }}
        >
          <span
            style={{
              fontSize: '0.75rem',
              fontWeight: 600,
              letterSpacing: '0.08em',
              textTransform: 'uppercase',
              color: '#6e6e73',
            }}
          >
            Most recent inspection
          </span>
          <div
            style={{
              display: 'flex',
              justifyContent: 'space-between',
              alignItems: 'flex-start',
              gap: '0.5rem',
              flexWrap: 'wrap',
            }}
          >
            <div style={{ display: 'flex', flexDirection: 'column', gap: '0.25rem' }}>
              <span style={{ fontSize: '0.95rem', fontWeight: 600 }}>
                {formatScenarioLabel(latestAssessmentEntry.scenario)}
              </span>
              <span style={{ fontSize: '0.85rem', color: '#6e6e73' }}>
                {formatRecordedTimestamp(latestAssessmentEntry.recordedAt)}
              </span>
            </div>
            <div style={{ display: 'flex', flexDirection: 'column', gap: '0.25rem' }}>
              <span style={{ fontSize: '0.8rem', color: '#6e6e73' }}>
                Rating: <strong>{latestAssessmentEntry.overallRating}</strong>
              </span>
              <span style={{ fontSize: '0.8rem', color: '#6e6e73' }}>
                Score: <strong>{latestAssessmentEntry.overallScore}/100</strong>
              </span>
              <span style={{ fontSize: '0.8rem', color: '#6e6e73' }}>
                Risk:{' '}
                <strong style={{ textTransform: 'capitalize' }}>
                  {latestAssessmentEntry.riskLevel}
                </strong>
              </span>
            </div>
          </div>
          <p style={{ margin: 0, fontSize: '0.85rem', color: '#3a3a3c' }}>
            {latestAssessmentEntry.summary || 'No summary recorded.'}
          </p>
          {previousAssessmentEntry && (
            <p style={{ margin: '0.35rem 0 0', fontSize: '0.75rem', color: '#6e6e73' }}>
              Last change:{' '}
              <strong>
                {formatScenarioLabel(previousAssessmentEntry.scenario)} —{' '}
                {formatRecordedTimestamp(previousAssessmentEntry.recordedAt)}
              </strong>
            </p>
          )}
        </div>
      ) : (
        <p style={{ margin: 0, fontSize: '0.9rem', color: '#6e6e73' }}>
          No developer inspections recorded yet. Save an inspection to begin the audit trail.
        </p>
      )}
    </div>
  )

  return (
    <div
      style={{
        padding: '3rem 2rem',
        maxWidth: '1200px',
        margin: '0 auto',
        fontFamily: '-apple-system, BlinkMacSystemFont, "SF Pro Display", "SF Pro Text", system-ui, sans-serif',
        color: '#1d1d1f',
      }}
    >
      {/* Header */}
      <header style={{ marginBottom: '3rem' }}>
        <h1
          style={{
            fontSize: '3rem',
            fontWeight: 700,
            letterSpacing: '-0.015em',
            margin: '0 0 0.5rem',
            lineHeight: 1.1,
          }}
        >
          Site Acquisition
        </h1>
        <p
          style={{
            fontSize: '1.25rem',
            color: '#6e6e73',
            margin: 0,
            lineHeight: 1.5,
            letterSpacing: '-0.005em',
          }}
        >
          Comprehensive property capture and development feasibility analysis for developers
        </p>
      </header>

      {/* Property Capture Form */}
      <section
        style={{
          background: 'white',
          border: '1px solid #d2d2d7',
          borderRadius: '18px',
          padding: '2rem',
          marginBottom: '2rem',
        }}
      >
        <h2
          style={{
            fontSize: '1.5rem',
            fontWeight: 600,
            marginBottom: '1.5rem',
            letterSpacing: '-0.01em',
          }}
        >
          Property Coordinates
        </h2>

        <form onSubmit={handleCapture}>
          <div
            style={{
              display: 'grid',
              gridTemplateColumns: 'repeat(2, 1fr)',
              gap: '1rem',
              marginBottom: '2rem',
            }}
          >
            <div>
              <label
                htmlFor="latitude"
                style={{
                  display: 'block',
                  fontSize: '0.9375rem',
                  fontWeight: 500,
                  marginBottom: '0.5rem',
                  color: '#1d1d1f',
                }}
              >
                Latitude
              </label>
              <input
                id="latitude"
                type="text"
                value={latitude}
                onChange={(e) => setLatitude(e.target.value)}
                style={{
                  width: '100%',
                  padding: '0.875rem 1rem',
                  fontSize: '1rem',
                  border: '1px solid #d2d2d7',
                  borderRadius: '12px',
                  outline: 'none',
                  fontFamily: 'ui-monospace, SFMono-Regular, Menlo, Monaco, monospace',
                  transition: 'all 0.2s ease',
                }}
                onFocus={(e) => {
                  e.currentTarget.style.borderColor = '#1d1d1f'
                  e.currentTarget.style.boxShadow = '0 0 0 4px rgba(0, 0, 0, 0.04)'
                }}
                onBlur={(e) => {
                  e.currentTarget.style.borderColor = '#d2d2d7'
                  e.currentTarget.style.boxShadow = 'none'
                }}
              />
            </div>

            <div>
              <label
                htmlFor="longitude"
                style={{
                  display: 'block',
                  fontSize: '0.9375rem',
                  fontWeight: 500,
                  marginBottom: '0.5rem',
                  color: '#1d1d1f',
                }}
              >
                Longitude
              </label>
              <input
                id="longitude"
                type="text"
                value={longitude}
                onChange={(e) => setLongitude(e.target.value)}
                style={{
                  width: '100%',
                  padding: '0.875rem 1rem',
                  fontSize: '1rem',
                  border: '1px solid #d2d2d7',
                  borderRadius: '12px',
                  outline: 'none',
                  fontFamily: 'ui-monospace, SFMono-Regular, Menlo, Monaco, monospace',
                  transition: 'all 0.2s ease',
                }}
                onFocus={(e) => {
                  e.currentTarget.style.borderColor = '#1d1d1f'
                  e.currentTarget.style.boxShadow = '0 0 0 4px rgba(0, 0, 0, 0.04)'
                }}
                onBlur={(e) => {
                  e.currentTarget.style.borderColor = '#d2d2d7'
                  e.currentTarget.style.boxShadow = 'none'
                }}
              />
            </div>
          </div>

          <h3
            style={{
              fontSize: '1.125rem',
              fontWeight: 600,
              marginBottom: '1rem',
              letterSpacing: '-0.01em',
            }}
          >
            Development Scenarios
          </h3>

          <div
            style={{
              display: 'grid',
              gridTemplateColumns: 'repeat(auto-fit, minmax(280px, 1fr))',
              gap: '1rem',
              marginBottom: '2rem',
            }}
          >
            {SCENARIO_OPTIONS.map((scenario) => {
              const isSelected = selectedScenarios.includes(scenario.value)
              return (
                <button
                  key={scenario.value}
                  type="button"
                  onClick={() => toggleScenario(scenario.value)}
                  style={{
                    background: isSelected ? '#f5f5f7' : 'white',
                    border: `1px solid ${isSelected ? '#1d1d1f' : '#d2d2d7'}`,
                    borderRadius: '12px',
                    padding: '1.25rem',
                    cursor: 'pointer',
                    textAlign: 'left',
                    transition: 'all 0.2s ease',
                    position: 'relative',
                  }}
                  onMouseEnter={(e) => {
                    e.currentTarget.style.transform = 'translateY(-2px)'
                    e.currentTarget.style.boxShadow = '0 8px 16px rgba(0, 0, 0, 0.08)'
                  }}
                  onMouseLeave={(e) => {
                    e.currentTarget.style.transform = 'translateY(0)'
                    e.currentTarget.style.boxShadow = 'none'
                  }}
                >
                  {isSelected && (
                    <div
                      style={{
                        position: 'absolute',
                        top: '1rem',
                        right: '1rem',
                        width: '20px',
                        height: '20px',
                        borderRadius: '50%',
                        background: '#1d1d1f',
                        display: 'flex',
                        alignItems: 'center',
                        justifyContent: 'center',
                        fontSize: '12px',
                        color: 'white',
                      }}
                    >
                      ✓
                    </div>
                  )}
                  <div
                    style={{
                      display: 'flex',
                      alignItems: 'center',
                      gap: '0.75rem',
                      marginBottom: '0.5rem',
                    }}
                  >
                    <span style={{ fontSize: '1.5rem' }}>{scenario.icon}</span>
                    <div
                      style={{
                        fontSize: '1.0625rem',
                        fontWeight: 600,
                        color: '#1d1d1f',
                        letterSpacing: '-0.005em',
                      }}
                    >
                      {scenario.label}
                    </div>
                  </div>
                  <div
                    style={{
                      fontSize: '0.875rem',
                      color: '#6e6e73',
                      lineHeight: 1.4,
                      letterSpacing: '-0.005em',
                    }}
                  >
                    {scenario.description}
                  </div>
                </button>
              )
            })}
          </div>

          <button
            type="submit"
            disabled={isCapturing || selectedScenarios.length === 0}
            style={{
              width: '100%',
              padding: '0.875rem 2rem',
              fontSize: '1.0625rem',
              fontWeight: 500,
              color: 'white',
              background:
                isCapturing || selectedScenarios.length === 0 ? '#d2d2d7' : '#1d1d1f',
              border: 'none',
              borderRadius: '12px',
              cursor:
                isCapturing || selectedScenarios.length === 0 ? 'not-allowed' : 'pointer',
              transition: 'all 0.2s ease',
              letterSpacing: '-0.005em',
            }}
            onMouseEnter={(e) => {
              if (!isCapturing && selectedScenarios.length > 0) {
                e.currentTarget.style.background = '#424245'
              }
            }}
            onMouseLeave={(e) => {
              if (!isCapturing && selectedScenarios.length > 0) {
                e.currentTarget.style.background = '#1d1d1f'
              }
            }}
          >
            {isCapturing ? 'Capturing Property...' : 'Capture Property'}
          </button>

          {error && (
            <div
              style={{
                marginTop: '1rem',
                padding: '1rem',
                background: '#fff5f5',
                border: '1px solid #fed7d7',
                borderRadius: '12px',
                color: '#c53030',
                fontSize: '0.9375rem',
              }}
            >
              {error}
            </div>
          )}

          {capturedProperty && (
            <div
              style={{
                marginTop: '1rem',
                padding: '1rem',
                background: '#f0fdf4',
                border: '1px solid #bbf7d0',
                borderRadius: '12px',
                color: '#15803d',
                fontSize: '0.9375rem',
              }}
            >
              <strong>Property captured successfully</strong>
              <div style={{ marginTop: '0.5rem', fontSize: '0.875rem' }}>
                {capturedProperty.address.fullAddress} • {capturedProperty.address.district}
              </div>
            </div>
          )}
        </form>
      </section>

      {capturedProperty && (
        <section
          style={{
            background: 'white',
            border: '1px solid #d2d2d7',
            borderRadius: '18px',
            padding: '2rem',
            marginBottom: '2rem',
          }}
        >
          <h2
            style={{
              fontSize: '1.5rem',
              fontWeight: 600,
              marginBottom: '1.5rem',
              letterSpacing: '-0.01em',
            }}
          >
            Property Overview
          </h2>
          <div
            style={{
              display: 'grid',
              gap: '1.25rem',
              gridTemplateColumns: 'repeat(auto-fit, minmax(240px, 1fr))',
            }}
          >
            {propertyOverviewCards.map((card, index) => (
              <article
                key={`${card.title}-${index}`}
                style={{
                  border: '1px solid #e5e7eb',
                  borderRadius: '16px',
                  padding: '1.25rem',
                  background: '#f9fafb',
                  display: 'flex',
                  flexDirection: 'column',
                  gap: '0.9rem',
                  minHeight: '100%',
                }}
              >
                <div style={{ display: 'flex', flexDirection: 'column', gap: '0.25rem' }}>
                  <span
                    style={{
                      fontSize: '0.75rem',
                      letterSpacing: '0.08em',
                      textTransform: 'uppercase',
                      fontWeight: 600,
                      color: '#6b7280',
                    }}
                  >
                    {card.title}
                  </span>
                  {card.subtitle && (
                    <span
                      style={{
                        fontSize: '1rem',
                        fontWeight: 600,
                        color: '#111827',
                        letterSpacing: '-0.01em',
                      }}
                    >
                      {card.subtitle}
                    </span>
                  )}
                </div>
                <dl
                  style={{
                    margin: 0,
                    display: 'grid',
                    gridTemplateColumns: 'repeat(auto-fit, minmax(160px, 1fr))',
                    gap: '0.75rem',
                  }}
                >
                  {card.items.map((item) => (
                    <div
                      key={`${card.title}-${item.label}`}
                      style={{
                        display: 'flex',
                        flexDirection: 'column',
                        gap: '0.2rem',
                      }}
                    >
                      <dt
                        style={{
                          margin: 0,
                          fontSize: '0.75rem',
                          fontWeight: 600,
                          letterSpacing: '0.06em',
                          textTransform: 'uppercase',
                          color: '#9ca3af',
                        }}
                      >
                        {item.label}
                      </dt>
                      <dd
                        style={{
                          margin: 0,
                          fontSize: '0.95rem',
                          fontWeight: 600,
                          color: '#1f2937',
                        }}
                      >
                        {item.value}
                      </dd>
                    </div>
                  ))}
                </dl>
                {card.tags && card.tags.length > 0 && (
                  <div
                    style={{
                      display: 'flex',
                      flexWrap: 'wrap',
                      gap: '0.4rem',
                    }}
                  >
                    {card.tags.map((tag) => (
                      <span
                        key={`${card.title}-${tag}`}
                        style={{
                          display: 'inline-flex',
                          alignItems: 'center',
                          padding: '0.25rem 0.6rem',
                          borderRadius: '9999px',
                          background: '#e0e7ff',
                          color: '#3730a3',
                          fontSize: '0.75rem',
                          fontWeight: 600,
                        }}
                      >
                        {tag}
                      </span>
                    ))}
                  </div>
                )}
                {card.note && (
                  <p
                    style={{
                      margin: 0,
                      fontSize: '0.75rem',
                      color: '#6b7280',
                    }}
                  >
                    {card.note}
                  </p>
                )}
              </article>
            ))}
          </div>
          {previewJob && (
            <div
              style={{
                marginTop: '2rem',
                display: 'flex',
                flexDirection: 'column',
                gap: '0.75rem',
              }}
            >
              <div
                style={{
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'space-between',
                }}
              >
                <h3
                  style={{
                    margin: 0,
                    fontSize: '1.1rem',
                    fontWeight: 600,
                    letterSpacing: '-0.01em',
                    color: '#111827',
                  }}
                >
                  Development Preview
                </h3>
                <span
                  style={{
                    fontSize: '0.75rem',
                    fontWeight: 600,
                    letterSpacing: '0.08em',
                    color: '#4b5563',
                    textTransform: 'uppercase',
                  }}
                >
                  {previewJob.status.toUpperCase()}
                </span>
              </div>
              <Preview3DViewer
                previewUrl={previewJob.previewUrl}
                metadataUrl={previewViewerMetadataUrl}
                status={previewJob.status}
                thumbnailUrl={previewJob.thumbnailUrl}
                layerVisibility={previewLayerVisibility}
                focusLayerId={previewFocusLayerId}
              />
              <p style={{ margin: 0, fontSize: '0.85rem', color: '#4b5563' }}>
                Geometry detail:{' '}
                <strong>{describeDetailLevel(previewJob.geometryDetailLevel)}</strong>
              </p>
            </div>
          )}
          {previewJob && (
            <div
              style={{
                marginTop: '1rem',
                display: 'flex',
                flexWrap: 'wrap',
                alignItems: 'flex-end',
                gap: '1rem',
              }}
            >
              <label
                style={{
                  display: 'flex',
                  flexDirection: 'column',
                  gap: '0.4rem',
                  fontSize: '0.85rem',
                  color: '#374151',
                }}
              >
                <span style={{ fontWeight: 600, color: '#111827' }}>Geometry detail</span>
                <select
                  value={previewDetailLevel}
                  onChange={(event) =>
                    setPreviewDetailLevel(event.target.value as GeometryDetailLevel)
                  }
                  disabled={isRefreshingPreview}
                  style={{
                    minWidth: '240px',
                    padding: '0.45rem 0.65rem',
                    borderRadius: '8px',
                    border: '1px solid #d1d5db',
                    background: isRefreshingPreview ? '#f3f4f6' : '#fff',
                    color: '#111827',
                  }}
                >
                  {PREVIEW_DETAIL_OPTIONS.map((option) => (
                    <option key={option} value={option}>
                      {PREVIEW_DETAIL_LABELS[option]}
                    </option>
                  ))}
                </select>
                <span style={{ fontSize: '0.8rem', color: '#6b7280' }}>
                  {previewDetailLevel === 'simple'
                    ? 'Fast render for smoke testing.'
                    : 'Detailed render with setbacks, podiums, and floor lines.'}
                </span>
              </label>
              <button
                type="button"
                onClick={handleRefreshPreview}
                disabled={isRefreshingPreview}
                style={{
                  padding: '0.5rem 0.85rem',
                  borderRadius: '9999px',
                  border: '1px solid',
                  borderColor: isRefreshingPreview ? '#cbd5f5' : '#6366f1',
                  background: isRefreshingPreview ? '#eef2ff' : '#4f46e5',
                  color: '#fff',
                  fontSize: '0.875rem',
                  fontWeight: 600,
                  cursor: isRefreshingPreview ? 'wait' : 'pointer',
                  transition: 'background 0.2s ease',
                }}
              >
                {isRefreshingPreview ? 'Refreshing preview…' : 'Refresh preview render'}
              </button>
              <span style={{ fontSize: '0.85rem', color: '#4b5563' }}>
                Status updates automatically while processing.
              </span>
            </div>
          )}
          {previewJob && (
            <section
              style={{
                marginTop: '1.5rem',
                border: '1px solid #e5e7eb',
                borderRadius: '16px',
                padding: '1.2rem',
                background: '#ffffff',
                display: 'flex',
                flexDirection: 'column',
                gap: '1rem',
              }}
            >
              <div
                style={{
                  display: 'flex',
                  justifyContent: 'space-between',
                  flexWrap: 'wrap',
                  gap: '0.75rem',
                  alignItems: 'center',
                }}
              >
                <div>
                  <h4
                    style={{
                      margin: 0,
                      fontSize: '1rem',
                      fontWeight: 600,
                      letterSpacing: '-0.01em',
                      color: '#111827',
                    }}
                  >
                    Rendered layers
                  </h4>
                  <p style={{ margin: 0, fontSize: '0.9rem', color: '#4b5563' }}>
                    Hide, solo, and zoom specific massing layers directly from the Site Acquisition
                    workspace while reviewing the Phase 2B preview.
                  </p>
                </div>
                <div
                  style={{
                    fontSize: '0.85rem',
                    fontWeight: 600,
                    color: previewMetadataError ? '#b45309' : '#4b5563',
                  }}
                >
                  {isPreviewMetadataLoading
                    ? 'Loading preview metadata…'
                    : previewMetadataError
                      ? `Metadata error: ${previewMetadataError}`
                      : `${previewLayerMetadata.length} layers${
                          hiddenLayerCount ? ` · ${hiddenLayerCount} hidden` : ''
                        }`}
                </div>
              </div>
              <div style={{ display: 'flex', flexWrap: 'wrap', gap: '0.5rem' }}>
                <button
                  type="button"
                  onClick={handleShowAllLayers}
                  disabled={
                    isPreviewMetadataLoading ||
                    !previewLayerMetadata.length ||
                    (hiddenLayerCount === 0 && !previewFocusLayerId)
                  }
                  style={{
                    padding: '0.35rem 0.8rem',
                    borderRadius: '9999px',
                    border: '1px solid #d1d5db',
                    background: '#f9fafb',
                    fontWeight: 600,
                    color: '#111827',
                    fontSize: '0.85rem',
                  }}
                >
                  Show all layers
                </button>
                <button
                  type="button"
                  onClick={handleResetLayerFocus}
                  disabled={!previewFocusLayerId}
                  style={{
                    padding: '0.35rem 0.8rem',
                    borderRadius: '9999px',
                    border: '1px solid #d1d5db',
                    background: '#f9fafb',
                    fontWeight: 600,
                    color: previewFocusLayerId ? '#111827' : '#9ca3af',
                    fontSize: '0.85rem',
                  }}
                >
                  Reset view
                </button>
              </div>
              {!isPreviewMetadataLoading && !previewMetadataError && previewLayerMetadata.length === 0 && (
                <p style={{ margin: 0, fontSize: '0.85rem', color: '#4b5563' }}>
                  Layer metrics will populate once the preview metadata asset is ready. Refresh the
                  render if the queue has expired.
                </p>
              )}
              {previewLayerMetadata.length > 0 && (
                <div style={{ overflowX: 'auto' }}>
                  <table
                    style={{
                      width: '100%',
                      borderCollapse: 'collapse',
                      minWidth: '640px',
                    }}
                  >
                    <thead>
                      <tr style={{ textAlign: 'left', borderBottom: '1px solid #e5e7eb' }}>
                        <th style={{ padding: '0.5rem', fontSize: '0.8rem', color: '#6b7280' }}>Layer</th>
                        <th style={{ padding: '0.5rem', fontSize: '0.8rem', color: '#6b7280' }}>Allocation</th>
                        <th style={{ padding: '0.5rem', fontSize: '0.8rem', color: '#6b7280' }}>GFA (sqm)</th>
                        <th style={{ padding: '0.5rem', fontSize: '0.8rem', color: '#6b7280' }}>NIA (sqm)</th>
                        <th style={{ padding: '0.5rem', fontSize: '0.8rem', color: '#6b7280' }}>Est. height (m)</th>
                        <th style={{ padding: '0.5rem', fontSize: '0.8rem', color: '#6b7280' }}>Est. floors</th>
                        <th style={{ padding: '0.5rem', fontSize: '0.8rem', color: '#6b7280' }}>Controls</th>
                      </tr>
                    </thead>
                    <tbody>
                      {previewLayerMetadata.map((layer) => {
                        const isVisible = previewLayerVisibility[layer.id] !== false
                        return (
                          <tr key={layer.id} style={{ borderBottom: '1px solid #f3f4f6' }}>
                            <th
                              scope="row"
                              style={{
                                padding: '0.65rem 0.5rem',
                                fontSize: '0.9rem',
                                fontWeight: 600,
                                color: '#111827',
                                display: 'flex',
                                alignItems: 'center',
                                gap: '0.5rem',
                              }}
                            >
                              <span
                                style={{
                                  display: 'inline-flex',
                                  width: '14px',
                                  height: '14px',
                                  borderRadius: '9999px',
                                  background: layer.color,
                                  boxShadow: '0 0 0 1px rgb(255 255 255 / 0.5)',
                                }}
                                aria-hidden="true"
                              />
                              {toTitleCase(layer.name)}
                            </th>
                            <td style={{ padding: '0.65rem 0.5rem', color: '#374151' }}>
                              {layer.metrics.allocationPct != null
                                ? `${formatNumberMetric(layer.metrics.allocationPct, {
                                    maximumFractionDigits:
                                      layer.metrics.allocationPct >= 10 ? 0 : 1,
                                  })}%`
                                : '—'}
                            </td>
                            <td style={{ padding: '0.65rem 0.5rem', color: '#374151' }}>
                              {layer.metrics.gfaSqm != null
                                ? `${formatNumberMetric(layer.metrics.gfaSqm, {
                                    maximumFractionDigits:
                                      layer.metrics.gfaSqm >= 1000 ? 0 : 1,
                                  })}`
                                : '—'}
                            </td>
                            <td style={{ padding: '0.65rem 0.5rem', color: '#374151' }}>
                              {layer.metrics.niaSqm != null
                                ? `${formatNumberMetric(layer.metrics.niaSqm, {
                                    maximumFractionDigits:
                                      layer.metrics.niaSqm >= 1000 ? 0 : 1,
                                  })}`
                                : '—'}
                            </td>
                            <td style={{ padding: '0.65rem 0.5rem', color: '#374151' }}>
                              {layer.metrics.heightM != null
                                ? `${formatNumberMetric(layer.metrics.heightM, {
                                    maximumFractionDigits: 1,
                                  })}`
                                : '—'}
                            </td>
                            <td style={{ padding: '0.65rem 0.5rem', color: '#374151' }}>
                              {layer.metrics.floors != null
                                ? formatNumberMetric(layer.metrics.floors, {
                                    maximumFractionDigits: 0,
                                  })
                                : '—'}
                            </td>
                            <td
                              style={{
                                padding: '0.65rem 0.5rem',
                                display: 'flex',
                                flexWrap: 'wrap',
                                gap: '0.4rem',
                              }}
                            >
                              <button
                                type="button"
                                onClick={() => handleToggleLayerVisibility(layer.id)}
                                style={{
                                  padding: '0.25rem 0.6rem',
                                  borderRadius: '9999px',
                                  border: '1px solid #d1d5db',
                                  background: isVisible ? '#f9fafb' : '#fee2e2',
                                  color: isVisible ? '#111827' : '#991b1b',
                                  fontSize: '0.8rem',
                                  fontWeight: 600,
                                }}
                              >
                                {isVisible ? 'Hide' : 'Show'}
                              </button>
                              <button
                                type="button"
                                onClick={() => handleSoloPreviewLayer(layer.id)}
                                style={{
                                  padding: '0.25rem 0.6rem',
                                  borderRadius: '9999px',
                                  border: '1px solid #d1d5db',
                                  background: '#f9fafb',
                                  fontSize: '0.8rem',
                                  fontWeight: 600,
                                  color: '#111827',
                                }}
                              >
                                Solo
                              </button>
                              <button
                                type="button"
                                onClick={() => handleFocusLayer(layer.id)}
                                style={{
                                  padding: '0.25rem 0.6rem',
                                  borderRadius: '9999px',
                                  border: '1px solid #d1d5db',
                                  background:
                                    previewFocusLayerId === layer.id ? '#e0e7ff' : '#f9fafb',
                                  color:
                                    previewFocusLayerId === layer.id ? '#312e81' : '#111827',
                                  fontSize: '0.8rem',
                                  fontWeight: 600,
                                }}
                              >
                                {previewFocusLayerId === layer.id ? 'Focused' : 'Zoom'}
                              </button>
                            </td>
                          </tr>
                        )
                      })}
                    </tbody>
                  </table>
                </div>
              )}
            </section>
          )}
          {colorLegendEntries.length > 0 && (
            <section
              style={{
                marginTop: '1.25rem',
                border: '1px solid #e5e7eb',
                borderRadius: '16px',
                padding: '1.25rem',
                background: '#ffffff',
                display: 'flex',
                flexDirection: 'column',
                gap: '1rem',
              }}
            >
              <div
                style={{
                  display: 'flex',
                  justifyContent: 'space-between',
                  flexWrap: 'wrap',
                  gap: '0.75rem',
                  alignItems: 'center',
                }}
              >
                <div>
                  <h4
                    style={{
                      margin: 0,
                      fontSize: '1rem',
                      fontWeight: 600,
                      letterSpacing: '-0.01em',
                      color: '#111827',
                    }}
                  >
                    Colour legend editor
                  </h4>
                  <p style={{ margin: 0, fontSize: '0.9rem', color: '#4b5563' }}>
                    Update the palette, labels, and descriptions before regenerating the preview so
                    property captures and developer decks stay consistent.
                  </p>
                </div>
                <span
                  style={{
                    fontSize: '0.85rem',
                    fontWeight: 600,
                    color: legendHasPendingChanges ? '#b45309' : '#10b981',
                  }}
                >
                  {legendHasPendingChanges
                    ? 'Palette edits pending preview refresh'
                    : 'Palette synced with latest preview'}
                </span>
              </div>
              <div
                style={{
                  display: 'grid',
                  gridTemplateColumns: 'repeat(auto-fit, minmax(240px, 1fr))',
                  gap: '1rem',
                }}
              >
                {colorLegendEntries.map((entry) => (
                  <div
                    key={entry.assetType}
                    style={{
                      border: '1px solid #e5e7eb',
                      borderRadius: '12px',
                      padding: '0.9rem',
                      background: '#f9fafb',
                      display: 'flex',
                      flexDirection: 'column',
                      gap: '0.6rem',
                    }}
                  >
                    <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                      <strong style={{ fontSize: '0.9rem', color: '#111827' }}>{entry.assetType}</strong>
                      <input
                        type="color"
                        aria-label={`Colour for ${entry.assetType}`}
                        value={entry.color}
                        onChange={(event) =>
                          handleLegendEntryChange(entry.assetType, 'color', event.target.value)
                        }
                        style={{
                          width: '36px',
                          height: '24px',
                          border: '1px solid #d1d5db',
                          borderRadius: '6px',
                          padding: 0,
                          background: '#fff',
                        }}
                      />
                    </div>
                    <label
                      style={{
                        display: 'flex',
                        flexDirection: 'column',
                        gap: '0.35rem',
                        fontSize: '0.8rem',
                        color: '#4b5563',
                      }}
                    >
                      Label
                      <input
                        type="text"
                        value={entry.label}
                        onChange={(event) =>
                          handleLegendEntryChange(entry.assetType, 'label', event.target.value)
                        }
                        style={{
                          padding: '0.4rem 0.55rem',
                          borderRadius: '8px',
                          border: '1px solid #d1d5db',
                          fontSize: '0.9rem',
                        }}
                      />
                    </label>
                    <label
                      style={{
                        display: 'flex',
                        flexDirection: 'column',
                        gap: '0.35rem',
                        fontSize: '0.8rem',
                        color: '#4b5563',
                      }}
                    >
                      Description
                      <textarea
                        value={entry.description ?? ''}
                        onChange={(event) =>
                          handleLegendEntryChange(
                            entry.assetType,
                            'description',
                            event.target.value,
                          )
                        }
                        rows={2}
                        style={{
                          resize: 'vertical',
                          minHeight: '56px',
                          padding: '0.4rem 0.55rem',
                          borderRadius: '8px',
                          border: '1px solid #d1d5db',
                          fontSize: '0.9rem',
                        }}
                      />
                    </label>
                  </div>
                ))}
              </div>
              <div
                style={{
                  display: 'flex',
                  flexWrap: 'wrap',
                  gap: '0.75rem',
                  alignItems: 'center',
                }}
              >
                <button
                  type="button"
                  onClick={handleLegendReset}
                  disabled={legendBaselineRef.current.length === 0}
                  style={{
                    padding: '0.45rem 0.85rem',
                    borderRadius: '9999px',
                    border: '1px solid #d1d5db',
                    background: '#f9fafb',
                    fontWeight: 600,
                    color: '#111827',
                    fontSize: '0.85rem',
                  }}
                >
                  Reset to preview defaults
                </button>
                <p style={{ margin: 0, fontSize: '0.85rem', color: '#4b5563' }}>
                  Use “Refresh preview render” after editing the palette so GLTF colours match the
                  updated legend.
                </p>
              </div>
            </section>
          )}
          {layerBreakdown.length > 0 && (
            <section
              style={{
                marginTop: '2rem',
                border: '1px solid #e5e7eb',
                borderRadius: '16px',
                padding: '1.5rem',
                background: '#ffffff',
                display: 'flex',
                flexDirection: 'column',
                gap: '1.25rem',
              }}
            >
              <div
                style={{
                  display: 'flex',
                  flexDirection: 'column',
                  gap: '0.35rem',
                }}
              >
                <h4
                  style={{
                    margin: 0,
                    fontSize: '1rem',
                    fontWeight: 600,
                    letterSpacing: '-0.01em',
                    color: '#111827',
                  }}
                >
                  Layer breakdown
                </h4>
                <p
                  style={{
                    margin: 0,
                    fontSize: '0.9rem',
                    color: '#4b5563',
                  }}
                >
                  Detailed optimiser output per massing layer (allocation, GFA, NIA, and height).
                </p>
              </div>
              <div
                style={{
                  display: 'grid',
                  gridTemplateColumns: 'repeat(auto-fit, minmax(220px, 1fr))',
                  gap: '1rem',
                }}
              >
                {layerBreakdown.map((layer) => (
                  <article
                    key={layer.id}
                    style={{
                      border: '1px solid #e5e7eb',
                      borderRadius: '12px',
                      padding: '1rem',
                      display: 'flex',
                      flexDirection: 'column',
                      gap: '0.75rem',
                      background: '#f9fafb',
                    }}
                  >
                    <div style={{ display: 'flex', alignItems: 'center', gap: '0.65rem' }}>
                      <span
                        aria-hidden="true"
                        style={{
                          width: '14px',
                          height: '14px',
                          borderRadius: '9999px',
                          background: layer.color,
                          boxShadow: '0 0 0 1px rgb(255 255 255 / 0.8)',
                        }}
                      />
                      <div style={{ display: 'flex', flexDirection: 'column', gap: '0.15rem' }}>
                        <span
                          style={{
                            fontWeight: 600,
                            letterSpacing: '-0.01em',
                            color: '#111827',
                          }}
                        >
                          {layer.label}
                        </span>
                        <span style={{ fontSize: '0.85rem', color: '#6b7280' }}>{layer.subtitle}</span>
                      </div>
                    </div>
                    <dl
                      style={{
                        margin: 0,
                        display: 'grid',
                        gridTemplateColumns: 'repeat(auto-fit, minmax(120px, 1fr))',
                        gap: '0.5rem',
                      }}
                    >
                      {layer.metrics.map((metric) => (
                        <div
                          key={`${layer.id}-${metric.label}`}
                          style={{ display: 'flex', flexDirection: 'column', gap: '0.15rem' }}
                        >
                          <dt
                            style={{
                              margin: 0,
                              fontSize: '0.7rem',
                              letterSpacing: '0.08em',
                              textTransform: 'uppercase',
                              color: '#9ca3af',
                              fontWeight: 600,
                            }}
                          >
                            {metric.label}
                          </dt>
                          <dd
                            style={{
                              margin: 0,
                              fontWeight: 600,
                              color: '#1f2937',
                              fontSize: '0.95rem',
                            }}
                          >
                            {metric.value}
                          </dd>
                        </div>
                      ))}
                    </dl>
                    {layer.description && (
                      <p
                        style={{
                          margin: 0,
                          fontSize: '0.8rem',
                          color: '#4b5563',
                        }}
                      >
                        {layer.description}
                      </p>
                    )}
                  </article>
                ))}
              </div>
            </section>
          )}
        </section>
      )}

      {capturedProperty && scenarioFocusOptions.length > 0 && (
        <section
          style={{
            background: '#f5f5f7',
            border: '1px solid #e5e5e7',
            borderRadius: '16px',
            padding: '1.5rem',
            marginBottom: '2rem',
          }}
        >
          <div
            style={{
              display: 'flex',
              flexWrap: 'wrap',
              alignItems: 'center',
              justifyContent: 'space-between',
              gap: '1rem',
              marginBottom: '1rem',
            }}
          >
            <div style={{ display: 'flex', flexDirection: 'column', gap: '0.35rem' }}>
              <span
                style={{
                  fontSize: '0.8125rem',
                  fontWeight: 600,
                  letterSpacing: '0.08em',
                  textTransform: 'uppercase',
                  color: '#6e6e73',
                }}
              >
                Scenario focus
              </span>
              <span style={{ fontSize: '0.95rem', color: '#3a3a3c' }}>
                Switch context to see checklist, feasibility, and inspections for the
                selected development path.
              </span>
            </div>
            <div
              style={{
                display: 'flex',
                alignItems: 'center',
                gap: '0.75rem',
                flexWrap: 'wrap',
              }}
            >
              <div
                style={{
                  display: 'flex',
                  flexDirection: 'column',
                  gap: '0.2rem',
                  minWidth: '180px',
                }}
              >
                <span
                  style={{
                    fontWeight: 700,
                    color: '#0f172a',
                  }}
                >
                  {activeScenarioSummary.label}
                </span>
                <span style={{ fontSize: '0.82rem', color: '#475569' }}>
                  {activeScenarioSummary.headline}
                </span>
                {activeScenarioSummary.detail && (
                  <span style={{ fontSize: '0.78rem', color: '#64748b' }}>
                    {activeScenarioSummary.detail}
                  </span>
                )}
              </div>
              <div
                style={{
                  display: 'flex',
                  gap: '0.65rem',
                  flexWrap: 'wrap',
                }}
              >
                <button
                  type="button"
                  onClick={handleScenarioComparisonScroll}
                  disabled={!scenarioComparisonVisible}
                  style={{
                    borderRadius: '9999px',
                    border: '1px solid #1d1d1f',
                    background: scenarioComparisonVisible ? '#1d1d1f' : '#f5f5f7',
                    color: scenarioComparisonVisible ? 'white' : '#a1a1aa',
                    padding: '0.45rem 0.95rem',
                    fontSize: '0.78rem',
                    fontWeight: 600,
                    cursor: scenarioComparisonVisible ? 'pointer' : 'not-allowed',
                  }}
                >
                  Compare scenarios
                </button>
                <button
                  type="button"
                  onClick={() => setQuickAnalysisHistoryOpen(true)}
                  disabled={quickAnalysisHistory.length === 0}
                  style={{
                    borderRadius: '9999px',
                    border: '1px solid #d2d2d7',
                    background:
                      quickAnalysisHistory.length === 0 ? '#f5f5f7' : 'white',
                    color:
                      quickAnalysisHistory.length === 0 ? '#a1a1aa' : '#1d1d1f',
                    padding: '0.45rem 0.95rem',
                    fontSize: '0.78rem',
                    fontWeight: 600,
                    cursor:
                      quickAnalysisHistory.length === 0 ? 'not-allowed' : 'pointer',
                  }}
                >
                  Quick analysis history ({quickAnalysisHistory.length})
                </button>
                <button
                  type="button"
                  onClick={() => setHistoryModalOpen(true)}
                  style={{
                    borderRadius: '9999px',
                    border: '1px solid #d2d2d7',
                    background: 'white',
                    color: '#1d1d1f',
                    padding: '0.45rem 0.95rem',
                    fontSize: '0.78rem',
                    fontWeight: 600,
                    cursor: 'pointer',
                  }}
                >
                  Inspection history
                </button>
              </div>
            </div>
          </div>
          <div
            style={{
              display: 'flex',
              flexWrap: 'wrap',
              gap: '0.75rem',
            }}
          >
            {scenarioFocusOptions.map((scenarioKey) => {
              const option =
                scenarioKey === 'all' ? null : scenarioLookup.get(scenarioKey)
              const label =
                scenarioKey === 'all'
                  ? 'All scenarios'
                  : option?.label ?? formatScenarioLabel(scenarioKey)
              const icon = scenarioKey === 'all' ? '🌐' : option?.icon ?? '🏗️'
              const isActive = activeScenario === scenarioKey
              const progressStats =
                scenarioKey === 'all'
                  ? displaySummary
                  : scenarioChecklistProgress[scenarioKey]
              const progressLabel = progressStats
                ? `${progressStats.completed}/${progressStats.total || 0}`
                : null
              const progressPercent =
                progressStats && progressStats.total > 0
                  ? Math.round((progressStats.completed / progressStats.total) * 100)
                  : null

              return (
                <button
                  key={scenarioKey}
                  type="button"
                  onClick={() => setActiveScenario(scenarioKey)}
                  aria-pressed={isActive}
                  style={{
                    display: 'inline-flex',
                    alignItems: 'center',
                    gap: '0.65rem',
                    borderRadius: '9999px',
                    border: `1px solid ${isActive ? '#0071e3' : '#d2d2d7'}`,
                    background: isActive ? '#dbeafe' : 'white',
                    color: isActive ? '#0c4a6e' : '#1d1d1f',
                    padding: '0.55rem 1.1rem',
                    fontSize: '0.95rem',
                    fontWeight: 600,
                    cursor: 'pointer',
                    transition: 'all 0.2s ease',
                  }}
                >
                  <span style={{ fontSize: '1.2rem' }}>{icon}</span>
                  <span>{label}</span>
                  {progressLabel && (
                    <span
                      style={{
                        display: 'inline-flex',
                        alignItems: 'center',
                        justifyContent: 'center',
                        minWidth: '2.5rem',
                        padding: '0.2rem 0.6rem',
                        borderRadius: '9999px',
                        background: isActive ? '#1d4ed8' : '#e5e7eb',
                        color: isActive ? 'white' : '#1f2937',
                        fontSize: '0.75rem',
                        fontWeight: 600,
                      }}
                      title={
                        progressPercent !== null
                          ? `${progressStats?.completed ?? 0} of ${
                              progressStats?.total ?? 0
                            } items completed (${progressPercent}%)`
                          : undefined
                      }
                    >
                      {progressLabel}
                    </span>
                  )}
                </button>
              )
            })}
          </div>

        </section>
      )}

      {/* Due Diligence Checklist */}
      <section
        style={{
          background: 'white',
          border: '1px solid #d2d2d7',
          borderRadius: '18px',
          padding: '2rem',
          marginBottom: '2rem',
        }}
      >
        <div
          style={{
            display: 'flex',
            justifyContent: 'space-between',
            alignItems: 'flex-start',
            marginBottom: '1.5rem',
          }}
        >
          <div>
            <h2
              style={{
                fontSize: '1.5rem',
                fontWeight: 600,
                marginBottom: '0.5rem',
                letterSpacing: '-0.01em',
              }}
            >
              Due Diligence Checklist
            </h2>
            {displaySummary && (
              <p
                style={{
                  margin: 0,
                  fontSize: '0.9375rem',
                  color: '#6e6e73',
                }}
              >
                {activeScenario === 'all'
                  ? 'Overall progress'
                  : `${activeScenarioDetails?.label ?? 'Scenario'}`}
                : {displaySummary.completed} of {displaySummary.total} items completed (
                {displaySummary.completionPercentage.toFixed(0)}%)
              </p>
            )}
            {activeScenarioDetails?.description && (
              <p
                style={{
                  margin: '0.25rem 0 0',
                  fontSize: '0.875rem',
                  color: '#86868b',
                }}
              >
                {activeScenarioDetails.description}
            </p>
          )}
        </div>
        <div
          style={{
            display: 'flex',
            alignItems: 'center',
            gap: '0.75rem',
          }}
        >
          <Link
            to="/app/site-acquisition/checklist-templates"
            style={{
              display: 'inline-flex',
              alignItems: 'center',
              gap: '0.35rem',
              background: '#eff3ff',
              borderRadius: '999px',
              padding: '0.4rem 0.9rem',
              fontWeight: 600,
              color: '#1d4ed8',
              textDecoration: 'none',
              border: '1px solid #c7dafc',
            }}
          >
            Manage templates
          </Link>
        </div>
      </div>

        {availableChecklistScenarios.length > 0 && (
          <div
            style={{
              display: 'flex',
              flexWrap: 'wrap',
              gap: '0.75rem',
              marginBottom: '1.5rem',
            }}
          >
            <button
              type="button"
              onClick={() => setActiveScenario('all')}
              style={{
                display: 'flex',
                alignItems: 'center',
                gap: '0.5rem',
                padding: '0.5rem 0.85rem',
                borderRadius: '9999px',
                border: `1px solid ${
                  activeScenario === 'all' ? '#1d1d1f' : '#d2d2d7'
                }`,
                background: activeScenario === 'all' ? '#1d1d1f' : '#f5f5f7',
                color: activeScenario === 'all' ? 'white' : '#1d1d1f',
                cursor: 'pointer',
                fontSize: '0.875rem',
                fontWeight: 500,
                transition: 'all 0.2s ease',
              }}
            >
              All scenarios
            </button>
            {availableChecklistScenarios.map((scenario) => {
              const option = scenarioLookup.get(scenario)
              const isActive = activeScenario === scenario
              return (
                <button
                  key={scenario}
                  type="button"
                  onClick={() => setActiveScenario(scenario)}
                  style={{
                    display: 'flex',
                    alignItems: 'center',
                    gap: '0.5rem',
                    padding: '0.5rem 0.85rem',
                    borderRadius: '9999px',
                    border: `1px solid ${isActive ? '#1d1d1f' : '#d2d2d7'}`,
                    background: isActive ? '#1d1d1f' : '#f5f5f7',
                    color: isActive ? 'white' : '#1d1d1f',
                    cursor: 'pointer',
                    fontSize: '0.875rem',
                    fontWeight: 500,
                    transition: 'all 0.2s ease',
                  }}
                >
                  {option?.icon ? (
                    <span style={{ fontSize: '1rem' }}>{option.icon}</span>
                  ) : null}
                  <span>{option?.label ?? formatCategoryName(scenario)}</span>
                </button>
              )
            })}
          </div>
        )}

        {isLoadingChecklist ? (
          <div
            style={{
              padding: '3rem 2rem',
              textAlign: 'center',
              color: '#6e6e73',
            }}
          >
            <p>Loading checklist...</p>
          </div>
        ) : !capturedProperty ? (
          <div
            style={{
              padding: '3rem 2rem',
              textAlign: 'center',
              color: '#6e6e73',
              background: '#f5f5f7',
              borderRadius: '12px',
            }}
          >
            <div style={{ fontSize: '3rem', marginBottom: '1rem' }}>📋</div>
            <p style={{ margin: 0, fontSize: '1.0625rem' }}>
              Capture a property to view the comprehensive due diligence checklist
            </p>
            <p style={{ margin: '0.5rem 0 0', fontSize: '0.9375rem' }}>
              Automatically generated based on selected development scenarios
            </p>
          </div>
        ) : checklistItems.length === 0 ? (
          <div
            style={{
              padding: '2rem',
              textAlign: 'center',
              color: '#6e6e73',
              background: '#f5f5f7',
              borderRadius: '12px',
            }}
          >
            <p>No checklist items found for this property.</p>
          </div>
        ) : filteredChecklistItems.length === 0 ? (
          <div
            style={{
              padding: '2rem',
              textAlign: 'center',
              color: '#6e6e73',
              background: '#f5f5f7',
              borderRadius: '12px',
            }}
          >
            <p>
              No checklist items for{' '}
              {activeScenarioDetails?.label ?? 'this scenario'} yet.
            </p>
          </div>
        ) : (
          <>
            {/* Progress bar */}
            {displaySummary && (
              <div
                style={{
                  marginBottom: '1.5rem',
                  background: '#f5f5f7',
                  borderRadius: '12px',
                  height: '8px',
                  overflow: 'hidden',
                }}
              >
                <div
                  style={{
                    width: `${displaySummary.completionPercentage}%`,
                    height: '100%',
                    background: 'linear-gradient(90deg, #0071e3 0%, #005bb5 100%)',
                    transition: 'width 0.3s ease',
                  }}
                />
              </div>
            )}

            {/* Group by category */}
            {Object.entries(
              filteredChecklistItems.reduce((acc, item) => {
                const category = item.category
                if (!acc[category]) {
                  acc[category] = []
                }
                acc[category].push(item)
                return acc
              }, {} as Record<string, ChecklistItem[]>),
            ).map(([category, items]: [string, ChecklistItem[]]) => (
              <div
                key={category}
                style={{
                  marginBottom: '1.5rem',
                  border: '1px solid #e5e5e7',
                  borderRadius: '12px',
                  overflow: 'hidden',
                }}
              >
                <button
                  type="button"
                  onClick={() =>
                    setSelectedCategory(selectedCategory === category ? null : category)
                  }
                  style={{
                    width: '100%',
                    padding: '1rem 1.25rem',
                    background: '#f5f5f7',
                    border: 'none',
                    display: 'flex',
                    justifyContent: 'space-between',
                    alignItems: 'center',
                    cursor: 'pointer',
                    fontSize: '1rem',
                    fontWeight: 600,
                    textAlign: 'left',
                  }}
                >
                  <span>{formatCategoryName(category)}</span>
                  <span
                    style={{
                      fontSize: '0.875rem',
                      color: '#6e6e73',
                    }}
                  >
                    {items.filter((item) => item.status === 'completed').length}/{items.length}
                  </span>
                </button>
                {(selectedCategory === category || selectedCategory === null) && (
                  <div style={{ padding: '0' }}>
                    {items.map((item) => (
                      <div
                        key={item.id}
                        style={{
                          padding: '1rem 1.25rem',
                          borderTop: '1px solid #e5e5e7',
                          display: 'flex',
                          gap: '1rem',
                          alignItems: 'flex-start',
                        }}
                      >
                        <select
                          value={item.status}
                          onChange={(e) =>
                            handleChecklistUpdate(
                              item.id,
                              e.target.value as
                                | 'pending'
                                | 'in_progress'
                                | 'completed'
                                | 'not_applicable',
                            )
                          }
                          style={{
                            padding: '0.5rem',
                            border: '1px solid #d2d2d7',
                            borderRadius: '8px',
                            fontSize: '0.875rem',
                            background: 'white',
                            cursor: 'pointer',
                          }}
                        >
                          <option value="pending">Pending</option>
                          <option value="in_progress">In Progress</option>
                          <option value="completed">Completed</option>
                          <option value="not_applicable">Not Applicable</option>
                        </select>
                        <div style={{ flex: 1 }}>
                          <div
                            style={{
                              display: 'flex',
                              gap: '0.75rem',
                              alignItems: 'center',
                              marginBottom: '0.25rem',
                            }}
                          >
                            <h4
                              style={{
                                margin: 0,
                                fontSize: '0.9375rem',
                                fontWeight: 600,
                              }}
                            >
                              {item.itemTitle}
                            </h4>
                            {item.priority === 'critical' && (
                              <span
                                style={{
                                  padding: '0.125rem 0.5rem',
                                  background: '#fee2e2',
                                  color: '#991b1b',
                                  fontSize: '0.75rem',
                                  fontWeight: 600,
                                  borderRadius: '6px',
                                }}
                              >
                                CRITICAL
                              </span>
                            )}
                            {item.priority === 'high' && (
                              <span
                                style={{
                                  padding: '0.125rem 0.5rem',
                                  background: '#fef3c7',
                                  color: '#92400e',
                                  fontSize: '0.75rem',
                                  fontWeight: 600,
                                  borderRadius: '6px',
                                }}
                              >
                                HIGH
                              </span>
                            )}
                          </div>
                          {item.itemDescription && (
                            <p
                              style={{
                                margin: '0.5rem 0 0',
                                fontSize: '0.875rem',
                                color: '#6e6e73',
                                lineHeight: 1.5,
                              }}
                            >
                              {item.itemDescription}
                            </p>
                          )}
                          {item.requiresProfessional && item.professionalType && (
                            <p
                              style={{
                                margin: '0.5rem 0 0',
                                fontSize: '0.8125rem',
                                color: '#0071e3',
                              }}
                            >
                              Requires: {item.professionalType}
                            </p>
                          )}
                          {item.dueDate && (
                            <p
                              style={{
                                margin: '0.25rem 0 0',
                                fontSize: '0.8125rem',
                                color: '#6e6e73',
                              }}
                            >
                              Due: {new Date(item.dueDate).toLocaleDateString()}
                            </p>
                          )}
                        </div>
                      </div>
                    ))}
                  </div>
                )}
              </div>
            ))}
          </>
        )}
      </section>

      <section
        style={{
          background: 'white',
          border: '1px solid #d2d2d7',
          borderRadius: '18px',
          padding: '2rem',
          marginBottom: '2rem',
        }}
      >
        <h2
          style={{
            fontSize: '1.5rem',
            fontWeight: 600,
            marginBottom: '1rem',
            letterSpacing: '-0.01em',
          }}
        >
          Multi-Scenario Comparison
        </h2>
        {!capturedProperty ? (
          <div
            style={{
              padding: '3rem 2rem',
              textAlign: 'center',
              color: '#6e6e73',
              background: '#f5f5f7',
              borderRadius: '12px',
            }}
          >
            <div style={{ fontSize: '3rem', marginBottom: '1rem' }}>📊</div>
            <p style={{ margin: 0, fontSize: '1.0625rem' }}>
              Capture a property to review scenario economics and development posture
            </p>
            <p style={{ margin: '0.5rem 0 0', fontSize: '0.9375rem' }}>
              Financial and planning metrics for each developer scenario appear here.
            </p>
          </div>
        ) : quickAnalysisScenarios.length === 0 ? (
          <div
            style={{
              padding: '2.5rem',
              textAlign: 'center',
              color: '#6e6e73',
              background: '#f5f5f7',
              borderRadius: '12px',
            }}
          >
            <p style={{ margin: 0 }}>
              Quick analysis metrics unavailable for this capture. Try regenerating the
              scenarios.
            </p>
          </div>
        ) : (
          <div style={{ display: 'flex', flexDirection: 'column', gap: '1.5rem' }}>
            <div
              style={{
                display: 'grid',
                gap: '1rem',
                gridTemplateColumns: 'repeat(auto-fit, minmax(280px, 1fr))',
              }}
            >
              {scenarioComparisonData.map((row) => {
                const isActive =
                  row.key === 'all'
                    ? activeScenario === 'all'
                    : activeScenario === row.key
                const progressLabel =
                  row.checklistCompleted !== null && row.checklistTotal !== null
                    ? `${row.checklistCompleted}/${row.checklistTotal}`
                    : null
                const progressPercent = row.checklistPercent ?? null
                const focusable = row.key !== 'all'
                const primaryVisuals = row.primaryInsight
                  ? getSeverityVisuals(row.primaryInsight.severity)
                  : null

                return (
                  <article
                    key={row.key}
                    style={{
                      border: `2px solid ${isActive ? '#1d1d1f' : '#e5e5e7'}`,
                      borderRadius: '14px',
                      padding: '1.35rem',
                      background: isActive ? '#ffffff' : '#f5f5f7',
                      display: 'flex',
                      flexDirection: 'column',
                      gap: '1rem',
                      transition: 'border 0.2s ease, background 0.2s ease',
                    }}
                  >
                    <div
                      style={{
                        display: 'flex',
                        justifyContent: 'space-between',
                        alignItems: 'flex-start',
                        gap: '0.75rem',
                        flexWrap: 'wrap',
                      }}
                    >
                      <div
                        style={{
                          display: 'flex',
                          alignItems: 'center',
                          gap: '0.65rem',
                        }}
                      >
                        <span style={{ fontSize: '1.5rem' }}>{row.icon}</span>
                        <div style={{ display: 'flex', flexDirection: 'column', gap: '0.2rem' }}>
                          <span
                            style={{
                              fontSize: '0.75rem',
                              fontWeight: 600,
                              letterSpacing: '0.08em',
                              textTransform: 'uppercase',
                              color: '#6b7280',
                            }}
                          >
                            {row.key === 'all' ? 'Aggregate' : 'Scenario'}
                          </span>
                          <span
                            style={{
                              fontSize: '1.125rem',
                              fontWeight: 600,
                              letterSpacing: '-0.01em',
                            }}
                          >
                            {row.label}
                          </span>
                        </div>
                      </div>
                      {focusable ? (
                        isActive ? (
                          <span
                            style={{
                              borderRadius: '9999px',
                              background: '#1d4ed8',
                              color: '#ffffff',
                              padding: '0.25rem 0.75rem',
                              fontSize: '0.75rem',
                              fontWeight: 600,
                              letterSpacing: '0.08em',
                              textTransform: 'uppercase',
                            }}
                          >
                            Focus
                          </span>
                        ) : (
                          <button
                            type="button"
                            onClick={() => setActiveScenario(row.key)}
                            style={{
                              border: '1px solid #1d1d1f',
                              background: 'white',
                              color: '#1d1d1f',
                              borderRadius: '9999px',
                              padding: '0.3rem 0.85rem',
                              fontSize: '0.78rem',
                              fontWeight: 600,
                              cursor: 'pointer',
                            }}
                          >
                            Focus scenario
                          </button>
                        )
                      ) : (
                        <span
                          style={{
                            borderRadius: '9999px',
                            background: '#e5e7eb',
                            color: '#374151',
                            padding: '0.25rem 0.75rem',
                            fontSize: '0.75rem',
                            fontWeight: 600,
                            letterSpacing: '0.08em',
                            textTransform: 'uppercase',
                          }}
                        >
                          Summary
                        </span>
                      )}
                    </div>

                    <div
                      style={{
                        display: 'flex',
                        flexWrap: 'wrap',
                        alignItems: 'center',
                        gap: '0.6rem',
                        fontSize: '0.78rem',
                        color: '#64748b',
                      }}
                    >
                      <span>
                        Inspector:{' '}
                        <strong>{row.inspectorName?.trim() || 'Not recorded'}</strong>
                      </span>
                      {row.recordedAt && (
                        <span>Logged {formatRecordedTimestamp(row.recordedAt)}</span>
                      )}
                      <span
                        style={{
                          display: 'inline-flex',
                          alignItems: 'center',
                          gap: '0.3rem',
                          borderRadius: '9999px',
                          padding: '0.15rem 0.6rem',
                          fontWeight: 600,
                          letterSpacing: '0.05em',
                          textTransform: 'uppercase',
                          background:
                            row.source === 'manual' ? '#dcfce7' : 'rgba(37, 99, 235, 0.12)',
                          color: row.source === 'manual' ? '#166534' : '#1d4ed8',
                        }}
                      >
                        {row.source === 'manual' ? 'Manual inspection' : 'Automated baseline'}
                      </span>
                    </div>

                    {row.quickHeadline && (
                      <p
                        style={{
                          margin: 0,
                          fontSize: '0.92rem',
                          color: '#374151',
                          lineHeight: 1.45,
                        }}
                      >
                        {row.quickHeadline}
                      </p>
                    )}

                    {row.quickMetrics.length > 0 && (
                      <ul
                        style={{
                          margin: 0,
                          padding: 0,
                          listStyle: 'none',
                          display: 'grid',
                          gap: '0.45rem',
                          gridTemplateColumns: 'repeat(auto-fit, minmax(120px, 1fr))',
                        }}
                      >
                        {row.quickMetrics.map((metric) => (
                          <li
                            key={`${row.key}-${metric.label}`}
                            style={{ display: 'flex', flexDirection: 'column', gap: '0.15rem' }}
                          >
                            <span
                              style={{
                                fontSize: '0.75rem',
                                color: '#6b7280',
                                letterSpacing: '0.06em',
                                textTransform: 'uppercase',
                              }}
                            >
                              {metric.label}
                            </span>
                            <strong style={{ fontSize: '0.95rem', color: '#111827' }}>
                              {metric.value}
                            </strong>
                          </li>
                        ))}
                      </ul>
                    )}

                    <div
                      style={{
                        display: 'grid',
                        gap: '0.75rem',
                        gridTemplateColumns: 'repeat(auto-fit, minmax(160px, 1fr))',
                      }}
                    >
                      <div style={{ display: 'flex', flexDirection: 'column', gap: '0.25rem' }}>
                        <span
                          style={{
                            fontSize: '0.75rem',
                            letterSpacing: '0.06em',
                            textTransform: 'uppercase',
                            color: '#9ca3af',
                          }}
                        >
                          Condition
                        </span>
                        <span style={{ fontSize: '1rem', fontWeight: 600, color: '#111827' }}>
                          {row.conditionRating ? row.conditionRating : '—'}
                        </span>
                        <span style={{ fontSize: '0.85rem', color: '#475569' }}>
                          {row.conditionScore !== null
                            ? `${row.conditionScore}/100`
                            : '—'}{' '}
                          {row.riskLevel ? `· ${row.riskLevel} risk` : ''}
                        </span>
                      </div>
                      <div style={{ display: 'flex', flexDirection: 'column', gap: '0.25rem' }}>
                        <span
                          style={{
                            fontSize: '0.75rem',
                            letterSpacing: '0.06em',
                            textTransform: 'uppercase',
                            color: '#9ca3af',
                          }}
                        >
                          Checklist progress
                        </span>
                        {progressLabel ? (
                          <>
                            <div
                              style={{
                                height: '6px',
                                borderRadius: '9999px',
                                background: '#e5e7eb',
                                overflow: 'hidden',
                              }}
                            >
                              <div
                                style={{
                                  width: `${progressPercent ?? 0}%`,
                                  height: '100%',
                                  background: '#1d4ed8',
                                  transition: 'width 0.3s ease',
                                }}
                              />
                            </div>
                            <span style={{ fontSize: '0.85rem', color: '#334155' }}>
                              {progressLabel}
                              {progressPercent !== null ? ` (${progressPercent}%)` : ''}
                            </span>
                          </>
                        ) : (
                          <span style={{ fontSize: '0.85rem', color: '#64748b' }}>
                            No checklist items yet.
                          </span>
                        )}
                      </div>
                    </div>

                    {row.primaryInsight && primaryVisuals && (
                      <div
                        style={{
                          border: `1px solid ${primaryVisuals.border}`,
                          background: primaryVisuals.background,
                          color: primaryVisuals.text,
                          borderRadius: '12px',
                          padding: '1rem',
                          display: 'flex',
                          flexDirection: 'column',
                          gap: '0.5rem',
                        }}
                      >
                        <span
                          style={{
                            display: 'inline-flex',
                            alignItems: 'center',
                            gap: '0.4rem',
                            fontSize: '0.75rem',
                            fontWeight: 600,
                            letterSpacing: '0.08em',
                            textTransform: 'uppercase',
                          }}
                        >
                          <span
                            style={{
                              width: '0.35rem',
                              height: '0.35rem',
                              borderRadius: '9999px',
                              background: primaryVisuals.indicator,
                            }}
                          />
                          {primaryVisuals.label}
                        </span>
                        <strong style={{ fontSize: '0.95rem' }}>{row.primaryInsight.title}</strong>
                        <p style={{ margin: 0, fontSize: '0.85rem', lineHeight: 1.45 }}>
                          {row.primaryInsight.detail}
                        </p>
                        {row.primaryInsight.specialist && (
                          <span style={{ fontSize: '0.78rem', opacity: 0.85 }}>
                            Specialist: <strong>{row.primaryInsight.specialist}</strong>
                          </span>
                        )}
                      </div>
                    )}

                    {row.recommendedAction && (
                      <p
                        style={{
                          margin: 0,
                          fontSize: '0.85rem',
                          color: '#334155',
                        }}
                      >
                        <strong>Next action:</strong> {row.recommendedAction}
                      </p>
                    )}
                  </article>
                )
              })}
            </div>


            {feasibilitySignals.length > 0 && (
              <div
                style={{
                  border: '1px solid #d2d2d7',
                  borderRadius: '12px',
                  padding: '1.5rem',
                  background: '#f8fafc',
                  display: 'flex',
                  flexDirection: 'column',
                  gap: '1.25rem',
                }}
              >
                <div
                  style={{
                    display: 'flex',
                    flexWrap: 'wrap',
                    justifyContent: 'space-between',
                    gap: '0.75rem',
                    alignItems: 'center',
                  }}
                >
                  <h3
                    style={{
                      fontSize: '1.125rem',
                      fontWeight: 600,
                      margin: 0,
                      letterSpacing: '-0.01em',
                    }}
                  >
                    Feasibility Signals
                  </h3>
                  {propertyId && (
                    <Link
                      to={`/app/asset-feasibility?propertyId=${encodeURIComponent(propertyId)}`}
                      style={{
                        display: 'inline-flex',
                        alignItems: 'center',
                        gap: '0.35rem',
                        padding: '0.45rem 0.9rem',
                        borderRadius: '9999px',
                        border: '1px solid #0f172a',
                        background: '#0f172a',
                        color: 'white',
                        fontSize: '0.85rem',
                        fontWeight: 600,
                        textDecoration: 'none',
                      }}
                    >
                      Open Feasibility Workspace →
                    </Link>
                  )}
                </div>
                <p
                  style={{
                    margin: 0,
                    fontSize: '0.9rem',
                    color: '#334155',
                  }}
                >
                  Highlights derived from quick analysis. Prioritise these before handing
                  off to the feasibility team.
                </p>
                {capturedProperty && (
                  <div
                    style={{
                      display: 'flex',
                      flexWrap: 'wrap',
                      alignItems: 'center',
                      gap: '0.6rem',
                    }}
                  >
                    <button
                      type="button"
                      onClick={() => handleReportExport('json')}
                      disabled={isExportingReport}
                      style={{
                        border: '1px solid #0f172a',
                        background: '#0f172a',
                        color: '#fff',
                        borderRadius: '9999px',
                        padding: '0.45rem 0.95rem',
                        fontSize: '0.8rem',
                        fontWeight: 600,
                        cursor: isExportingReport ? 'not-allowed' : 'pointer',
                        transition: 'background 0.2s ease, color 0.2s ease',
                      }}
                    >
                      {isExportingReport ? 'Preparing JSON…' : 'Download JSON'}
                    </button>
                    <button
                      type="button"
                      onClick={() => handleReportExport('pdf')}
                      disabled={isExportingReport}
                      style={{
                        border: '1px solid #0f172a',
                        background: 'transparent',
                        color: '#0f172a',
                        borderRadius: '9999px',
                        padding: '0.45rem 0.95rem',
                        fontSize: '0.8rem',
                        fontWeight: 600,
                        cursor: isExportingReport ? 'not-allowed' : 'pointer',
                        transition: 'background 0.2s ease, color 0.2s ease',
                      }}
                    >
                      {isExportingReport ? 'Preparing PDF…' : 'Download PDF'}
                    </button>
                    {reportExportMessage && (
                      <span
                        style={{
                          fontSize: '0.78rem',
                          fontWeight: 500,
                          color: reportExportMessage
                            .toLowerCase()
                            .includes('unable')
                            ? '#c53030'
                            : '#15803d',
                        }}
                      >
                        {reportExportMessage}
                      </span>
                    )}
                  </div>
                )}
                <div
                  style={{
                    display: 'grid',
                    gap: '1rem',
                    gridTemplateColumns: 'repeat(auto-fit, minmax(240px, 1fr))',
                  }}
                >
                  {feasibilitySignals.map((entry) => (
                    <div
                      key={entry.scenario}
                      style={{
                        background: 'white',
                        borderRadius: '10px',
                        border: '1px solid #e2e8f0',
                        padding: '1.1rem',
                        display: 'flex',
                        flexDirection: 'column',
                        gap: '0.6rem',
                      }}
                    >
                      <div
                        style={{
                          display: 'flex',
                          alignItems: 'center',
                          gap: '0.5rem',
                          justifyContent: 'space-between',
                        }}
                      >
                        <strong style={{ fontSize: '0.95rem', color: '#0f172a' }}>
                          {entry.label}
                        </strong>
                      </div>
                      {entry.opportunities.length > 0 && (
                        <div style={{ display: 'grid', gap: '0.35rem' }}>
                          <span
                            style={{
                              fontSize: '0.75rem',
                              fontWeight: 700,
                              color: '#047857',
                              textTransform: 'uppercase',
                              letterSpacing: '0.08em',
                            }}
                          >
                            Opportunities
                          </span>
                          <ul
                            style={{
                              margin: 0,
                              paddingLeft: '1.1rem',
                              fontSize: '0.85rem',
                              color: '#065f46',
                              lineHeight: 1.4,
                            }}
                          >
                            {entry.opportunities.map((message) => (
                              <li key={message}>{message}</li>
                            ))}
                          </ul>
                        </div>
                      )}
                      {entry.risks.length > 0 && (
                        <div style={{ display: 'grid', gap: '0.35rem' }}>
                          <span
                            style={{
                              fontSize: '0.75rem',
                              fontWeight: 700,
                              color: '#b91c1c',
                              textTransform: 'uppercase',
                              letterSpacing: '0.08em',
                            }}
                          >
                            Risks & Follow-ups
                          </span>
                          <ul
                            style={{
                              margin: 0,
                              paddingLeft: '1.1rem',
                              fontSize: '0.85rem',
                              color: '#7f1d1d',
                              lineHeight: 1.4,
                            }}
                          >
                            {entry.risks.map((message) => (
                              <li key={message}>{message}</li>
                            ))}
                          </ul>
                        </div>
                      )}
                      {entry.opportunities.length === 0 && entry.risks.length === 0 && (
                        <p
                          style={{
                            margin: 0,
                            fontSize: '0.85rem',
                            color: '#475569',
                          }}
                        >
                          No automated guidance produced. Review the scenario notes for
                          additional context.
                        </p>
                      )}
                    </div>
                  ))}
                </div>
              </div>
            )}

            {activeScenario !== 'all' && comparisonScenarios.length > 0 && (
              <div
                style={{
                  padding: '1.25rem',
                  background: '#f0f9ff',
                  borderRadius: '12px',
                  border: '1px solid #bae6fd',
                }}
              >
                <strong>Scenario focus:</strong> Viewing{' '}
                {scenarioLookup.get(activeScenario)?.label ??
                  formatCategoryName(activeScenario)}{' '}
                metrics. Switch back to “All scenarios” to compare options side-by-side.
              </div>
            )}
          </div>
        )}
      </section>

      <section
        style={{
          background: 'white',
          border: '1px solid #d2d2d7',
          borderRadius: '18px',
          padding: '2rem',
        }}
      >
        <h2
          style={{
            fontSize: '1.5rem',
            fontWeight: 600,
            marginBottom: '1rem',
            letterSpacing: '-0.01em',
          }}
        >
          Property Condition Assessment
        </h2>
        {isLoadingCondition ? (
          <div
            style={{
              padding: '2.5rem',
              textAlign: 'center',
              color: '#6e6e73',
              background: '#f5f5f7',
              borderRadius: '12px',
            }}
          >
            <p style={{ margin: 0 }}>Analysing building condition...</p>
          </div>
        ) : !capturedProperty ? (
          <div
            style={{
              padding: '3rem 2rem',
              textAlign: 'center',
              color: '#6e6e73',
              background: '#f5f5f7',
              borderRadius: '12px',
            }}
          >
            <div style={{ fontSize: '3rem', marginBottom: '1rem' }}>🏢</div>
            <p style={{ margin: 0, fontSize: '1.0625rem' }}>
              Capture a property to generate the developer condition assessment
            </p>
            <p style={{ margin: '0.5rem 0 0', fontSize: '0.9375rem' }}>
              Structural, M&amp;E, and compliance insights will appear here with targeted actions.
            </p>
          </div>
        ) : !conditionAssessment ? (
          <div
            style={{
              padding: '2.5rem 2rem',
              textAlign: 'center',
              color: '#6e6e73',
              background: capturedProperty?.propertyId === 'offline-property' ? '#f5f5f7' : '#fff7ed',
              borderRadius: '12px',
              border: capturedProperty?.propertyId === 'offline-property' ? 'none' : '1px solid #fed7aa',
            }}
          >
            <p style={{ margin: 0 }}>
              {capturedProperty?.propertyId === 'offline-property'
                ? 'Condition assessment not available in offline mode. Capture a real property to access inspection data.'
                : 'Unable to load condition assessment. Please retry after refreshing the capture.'}
            </p>
          </div>
        ) : (
          <div
            style={{
              display: 'flex',
              flexDirection: 'column',
              gap: '1.75rem',
            }}
          >
            <div
              style={{
                display: 'flex',
                flexWrap: 'wrap',
                gap: '1.5rem',
                alignItems: 'flex-start',
              }}
            >
              <div
                style={{
                  flex: '1 1 260px',
                  background: '#f5f5f7',
                  borderRadius: '12px',
                  padding: '1.5rem',
                  display: 'flex',
                  flexDirection: 'column',
                  gap: '0.5rem',
                }}
              >
                <span
                  style={{
                    fontSize: '0.875rem',
                    fontWeight: 600,
                    color: '#6e6e73',
                    letterSpacing: '0.08em',
                    textTransform: 'uppercase',
                  }}
                >
                  Overall Rating
                </span>
                <div
                  style={{
                    display: 'flex',
                    alignItems: 'baseline',
                    gap: '0.75rem',
                  }}
                >
                  <span style={{ fontSize: '2.5rem', fontWeight: 700 }}>
                    {conditionAssessment.overallRating}
                  </span>
                  <span style={{ fontSize: '1rem', color: '#6e6e73' }}>
                    {conditionAssessment.overallScore}/100 · {conditionAssessment.riskLevel} risk
                  </span>
                </div>
                <p
                  style={{
                    margin: 0,
                    fontSize: '0.9375rem',
                    color: '#3a3a3c',
                    lineHeight: 1.5,
                  }}
                >
                  {conditionAssessment.summary}
                </p>
                {conditionAssessment.scenarioContext && (
                  <p
                    style={{
                      margin: 0,
                      fontSize: '0.875rem',
                      color: '#0071e3',
                    }}
                  >
                    {conditionAssessment.scenarioContext}
                  </p>
                )}
                <div
                  style={{
                    display: 'flex',
                    flexWrap: 'wrap',
                    gap: '0.75rem',
                    fontSize: '0.8125rem',
                    color: '#6e6e73',
                  }}
                >
                  <span>
                    Inspector:{' '}
                    <strong>{conditionAssessment.inspectorName?.trim() || 'Not recorded'}</strong>
                  </span>
                  {conditionAssessment.recordedAt && (
                    <span>Logged {formatRecordedTimestamp(conditionAssessment.recordedAt)}</span>
                  )}
                </div>
                {conditionAssessment.attachments.length > 0 && (
                  <div>
                    <span
                      style={{
                        display: 'inline-block',
                        marginTop: '0.5rem',
                        fontSize: '0.75rem',
                        fontWeight: 600,
                        textTransform: 'uppercase',
                        color: '#6e6e73',
                        letterSpacing: '0.06em',
                      }}
                    >
                      Attachments
                    </span>
                    <ul style={{ margin: '0.35rem 0 0', paddingLeft: '1.2rem' }}>
                      {conditionAssessment.attachments.map((attachment, index) => (
                        <li key={`current-attachment-${index}`} style={{ fontSize: '0.85rem' }}>
                          {attachment.url ? (
                            <a
                              href={attachment.url}
                              target="_blank"
                              rel="noreferrer"
                              style={{ color: '#0a84ff' }}
                            >
                              {attachment.label}
                            </a>
                          ) : (
                            attachment.label
                          )}
                        </li>
                      ))}
                    </ul>
                  </div>
                )}
              </div>
              <div
                style={{
                  flex: '1 1 280px',
                  background: '#f5f5f7',
                  borderRadius: '12px',
                  padding: '1.5rem',
                }}
              >
                <h3
                  style={{
                    margin: '0 0 0.75rem',
                    fontSize: '1.0625rem',
                    fontWeight: 600,
                  }}
                >
                  Immediate Actions
                </h3>
                <ul
                  style={{
                    margin: 0,
                    paddingLeft: '1.2rem',
                    color: '#3a3a3c',
                    fontSize: '0.9375rem',
                    lineHeight: 1.5,
                  }}
                >
                  {conditionAssessment.recommendedActions.map((action) => (
                    <li key={action}>{action}</li>
                  ))}
                </ul>
              </div>
            </div>

            {combinedConditionInsights.length > 0 && (
              <div
                style={{
                  border: '1px solid #e5e5e7',
                  borderRadius: '12px',
                  padding: '1.5rem',
                  background: '#f8fafc',
                  display: 'flex',
                  flexDirection: 'column',
                  gap: '1rem',
                }}
              >
                <div
                  style={{
                    display: 'flex',
                    justifyContent: 'space-between',
                    alignItems: 'center',
                    flexWrap: 'wrap',
                    gap: '0.75rem',
                  }}
                >
                  <h3
                    style={{
                      margin: 0,
                      fontSize: '1.125rem',
                      fontWeight: 600,
                      letterSpacing: '-0.01em',
                    }}
                  >
                    Condition insights
                  </h3>
                  <span style={{ fontSize: '0.85rem', color: '#475569' }}>
                    {insightSubtitle}
                  </span>
                </div>
                <div
                  style={{
                    display: 'grid',
                    gap: '1rem',
                    gridTemplateColumns: 'repeat(auto-fit, minmax(240px, 1fr))',
                  }}
                >
                  {combinedConditionInsights.map((insight) => {
                    const visuals = getSeverityVisuals(insight.severity)
                    const isChecklistInsight = insight.id.startsWith('checklist-')
                    const chipStyle: CSSProperties = {
                      display: 'inline-flex',
                      alignItems: 'center',
                      gap: '0.35rem',
                      padding: '0.3rem 0.6rem',
                      borderRadius: '9999px',
                      fontSize: '0.75rem',
                      fontWeight: 600,
                      background: 'rgba(15, 23, 42, 0.08)',
                      color: '#0f172a',
                      border: '1px solid rgba(15, 23, 42, 0.12)',
                    }
                    return (
                      <div
                        key={insight.id}
                        style={{
                          border: `1px solid ${visuals.border}`,
                          background: visuals.background,
                          color: visuals.text,
                          borderRadius: '12px',
                          padding: '1.2rem',
                          display: 'flex',
                          flexDirection: 'column',
                          gap: '0.65rem',
                        }}
                      >
                        <span
                          style={{
                            display: 'inline-flex',
                            alignItems: 'center',
                            gap: '0.4rem',
                            fontSize: '0.75rem',
                            fontWeight: 700,
                            textTransform: 'uppercase',
                            letterSpacing: '0.08em',
                          }}
                        >
                          <span
                            style={{
                              width: '0.35rem',
                              height: '0.35rem',
                              borderRadius: '9999px',
                              background: visuals.indicator,
                            }}
                          />
                          {visuals.label}
                        </span>
                        <strong style={{ fontSize: '0.95rem', lineHeight: 1.4 }}>
                          {insight.title}
                        </strong>
                        <p
                          style={{
                            margin: 0,
                            fontSize: '0.85rem',
                            lineHeight: 1.4,
                          }}
                        >
                          {insight.detail}
                        </p>
                        {(insight.specialist || isChecklistInsight) && (
                          <div
                            style={{
                              display: 'flex',
                              flexWrap: 'wrap',
                              gap: '0.5rem',
                            }}
                          >
                            {isChecklistInsight && (
                              <span
                                style={{
                                  ...chipStyle,
                                  background: 'rgba(29, 78, 216, 0.08)',
                                  color: '#1d4ed8',
                                  border: '1px solid rgba(29, 78, 216, 0.15)',
                                }}
                              >
                                Checklist follow-up
                              </span>
                            )}
                            {insight.specialist && (
                              <span style={chipStyle}>
                                Specialist · <strong>{insight.specialist}</strong>
                              </span>
                            )}
                          </div>
                        )}
                      </div>
                    )
                  })}
                </div>
              </div>
            )}

            <div
              style={{
                display: 'grid',
                gap: '1rem',
                gridTemplateColumns: 'repeat(auto-fit, minmax(260px, 1fr))',
              }}
            >
              {conditionAssessment.systems.map((system) => {
                const comparison = systemComparisonMap.get(system.name)
                const delta =
                  comparison && typeof comparison.scoreDelta === 'number'
                    ? comparison.scoreDelta
                    : null
                const previousRating = comparison?.previous?.rating ?? null
                const previousScore =
                  typeof comparison?.previous?.score === 'number'
                    ? comparison?.previous?.score
                    : null
                const systemSeverity = classifySystemSeverity(system.rating, delta)
                const badgeVisuals = getSeverityVisuals(systemSeverity)
                const deltaVisuals = getDeltaVisuals(delta)

                return (
                  <div
                    key={system.name}
                    style={{
                      border: '1px solid #e5e5e7',
                      borderRadius: '12px',
                      padding: '1.25rem',
                      display: 'flex',
                      flexDirection: 'column',
                      gap: '0.75rem',
                    }}
                  >
                    <div
                      style={{
                        display: 'flex',
                        justifyContent: 'space-between',
                        alignItems: 'flex-start',
                        flexWrap: 'wrap',
                        gap: '0.6rem',
                      }}
                    >
                      <div
                        style={{
                          display: 'flex',
                          flexDirection: 'column',
                          gap: '0.35rem',
                        }}
                      >
                        <h3
                          style={{
                            margin: 0,
                            fontSize: '1.0625rem',
                            fontWeight: 600,
                          }}
                        >
                          {system.name}
                        </h3>
                        {previousRating && previousScore !== null && (
                          <span style={{ fontSize: '0.8rem', color: '#6e6e73' }}>
                            Previous {previousRating} · {previousScore}/100
                          </span>
                        )}
                      </div>
                      <div
                        style={{
                          display: 'flex',
                          alignItems: 'center',
                          flexWrap: 'wrap',
                          gap: '0.45rem',
                        }}
                      >
                        <span
                          style={{
                            display: 'inline-flex',
                            alignItems: 'center',
                            gap: '0.35rem',
                            padding: '0.3rem 0.65rem',
                            borderRadius: '9999px',
                            fontSize: '0.75rem',
                            fontWeight: 700,
                            textTransform: 'uppercase',
                            letterSpacing: '0.05em',
                            border: `1px solid ${badgeVisuals.border}`,
                            background: badgeVisuals.background,
                            color: badgeVisuals.text,
                          }}
                        >
                          <span
                            style={{
                              width: '0.35rem',
                              height: '0.35rem',
                              borderRadius: '9999px',
                              background: badgeVisuals.indicator,
                            }}
                          />
                          {system.rating} · {system.score}/100
                        </span>
                        {delta !== null && (
                          <span
                            style={{
                              display: 'inline-flex',
                              alignItems: 'center',
                              gap: '0.25rem',
                              padding: '0.25rem 0.55rem',
                              borderRadius: '9999px',
                              fontSize: '0.75rem',
                              fontWeight: 600,
                              background: deltaVisuals.background,
                              color: deltaVisuals.text,
                              border: `1px solid ${deltaVisuals.border}`,
                            }}
                          >
                            {delta > 0 ? '▲' : delta < 0 ? '▼' : '■'}{' '}
                            {formatDeltaValue(delta)}
                          </span>
                        )}
                      </div>
                    </div>
                    <p
                      style={{
                        margin: 0,
                        fontSize: '0.9rem',
                        color: '#3a3a3c',
                        lineHeight: 1.5,
                      }}
                    >
                      {system.notes}
                    </p>
                    <ul
                      style={{
                        margin: 0,
                        paddingLeft: '1.1rem',
                        fontSize: '0.875rem',
                        color: '#3a3a3c',
                        lineHeight: 1.4,
                      }}
                    >
                      {system.recommendedActions.map((action) => (
                        <li key={action}>{action}</li>
                      ))}
                    </ul>
                  </div>
                )
              })}
            </div>

            <div
              style={{
                border: '1px solid #e5e5e7',
                borderRadius: '12px',
                padding: '1.5rem',
                display: 'flex',
                flexDirection: 'column',
                gap: '1rem',
              }}
            >
              <div
                style={{
                  display: 'flex',
                  justifyContent: 'space-between',
                  alignItems: 'center',
                  flexWrap: 'wrap',
                  gap: '0.75rem',
                }}
              >
                <div
                  style={{ maxWidth: '520px', display: 'flex', flexDirection: 'column', gap: '0.35rem' }}
                >
                  <h3
                    style={{
                      margin: 0,
                      fontSize: '1.0625rem',
                      fontWeight: 600,
                    }}
                  >
                    Manual inspection capture
                  </h3>
                  <p style={{ margin: 0, fontSize: '0.9rem', color: '#4b5563', lineHeight: 1.5 }}>
                    Log a fresh site visit or update the latest inspection without waiting for automated sync.
                  </p>
                </div>
                <div style={{ display: 'flex', gap: '0.75rem', flexWrap: 'wrap' }}>
                  <button
                    type="button"
                    onClick={() => openAssessmentEditor('new')}
                    disabled={!capturedProperty}
                    style={{
                      border: '1px solid #1d1d1f',
                      background: capturedProperty ? '#1d1d1f' : '#f5f5f7',
                      color: capturedProperty ? 'white' : '#1d1d1f88',
                      borderRadius: '9999px',
                      padding: '0.45rem 1.1rem',
                      fontSize: '0.8125rem',
                      fontWeight: 600,
                      cursor: capturedProperty ? 'pointer' : 'not-allowed',
                    }}
                  >
                    Log inspection
                  </button>
                  {conditionAssessment && (
                    <button
                      type="button"
                      onClick={() => openAssessmentEditor('edit')}
                      disabled={!capturedProperty}
                      style={{
                        border: '1px solid #1d1d1f',
                        background: 'white',
                        color: '#1d1d1f',
                        borderRadius: '9999px',
                        padding: '0.45rem 1.1rem',
                        fontSize: '0.8125rem',
                        fontWeight: 600,
                        cursor: capturedProperty ? 'pointer' : 'not-allowed',
                      }}
                    >
                      Edit latest
                    </button>
                  )}
                </div>
              </div>
              {assessmentSaveMessage && (
                <p
                  style={{
                    margin: 0,
                    fontSize: '0.85rem',
                    color: assessmentSaveMessage.includes('success')
                      ? '#15803d'
                      : '#c53030',
                  }}
                >
                  {assessmentSaveMessage}
                </p>
              )}
              {capturedProperty ? (
                <div
                  style={{
                    display: 'flex',
                    flexWrap: 'wrap',
                    gap: '0.6rem',
                    fontSize: '0.85rem',
                    color: '#4b5563',
                  }}
                >
                  {latestAssessmentEntry ? (
                    <>
                      <span>
                        Last recorded:{' '}
                        <strong>{formatRecordedTimestamp(latestAssessmentEntry.recordedAt)}</strong>
                      </span>
                      <span>•</span>
                      <span>
                        Scenario:{' '}
                        <strong>{formatScenarioLabel(latestAssessmentEntry.scenario)}</strong>
                      </span>
                      <span>•</span>
                      <span>
                        Rating:{' '}
                        <strong>
                          {latestAssessmentEntry.overallRating} · {latestAssessmentEntry.overallScore}/100
                        </strong>
                      </span>
                    </>
                  ) : (
                    <span>
                      No manual inspections logged yet - use "Log inspection" to create one.
                    </span>
                  )}
                </div>
              ) : (
                <p style={{ margin: 0, fontSize: '0.85rem', color: '#6b7280' }}>
                  Capture a property to enable manual inspection logging.
                </p>
              )}
            </div>

            <InlineInspectionHistorySummary />


            <div
              style={{
                border: '1px solid #e5e5e7',
                borderRadius: '12px',
                padding: '1.5rem',
                display: 'flex',
                flexDirection: 'column',
                gap: '1rem',
              }}
            >
              <div
                style={{
                  display: 'flex',
                  justifyContent: 'space-between',
                  alignItems: 'center',
                  flexWrap: 'wrap',
                  gap: '0.75rem',
                }}
              >
                <h3
                  style={{
                    margin: 0,
                    fontSize: '1.0625rem',
                    fontWeight: 600,
                  }}
                >
                  Scenario Overrides
                </h3>
                <div
                  style={{
                    display: 'flex',
                    flexWrap: 'wrap',
                    gap: '0.5rem',
                    alignItems: 'center',
                  }}
                >
                  <button
                    type="button"
                    onClick={() => handleReportExport('json')}
                    disabled={!capturedProperty || isExportingReport}
                    style={{
                      border: '1px solid #1d1d1f',
                      background: '#1d1d1f',
                      color: 'white',
                      borderRadius: '9999px',
                      padding: '0.4rem 0.9rem',
                      fontSize: '0.8125rem',
                      fontWeight: 600,
                      cursor: isExportingReport ? 'not-allowed' : 'pointer',
                    }}
                  >
                    {isExportingReport ? 'Preparing JSON…' : 'Download JSON'}
                  </button>
                  <button
                    type="button"
                    onClick={() => handleReportExport('pdf')}
                    disabled={!capturedProperty || isExportingReport}
                    style={{
                      border: '1px solid #1d1d1f',
                      background: 'white',
                      color: '#1d1d1f',
                      borderRadius: '9999px',
                      padding: '0.4rem 0.9rem',
                      fontSize: '0.8125rem',
                      fontWeight: 600,
                      cursor: isExportingReport ? 'not-allowed' : 'pointer',
                    }}
                  >
                    {isExportingReport ? 'Preparing PDF…' : 'Download PDF'}
                  </button>
                  {scenarioOverrideEntries.length > 1 && baseScenarioAssessment && (
                    <label
                      style={{
                        display: 'flex',
                        alignItems: 'center',
                        gap: '0.5rem',
                        fontSize: '0.85rem',
                        color: '#3a3a3c',
                      }}
                    >
                      <span style={{ fontWeight: 600 }}>Baseline scenario</span>
                      <select
                        value={baseScenarioAssessment.scenario}
                        onChange={(event) =>
                          setScenarioComparisonBase(event.target.value as DevelopmentScenario)
                        }
                        style={{
                          borderRadius: '8px',
                          border: '1px solid #d2d2d7',
                          padding: '0.4rem 0.6rem',
                          fontSize: '0.85rem',
                        }}
                      >
                        {scenarioOverrideEntries.map((entry) => (
                          <option key={entry.scenario} value={entry.scenario}>
                            {formatScenarioLabel(entry.scenario)}
                          </option>
                        ))}
                      </select>
                    </label>
                  )}
                </div>
              </div>
              {scenarioAssessmentsError ? (
                <p
                  style={{
                    margin: 0,
                    fontSize: '0.85rem',
                    color: '#c53030',
                  }}
                >
                  {scenarioAssessmentsError}
                </p>
              ) : isLoadingScenarioAssessments ? (
                <div
                  style={{
                    padding: '1.5rem',
                    textAlign: 'center',
                    color: '#6e6e73',
                    background: '#f5f5f7',
                    borderRadius: '10px',
                  }}
                >
                  <p style={{ margin: 0, fontSize: '0.9rem' }}>Loading scenario overrides...</p>
                </div>
              ) : scenarioOverrideEntries.length === 0 ? (
                <div
                  style={{
                    padding: '1.5rem',
                    textAlign: 'center',
                    color: '#6e6e73',
                    background: '#f5f5f7',
                    borderRadius: '10px',
                  }}
                >
                  <p style={{ margin: 0, fontSize: '0.9rem' }}>
                    No scenario-specific overrides recorded yet. Save an inspection for a
                    specific scenario to compare outcomes.
                  </p>
                </div>
              ) : (
                <div style={{ display: 'flex', flexDirection: 'column', gap: '1.25rem' }}>
                  {scenarioOverrideEntries.length > 0 && (
                    <div
                      style={{
                        display: 'flex',
                        flexWrap: 'wrap',
                        gap: '0.75rem',
                        alignItems: 'center',
                        justifyContent: 'space-between',
                        marginBottom: '1rem',
                      }}
                    >
                      <div
                        style={{
                          display: 'flex',
                          flexDirection: 'column',
                          gap: '0.25rem',
                        }}
                      >
                        <span
                          style={{
                            fontSize: '0.8rem',
                            fontWeight: 600,
                            letterSpacing: '0.06em',
                            textTransform: 'uppercase',
                            color: '#6e6e73',
                          }}
                        >
                          Compare against
                        </span>
                        <span style={{ fontSize: '0.95rem', color: '#1d1d1f' }}>
                          Choose the baseline inspection to benchmark other scenarios.
                        </span>
                      </div>
                      <label
                        style={{
                          display: 'inline-flex',
                          alignItems: 'center',
                          gap: '0.5rem',
                          fontSize: '0.9rem',
                          color: '#3a3a3c',
                        }}
                      >
                        <span style={{ fontWeight: 600 }}>Baseline scenario</span>
                        <select
                          value={baseScenarioAssessment?.scenario ?? ''}
                          onChange={(event) => {
                            const selected = event.target.value as DevelopmentScenario
                            if (selected) {
                              setScenarioComparisonBase(selected)
                            }
                          }}
                          style={{
                            borderRadius: '9999px',
                            border: '1px solid #d2d2d7',
                            padding: '0.4rem 0.9rem',
                            background: 'white',
                            fontSize: '0.9rem',
                            fontWeight: 600,
                            cursor: 'pointer',
                          }}
                        >
                          {scenarioOverrideEntries.map((assessment) => (
                            <option key={assessment.scenario} value={assessment.scenario}>
                              {formatScenarioLabel(assessment.scenario)}
                            </option>
                          ))}
                        </select>
                      </label>
                    </div>
                  )}

                  {baseScenarioAssessment && (
                    <div
                      style={{
                        border: '1px solid #d2d2d7',
                        borderRadius: '12px',
                        padding: '1.25rem',
                        background: '#f5f5f7',
                        display: 'flex',
                        flexDirection: 'column',
                        gap: '0.6rem',
                      }}
                    >
                      <span
                        style={{
                          fontSize: '0.75rem',
                          fontWeight: 600,
                          letterSpacing: '0.08em',
                          textTransform: 'uppercase',
                          color: '#6e6e73',
                        }}
                      >
                        Baseline scenario
                      </span>
                      <strong style={{ fontSize: '1rem', fontWeight: 600 }}>
                        {formatScenarioLabel(baseScenarioAssessment.scenario)}
                      </strong>
                      <div
                        style={{
                          display: 'flex',
                          flexWrap: 'wrap',
                          gap: '0.75rem',
                          alignItems: 'center',
                          color: '#3a3a3c',
                          fontSize: '0.9rem',
                        }}
                      >
                        <span>Rating {baseScenarioAssessment.overallRating}</span>
                        <span>{baseScenarioAssessment.overallScore}/100 score</span>
                        <span style={{ textTransform: 'capitalize' }}>
                          {baseScenarioAssessment.riskLevel} risk
                        </span>
                      </div>
                      <p
                        style={{
                          margin: 0,
                          fontSize: '0.9rem',
                          color: '#3a3a3c',
                          lineHeight: 1.5,
                        }}
                      >
                        {baseScenarioAssessment.summary}
                      </p>
                      {baseScenarioAssessment.scenarioContext && (
                        <p
                          style={{
                            margin: 0,
                            fontSize: '0.85rem',
                            color: '#0071e3',
                          }}
                        >
                          {baseScenarioAssessment.scenarioContext}
                        </p>
                      )}
                      {baseScenarioAssessment.recommendedActions.length > 0 && (
                        <div style={{ display: 'grid', gap: '0.4rem' }}>
                          <strong style={{ fontSize: '0.85rem' }}>Actions</strong>
                          <ul
                            style={{
                              margin: 0,
                              paddingLeft: '1.1rem',
                              fontSize: '0.85rem',
                              color: '#3a3a3c',
                              lineHeight: 1.4,
                            }}
                          >
                            {baseScenarioAssessment.recommendedActions.map((action) => (
                              <li key={action}>{action}</li>
                            ))}
                          </ul>
                        </div>
                      )}
                    </div>
                  )}
                  {scenarioComparisonEntries.length === 0 ? (
                    <div
                      style={{
                        padding: '1.25rem',
                        border: '1px solid #d2d2d7',
                        borderRadius: '12px',
                        background: '#ffffff',
                        color: '#6e6e73',
                        fontSize: '0.9rem',
                      }}
                    >
                      Capture another scenario-specific override to compare with the baseline.
                    </div>
                  ) : (
                    <div
                      style={{
                        display: 'grid',
                        gap: '1rem',
                        gridTemplateColumns: 'repeat(auto-fit, minmax(260px, 1fr))',
                      }}
                    >
                      {scenarioComparisonEntries.map((assessment) => {
                        if (!baseScenarioAssessment) {
                          return null
                        }
                        const scoreDelta = assessment.overallScore - baseScenarioAssessment.overallScore
                        const ratingInfo = describeRatingChange(
                          assessment.overallRating,
                          baseScenarioAssessment.overallRating,
                        )
                        const riskInfo = describeRiskChange(
                          assessment.riskLevel,
                          baseScenarioAssessment.riskLevel,
                        )
                        const toneColorMap: Record<'positive' | 'negative' | 'neutral', string> = {
                          positive: '#15803d',
                          negative: '#c53030',
                          neutral: '#6e6e73',
                        }

                        return (
                          <div
                            key={assessment.scenario}
                            style={{
                              border: '1px solid #e5e5e7',
                              borderRadius: '12px',
                              padding: '1.25rem',
                              display: 'flex',
                              flexDirection: 'column',
                              gap: '0.6rem',
                              background: '#ffffff',
                            }}
                          >
                            <strong style={{ fontSize: '1rem', fontWeight: 600 }}>
                              {formatScenarioLabel(assessment.scenario)}
                            </strong>
                            <div
                              style={{
                                display: 'flex',
                                flexDirection: 'column',
                                gap: '0.4rem',
                                fontSize: '0.9rem',
                                color: '#3a3a3c',
                              }}
                            >
                              <span>
                                Score {assessment.overallScore}/100{' '}
                                <span
                                  style={{
                                    color:
                                      scoreDelta > 0
                                        ? '#15803d'
                                        : scoreDelta < 0
                                        ? '#c53030'
                                        : '#6e6e73',
                                    fontWeight: 600,
                                  }}
                                >
                                  {scoreDelta === 0
                                    ? 'Δ 0'
                                    : `Δ ${scoreDelta > 0 ? '+' : ''}${scoreDelta}`}
                                </span>
                              </span>
                              <span
                                style={{
                                  color: toneColorMap[ratingInfo.tone],
                                  fontWeight: 600,
                                }}
                              >
                                {ratingInfo.text}
                              </span>
                              <span
                                style={{
                                  color: toneColorMap[riskInfo.tone],
                                  fontWeight: 600,
                                }}
                              >
                                {riskInfo.text}
                              </span>
                            </div>
                            <p
                              style={{
                                margin: 0,
                                fontSize: '0.9rem',
                                color: '#3a3a3c',
                                lineHeight: 1.5,
                              }}
                            >
                              {assessment.summary}
                            </p>
                            {assessment.scenarioContext && (
                              <p
                                style={{
                                  margin: 0,
                                  fontSize: '0.85rem',
                                  color: '#0071e3',
                                }}
                              >
                                {assessment.scenarioContext}
                              </p>
                            )}
                            {assessment.recommendedActions.length > 0 && (
                              <div style={{ display: 'grid', gap: '0.4rem' }}>
                                <strong style={{ fontSize: '0.85rem' }}>Actions</strong>
                                <ul
                                  style={{
                                    margin: 0,
                                    paddingLeft: '1.1rem',
                                    fontSize: '0.85rem',
                                    color: '#3a3a3c',
                                    lineHeight: 1.4,
                                  }}
                                >
                                  {assessment.recommendedActions.map((action) => (
                                    <li key={action}>{action}</li>
                                  ))}
                                </ul>
                              </div>
                            )}
                          </div>
                        )
                      })}
                    </div>
                  )}
                </div>
              )}
            </div>

          </div>
        )}
      </section>

      {isEditingAssessment &&
        createPortal(
          <div
            role="presentation"
            onClick={(event) => {
              if (event.target === event.currentTarget) {
                closeAssessmentEditor()
              }
            }}
            style={{
              position: 'fixed',
              inset: 0,
              background: 'rgba(0,0,0,0.45)',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              padding: '2rem',
              zIndex: 1000,
            }}
          >
            <div
              role="dialog"
              aria-modal="true"
              aria-label="Manual inspection editor"
              onClick={(event) => event.stopPropagation()}
              style={{
                background: 'white',
                borderRadius: '16px',
                maxWidth: '900px',
                width: '100%',
                maxHeight: '85vh',
                overflowY: 'auto',
                boxShadow: '0 20px 40px rgba(0,0,0,0.25)',
                padding: '2rem',
                position: 'relative',
              }}
            >
              <button
                type="button"
                onClick={closeAssessmentEditor}
                aria-label="Close inspection editor"
                style={{
                  position: 'absolute',
                  top: '1rem',
                  right: '1rem',
                  border: 'none',
                  background: 'transparent',
                  fontSize: '1.5rem',
                  cursor: 'pointer',
                  color: '#6e6e73',
                }}
              >
                ×
              </button>

              <div
                style={{
                  display: 'flex',
                  justifyContent: 'space-between',
                  alignItems: 'flex-start',
                  flexWrap: 'wrap',
                  gap: '1rem',
                  marginBottom: '1.5rem',
                }}
              >
                <div style={{ maxWidth: '540px', display: 'flex', flexDirection: 'column', gap: '0.35rem' }}>
                  <h2
                    style={{
                      margin: 0,
                      fontSize: '1.5rem',
                      fontWeight: 600,
                      letterSpacing: '-0.01em',
                    }}
                  >
                    {assessmentEditorMode === 'new' ? 'Log manual inspection' : 'Edit latest inspection'}
                  </h2>
                  <p style={{ margin: 0, fontSize: '0.95rem', color: '#4b5563', lineHeight: 1.6 }}>
                    {assessmentEditorMode === 'new'
                      ? 'Capture a manual inspection entry for the active scenario. All fields are required unless noted.'
                      : 'Update the most recent inspection. Saving will append a new entry to the inspection history.'}
                  </p>
                  {scenarioFocusOptions.length > 0 && (
                    <div
                      style={{
                        display: 'flex',
                        flexWrap: 'wrap',
                        gap: '0.55rem',
                      }}
                    >
                      {scenarioFocusOptions.map((option) => {
                        const isActive = activeScenario === option
                        const label =
                          option === 'all'
                            ? 'All scenarios'
                            : scenarioLookup.get(option)?.label ?? formatScenarioLabel(option)
                        return (
                          <button
                            key={`editor-filter-${option}`}
                            type="button"
                            onClick={() => setActiveScenario(option)}
                            style={{
                              borderRadius: '9999px',
                              border: `1px solid ${isActive ? '#1d4ed8' : '#d2d2d7'}`,
                              background: isActive ? '#dbeafe' : 'white',
                              color: isActive ? '#1d4ed8' : '#1d1d1f',
                              padding: '0.3rem 0.9rem',
                              fontSize: '0.78rem',
                              fontWeight: 600,
                              cursor: 'pointer',
                            }}
                          >
                            {label}
                          </button>
                        )
                      })}
                    </div>
                  )}
                </div>
                <button
                  type="button"
                  onClick={resetAssessmentDraft}
                  disabled={isSavingAssessment}
                  style={{
                    border: '1px solid #d2d2d7',
                    background: 'white',
                    color: '#1d1d1f',
                    borderRadius: '9999px',
                    padding: '0.45rem 1rem',
                    fontSize: '0.8125rem',
                    fontWeight: 600,
                    cursor: isSavingAssessment ? 'not-allowed' : 'pointer',
                  }}
                >
                  Reset draft
                </button>
              </div>

              <form onSubmit={handleAssessmentSubmit} style={{ display: 'grid', gap: '1.25rem' }}>
                <div
                  style={{
                    display: 'grid',
                    gap: '1rem',
                    gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))',
                  }}
                >
                  <label style={{ display: 'flex', flexDirection: 'column', gap: '0.4rem' }}>
                    <span style={{ fontSize: '0.8125rem', fontWeight: 600 }}>Scenario</span>
                    <select
                      value={assessmentDraft.scenario}
                      onChange={(e) =>
                        handleAssessmentFieldChange(
                          'scenario',
                          e.target.value as DevelopmentScenario | 'all',
                        )
                      }
                      style={{
                        borderRadius: '8px',
                        border: '1px solid #d2d2d7',
                        padding: '0.55rem 0.75rem',
                        fontSize: '0.9rem',
                      }}
                    >
                      <option value="all">All scenarios</option>
                      {SCENARIO_OPTIONS.map((option) => (
                        <option key={option.value} value={option.value}>
                          {option.label}
                        </option>
                      ))}
                    </select>
                  </label>
                  <label style={{ display: 'flex', flexDirection: 'column', gap: '0.4rem' }}>
                    <span style={{ fontSize: '0.8125rem', fontWeight: 600 }}>Overall rating</span>
                    <select
                      value={assessmentDraft.overallRating}
                      onChange={(e) =>
                        handleAssessmentFieldChange('overallRating', e.target.value)
                      }
                      style={{
                        borderRadius: '8px',
                        border: '1px solid #d2d2d7',
                        padding: '0.55rem 0.75rem',
                        fontSize: '0.9rem',
                      }}
                    >
                      {CONDITION_RATINGS.map((rating) => (
                        <option key={rating} value={rating}>
                          {rating}
                        </option>
                      ))}
                    </select>
                  </label>
                  <label style={{ display: 'flex', flexDirection: 'column', gap: '0.4rem' }}>
                    <span style={{ fontSize: '0.8125rem', fontWeight: 600 }}>Overall score</span>
                    <input
                      type="number"
                      min={0}
                      max={100}
                      value={assessmentDraft.overallScore}
                      onChange={(e) => handleAssessmentFieldChange('overallScore', e.target.value)}
                      style={{
                        borderRadius: '8px',
                        border: '1px solid #d2d2d7',
                        padding: '0.55rem 0.75rem',
                        fontSize: '0.9rem',
                      }}
                    />
                  </label>
                  <label style={{ display: 'flex', flexDirection: 'column', gap: '0.4rem' }}>
                    <span style={{ fontSize: '0.8125rem', fontWeight: 600 }}>Risk level</span>
                    <select
                      value={assessmentDraft.riskLevel}
                      onChange={(e) => handleAssessmentFieldChange('riskLevel', e.target.value)}
                      style={{
                        borderRadius: '8px',
                        border: '1px solid #d2d2d7',
                        padding: '0.55rem 0.75rem',
                        fontSize: '0.9rem',
                      }}
                    >
                      {CONDITION_RISK_LEVELS.map((risk) => (
                        <option key={risk} value={risk}>
                          {risk.charAt(0).toUpperCase() + risk.slice(1)}
                        </option>
                      ))}
                    </select>
                  </label>
                  <label style={{ display: 'flex', flexDirection: 'column', gap: '0.4rem' }}>
                    <span style={{ fontSize: '0.8125rem', fontWeight: 600 }}>Inspector name</span>
                    <input
                      type="text"
                      value={assessmentDraft.inspectorName}
                      onChange={(e) => handleAssessmentFieldChange('inspectorName', e.target.value)}
                      placeholder="e.g. Jane Tan"
                      style={{
                        borderRadius: '8px',
                        border: '1px solid #d2d2d7',
                        padding: '0.55rem 0.75rem',
                        fontSize: '0.9rem',
                      }}
                    />
                  </label>
                  <label style={{ display: 'flex', flexDirection: 'column', gap: '0.4rem' }}>
                    <span style={{ fontSize: '0.8125rem', fontWeight: 600 }}>Inspection date &amp; time</span>
                    <input
                      type="datetime-local"
                      value={assessmentDraft.recordedAtLocal}
                      onChange={(e) => handleAssessmentFieldChange('recordedAtLocal', e.target.value)}
                      style={{
                        borderRadius: '8px',
                        border: '1px solid #d2d2d7',
                        padding: '0.55rem 0.75rem',
                        fontSize: '0.9rem',
                      }}
                    />
                  </label>
                </div>

                <label style={{ display: 'flex', flexDirection: 'column', gap: '0.4rem' }}>
                  <span style={{ fontSize: '0.8125rem', fontWeight: 600 }}>Summary</span>
                  <textarea
                    value={assessmentDraft.summary}
                    onChange={(e) => handleAssessmentFieldChange('summary', e.target.value)}
                    rows={3}
                    style={{
                      borderRadius: '8px',
                      border: '1px solid #d2d2d7',
                      padding: '0.75rem',
                      fontSize: '0.9rem',
                    }}
                  />
                </label>

                <label style={{ display: 'flex', flexDirection: 'column', gap: '0.4rem' }}>
                  <span style={{ fontSize: '0.8125rem', fontWeight: 600 }}>Scenario context</span>
                  <textarea
                    value={assessmentDraft.scenarioContext}
                    onChange={(e) =>
                      handleAssessmentFieldChange('scenarioContext', e.target.value)
                    }
                    rows={2}
                    style={{
                      borderRadius: '8px',
                      border: '1px solid #d2d2d7',
                      padding: '0.75rem',
                    fontSize: '0.9rem',
                  }}
                />
              </label>

              <label style={{ display: 'flex', flexDirection: 'column', gap: '0.4rem' }}>
                <span style={{ fontSize: '0.8125rem', fontWeight: 600 }}>
                  Attachments (one per line as “Label | URL”)
                </span>
                <textarea
                  value={assessmentDraft.attachmentsText}
                  onChange={(e) => handleAssessmentFieldChange('attachmentsText', e.target.value)}
                  rows={3}
                  placeholder="Site photo | https://example.com/photo.jpg"
                  style={{
                    borderRadius: '8px',
                    border: '1px solid #d2d2d7',
                    padding: '0.75rem',
                    fontSize: '0.9rem',
                  }}
                />
              </label>

              <div style={{ display: 'grid', gap: '1rem' }}>
                {assessmentDraft.systems.map((system, index) => (
                  <div
                    key={`${system.name}-${index}`}
                    style={{
                        border: '1px solid #e5e5e7',
                        borderRadius: '12px',
                        padding: '1rem',
                        display: 'grid',
                        gap: '0.75rem',
                      }}
                    >
                      <div
                        style={{
                          display: 'flex',
                          justifyContent: 'space-between',
                          alignItems: 'center',
                          flexWrap: 'wrap',
                          gap: '0.5rem',
                        }}
                      >
                        <label style={{ display: 'flex', flexDirection: 'column', gap: '0.4rem' }}>
                          <span style={{ fontSize: '0.8rem', fontWeight: 600 }}>System</span>
                          <input
                            type="text"
                            value={system.name}
                            onChange={(e) =>
                              handleAssessmentSystemChange(index, 'name', e.target.value)
                            }
                            style={{
                              borderRadius: '8px',
                              border: '1px solid #d2d2d7',
                              padding: '0.55rem 0.75rem',
                              fontSize: '0.9rem',
                              minWidth: '12rem',
                            }}
                          />
                        </label>
                        <div style={{ display: 'flex', gap: '0.5rem', flexWrap: 'wrap' }}>
                          <label style={{ display: 'flex', flexDirection: 'column', gap: '0.35rem' }}>
                            <span style={{ fontSize: '0.8rem', fontWeight: 600 }}>Rating</span>
                            <input
                              type="text"
                              value={system.rating}
                              onChange={(e) =>
                                handleAssessmentSystemChange(index, 'rating', e.target.value)
                              }
                              style={{
                                borderRadius: '8px',
                                border: '1px solid #d2d2d7',
                                padding: '0.55rem 0.75rem',
                                fontSize: '0.9rem',
                                width: '6rem',
                              }}
                            />
                          </label>
                          <label style={{ display: 'flex', flexDirection: 'column', gap: '0.35rem' }}>
                            <span style={{ fontSize: '0.8rem', fontWeight: 600 }}>Score</span>
                            <input
                              type="number"
                              min={0}
                              max={100}
                              value={system.score}
                              onChange={(e) =>
                                handleAssessmentSystemChange(index, 'score', e.target.value)
                              }
                              style={{
                                borderRadius: '8px',
                                border: '1px solid #d2d2d7',
                                padding: '0.55rem 0.75rem',
                                fontSize: '0.9rem',
                                width: '6rem',
                              }}
                            />
                          </label>
                        </div>
                      </div>

                      <label style={{ display: 'flex', flexDirection: 'column', gap: '0.35rem' }}>
                        <span style={{ fontSize: '0.8rem', fontWeight: 600 }}>Notes</span>
                        <textarea
                          value={system.notes}
                          onChange={(e) =>
                            handleAssessmentSystemChange(index, 'notes', e.target.value)
                          }
                          rows={2}
                          style={{
                            borderRadius: '8px',
                            border: '1px solid #d2d2d7',
                            padding: '0.7rem',
                            fontSize: '0.9rem',
                          }}
                        />
                      </label>

                      <label style={{ display: 'flex', flexDirection: 'column', gap: '0.35rem' }}>
                        <span style={{ fontSize: '0.8rem', fontWeight: 600 }}>
                          Recommended actions (one per line)
                        </span>
                        <textarea
                          value={system.recommendedActions}
                          onChange={(e) =>
                            handleAssessmentSystemChange(index, 'recommendedActions', e.target.value)
                          }
                          rows={2}
                          style={{
                            borderRadius: '8px',
                            border: '1px solid #d2d2d7',
                            padding: '0.7rem',
                            fontSize: '0.9rem',
                          }}
                        />
                      </label>
                    </div>
                  ))}
                </div>

                <label style={{ display: 'flex', flexDirection: 'column', gap: '0.4rem' }}>
                  <span style={{ fontSize: '0.8125rem', fontWeight: 600 }}>
                    Additional recommended actions
                  </span>
                  <textarea
                    value={assessmentDraft.recommendedActionsText}
                    onChange={(e) =>
                      handleAssessmentFieldChange('recommendedActionsText', e.target.value)
                    }
                    rows={3}
                    style={{
                      borderRadius: '8px',
                      border: '1px solid #d2d2d7',
                      padding: '0.75rem',
                      fontSize: '0.9rem',
                    }}
                  />
                </label>

                <div
                  style={{
                    display: 'flex',
                    justifyContent: 'flex-end',
                    gap: '0.75rem',
                    flexWrap: 'wrap',
                  }}
                >
                  <button
                    type="button"
                    onClick={closeAssessmentEditor}
                    disabled={isSavingAssessment}
                    style={{
                      border: '1px solid #d2d2d7',
                      background: 'white',
                      color: '#1d1d1f',
                      borderRadius: '9999px',
                      padding: '0.55rem 1.25rem',
                      fontSize: '0.875rem',
                      fontWeight: 600,
                      cursor: isSavingAssessment ? 'not-allowed' : 'pointer',
                    }}
                  >
                    Cancel
                  </button>
                  <button
                    type="submit"
                    disabled={isSavingAssessment}
                    style={{
                      border: 'none',
                      background: '#1d1d1f',
                      color: 'white',
                      borderRadius: '9999px',
                      padding: '0.55rem 1.5rem',
                      fontSize: '0.875rem',
                      fontWeight: 600,
                      cursor: isSavingAssessment ? 'not-allowed' : 'pointer',
                    }}
                  >
                    {isSavingAssessment ? 'Saving…' : 'Save inspection'}
                  </button>
                </div>
      </form>
    </div>
  </div>,
  document.body,
)}

      {isQuickAnalysisHistoryOpen &&
        createPortal(
          <div
            role="presentation"
            onClick={(event) => {
              if (event.target === event.currentTarget) {
                setQuickAnalysisHistoryOpen(false)
              }
            }}
            style={{
              position: 'fixed',
              inset: 0,
              background: 'rgba(0,0,0,0.45)',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              padding: '2rem',
              zIndex: 1000,
            }}
          >
            <div
              role="dialog"
              aria-modal="true"
              aria-label="Quick analysis history"
              onClick={(event) => event.stopPropagation()}
              style={{
                background: 'white',
                borderRadius: '16px',
                maxWidth: '900px',
                width: '100%',
                maxHeight: '85vh',
                overflowY: 'auto',
                boxShadow: '0 20px 40px rgba(0,0,0,0.25)',
                padding: '2rem',
                position: 'relative',
              }}
            >
              <button
                type="button"
                onClick={() => setQuickAnalysisHistoryOpen(false)}
                aria-label="Close quick analysis history"
                style={{
                  position: 'absolute',
                  top: '1rem',
                  right: '1rem',
                  border: 'none',
                  background: 'transparent',
                  fontSize: '1.5rem',
                  cursor: 'pointer',
                  color: '#6e6e73',
                }}
              >
                ×
              </button>
              <div style={{ display: 'flex', flexDirection: 'column', gap: '1.5rem' }}>
                <div style={{ display: 'flex', flexDirection: 'column', gap: '0.3rem' }}>
                  <h2
                    style={{
                      margin: 0,
                      fontSize: '1.4rem',
                      fontWeight: 600,
                      letterSpacing: '-0.01em',
                    }}
                  >
                    Quick analysis history
                  </h2>
                  <p style={{ margin: 0, fontSize: '0.9rem', color: '#4b5563' }}>
                    Review the last {quickAnalysisHistory.length} generated snapshots of
                    multi-scenario feasibility metrics.
                  </p>
                </div>
                {quickAnalysisHistory.length === 0 ? (
                  <p style={{ margin: 0, fontSize: '0.9rem', color: '#6b7280' }}>
                    Capture a property to build the quick analysis history timeline.
                  </p>
                ) : (
                  quickAnalysisHistory.map((snapshot) => (
                    <article
                      key={`${snapshot.propertyId}-${snapshot.generatedAt}`}
                      style={{
                        border: '1px solid #e5e7eb',
                        borderRadius: '14px',
                        padding: '1.5rem',
                        display: 'flex',
                        flexDirection: 'column',
                        gap: '1rem',
                        background: '#f9fafb',
                      }}
                    >
                      <div
                        style={{
                          display: 'flex',
                          justifyContent: 'space-between',
                          alignItems: 'baseline',
                          flexWrap: 'wrap',
                          gap: '0.5rem',
                        }}
                      >
                        <h3
                          style={{
                            margin: 0,
                            fontSize: '1.05rem',
                            fontWeight: 600,
                            letterSpacing: '-0.01em',
                          }}
                        >
                          Generated {formatTimestamp(snapshot.generatedAt)}
                        </h3>
                        <span style={{ fontSize: '0.8rem', color: '#6b7280' }}>
                          Property ID: {snapshot.propertyId}
                        </span>
                      </div>
                      <div
                        style={{
                          display: 'grid',
                          gap: '1rem',
                          gridTemplateColumns: 'repeat(auto-fit, minmax(220px, 1fr))',
                        }}
                      >
                        {snapshot.scenarios.map((scenario) => {
                          const scenarioKey =
                            typeof scenario.scenario === 'string'
                              ? (scenario.scenario as DevelopmentScenario)
                              : 'raw_land'
                          const label =
                            scenarioLookup.get(scenarioKey)?.label ??
                            formatScenarioLabel(scenarioKey)
                          const metrics = summariseScenarioMetrics(
                            scenario.metrics ?? {},
                          )
                          return (
                            <section
                              key={`${snapshot.generatedAt}-${scenarioKey}`}
                              style={{
                                border: '1px solid #e5e7eb',
                                borderRadius: '12px',
                                padding: '1rem',
                                background: 'white',
                                display: 'flex',
                                flexDirection: 'column',
                                gap: '0.6rem',
                              }}
                            >
                              <div style={{ display: 'flex', flexDirection: 'column', gap: '0.25rem' }}>
                                <span
                                  style={{ fontSize: '0.75rem', color: '#6b7280', textTransform: 'uppercase' }}
                                >
                                  Scenario
                                </span>
                                <span
                                  style={{ fontSize: '1rem', fontWeight: 600, color: '#111827' }}
                                >
                                  {label}
                                </span>
                              </div>
                              {scenario.headline && (
                                <p style={{ margin: 0, fontSize: '0.85rem', color: '#374151' }}>
                                  {scenario.headline}
                                </p>
                              )}
                              {metrics.length > 0 ? (
                                <ul
                                  style={{
                                    margin: 0,
                                    padding: 0,
                                    listStyle: 'none',
                                    display: 'flex',
                                    flexDirection: 'column',
                                    gap: '0.35rem',
                                  }}
                                >
                                  {metrics.map((metric) => (
                                    <li key={`${scenarioKey}-${metric.key}`}>
                                      <span
                                        style={{
                                          display: 'block',
                                          fontSize: '0.75rem',
                                          letterSpacing: '0.06em',
                                          textTransform: 'uppercase',
                                          color: '#9ca3af',
                                        }}
                                      >
                                        {metric.label}
                                      </span>
                                      <span
                                        style={{ fontSize: '0.9rem', fontWeight: 600, color: '#1f2937' }}
                                      >
                                        {formatScenarioMetricValue(metric.key, metric.value)}
                                      </span>
                                    </li>
                                  ))}
                                </ul>
                              ) : (
                                <p style={{ margin: 0, fontSize: '0.8rem', color: '#6b7280' }}>
                                  No quantitative metrics captured for this scenario run.
                                </p>
                              )}
                            </section>
                          )
                        })}
                      </div>
                    </article>
                  ))
                )}
              </div>
            </div>
          </div>,
          document.body,
        )}

      {isHistoryModalOpen &&
        createPortal(
          <div
            role="presentation"
            onClick={(event) => {
              if (event.target === event.currentTarget) {
                setHistoryModalOpen(false)
              }
            }}
            style={{
              position: 'fixed',
              inset: 0,
              background: 'rgba(0,0,0,0.45)',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              padding: '2rem',
              zIndex: 1000,
            }}
          >
            <div
              role="dialog"
              aria-modal="true"
              aria-label="Inspection history"
              onClick={(event) => event.stopPropagation()}
              style={{
                background: 'white',
                borderRadius: '16px',
                width: 'min(1200px, 95vw)',
                maxHeight: '85vh',
                overflowY: 'auto',
                boxShadow: '0 20px 40px rgba(0,0,0,0.25)',
                padding: '2rem',
                position: 'relative',
              }}
            >
              <button
                type="button"
                onClick={() => setHistoryModalOpen(false)}
                aria-label="Close inspection history"
                style={{
                  position: 'absolute',
                  top: '1rem',
                  right: '1rem',
                  border: 'none',
                  background: 'transparent',
                  fontSize: '1.5rem',
                  cursor: 'pointer',
                  color: '#6e6e73',
                }}
              >
                ×
              </button>
              <InspectionHistoryContent />
            </div>
          </div>,
          document.body,
        )}
    </div>
  )
}

function formatDateTimeLocalInput(isoValue: string | null | undefined): string {
  if (!isoValue) {
    return ''
  }
  const date = new Date(isoValue)
  if (Number.isNaN(date.getTime())) {
    return ''
  }
  const year = date.getFullYear()
  const month = String(date.getMonth() + 1).padStart(2, '0')
  const day = String(date.getDate()).padStart(2, '0')
  const hours = String(date.getHours()).padStart(2, '0')
  const minutes = String(date.getMinutes()).padStart(2, '0')
  return `${year}-${month}-${day}T${hours}:${minutes}`
}

function convertLocalToISO(localValue: string): string | null {
  if (!localValue) {
    return null
  }
  const date = new Date(localValue)
  if (Number.isNaN(date.getTime())) {
    return null
  }
  return date.toISOString()
}

function parseAttachmentsText(value: string): ConditionAttachment[] {
  return value
    .split('\n')
    .map((line) => line.trim())
    .filter((line) => line.length > 0)
    .map((line) => {
      const [labelPart, urlPart] = line.split('|')
      const label = (labelPart ?? '').trim()
      const url = (urlPart ?? '').trim()
      return {
        label: label || url || 'Attachment',
        url: url.length > 0 ? url : null,
      }
    })
}

function safeNumber(value: unknown): number | null {
  if (typeof value === 'number' && Number.isFinite(value)) {
    return value
  }
  if (typeof value === 'string') {
    const parsed = Number(value)
    return Number.isFinite(parsed) ? parsed : null
  }
  return null
}

type InsightSeverity = 'critical' | 'warning' | 'positive' | 'info'

type ConditionInsightView = {
  id: string
  severity: InsightSeverity
  title: string
  detail: string
  specialist: string | null
}

const insightSeverityOrder: Record<InsightSeverity, number> = {
  critical: 0,
  warning: 1,
  info: 2,
  positive: 3,
}

function classifySystemSeverity(
  latestRating: string | null | undefined,
  delta: number | null,
): InsightSeverity | 'neutral' {
  if (!latestRating || typeof latestRating !== 'string') {
    return 'neutral'
  }
  const normalized = latestRating.toUpperCase()
  const negativeRating = normalized === 'D' || normalized === 'E'
  const warningRating = normalized === 'C'

  if (negativeRating) {
    return 'critical'
  }
  if (typeof delta === 'number') {
    if (delta <= -10) {
      return 'critical'
    }
    if (delta <= -5) {
      return 'warning'
    }
    if (delta >= 8) {
      return 'positive'
    }
  }
  if (warningRating) {
    return 'warning'
  }
  if (typeof delta === 'number' && delta >= 4) {
    return 'positive'
  }
  return 'neutral'
}

function buildSystemInsightTitle(
  name: string,
  severity: InsightSeverity,
  delta: number | null,
): string {
  if (severity === 'critical') {
    if (typeof delta === 'number' && delta < 0) {
      return `${name} dropped ${Math.abs(delta)} points`
    }
    return `${name} requires attention`
  }
  if (severity === 'warning') {
    if (typeof delta === 'number' && delta < 0) {
      return `${name} trending down`
    }
    return `${name} rated watch`
  }
  if (severity === 'positive') {
    if (typeof delta === 'number' && delta > 0) {
      return `${name} improved ${delta} points`
    }
    return `${name} improving`
  }
  return name
}

function formatScoreDelta(delta: number): string {
  if (delta === 0) {
    return 'held steady'
  }
  if (delta > 0) {
    return `improved by ${delta} points`
  }
  return `dropped ${Math.abs(delta)} points`
}

function formatDeltaValue(delta: number | null): string {
  if (delta === null) {
    return '0'
  }
  if (delta > 0) {
    return `+${delta}`
  }
  if (delta < 0) {
    return `${delta}`
  }
  return '0'
}

function slugify(value: string): string {
  return value
    .toLowerCase()
    .replace(/[^a-z0-9]+/g, '-')
    .replace(/^-+|-+$/g, '')
    .replace(/-{2,}/g, '-')
    || 'insight'
}

function systemSpecialistHint(name: string): string | null {
  const lower = name.toLowerCase()
  if (lower.includes('struct')) {
    return 'Structural engineer'
  }
  if (lower.includes('mechanical') || lower.includes('electrical') || lower.includes('m&e')) {
    return 'M&E engineer'
  }
  if (lower.includes('compliance') || lower.includes('maintenance') || lower.includes('envelope')) {
    return 'Building surveyor'
  }
  return null
}

function normaliseInsightSeverity(value: string | undefined): InsightSeverity {
  const severity = (value ?? 'warning').toLowerCase()
  if (severity === 'critical' || severity === 'warning' || severity === 'positive' || severity === 'info') {
    return severity as InsightSeverity
  }
  return 'warning'
}

function getSeverityVisuals(
  severity: InsightSeverity | 'neutral',
): { background: string; border: string; text: string; indicator: string; label: string } {
  switch (severity) {
    case 'critical':
      return {
        background: '#fef2f2',
        border: '#fecaca',
        text: '#991b1b',
        indicator: '#dc2626',
        label: 'Critical risk',
      }
    case 'warning':
      return {
        background: '#fef3c7',
        border: '#fde68a',
        text: '#92400e',
        indicator: '#f97316',
        label: 'Watchlist',
      }
    case 'info':
      return {
        background: '#eef2ff',
        border: '#c7d2fe',
        text: '#312e81',
        indicator: '#6366f1',
        label: 'Heads-up',
      }
    case 'positive':
      return {
        background: '#dcfce7',
        border: '#bbf7d0',
        text: '#166534',
        indicator: '#22c55e',
        label: 'Improving',
      }
    default:
      return {
        background: '#f5f5f7',
        border: '#e5e5e7',
        text: '#3a3a3c',
        indicator: '#6e6e73',
        label: 'Stable',
      }
  }
}

function getDeltaVisuals(
  delta: number | null,
): { background: string; border: string; text: string } {
  if (delta === null || delta === 0) {
    return {
      background: '#f5f5f7',
      border: '#e5e5e7',
      text: '#3a3a3c',
    }
  }
  if (delta > 0) {
    return {
      background: '#dcfce7',
      border: '#bbf7d0',
      text: '#166534',
    }
  }
  return {
    background: '#fee2e2',
    border: '#fecaca',
    text: '#b91c1c',
  }
}
const describeDetailLevel = (
  level: GeometryDetailLevel | null | undefined,
): string => {
  if (level && PREVIEW_DETAIL_LABELS[level]) {
    return PREVIEW_DETAIL_LABELS[level]
  }
  return PREVIEW_DETAIL_LABELS.medium
}
