import {
  FeasibilityAssessmentRequest,
  FeasibilityAssessmentResponse,
  FeasibilityRule,
  FeasibilityRulesResponse,
  NewFeasibilityProjectInput,
  RuleAssessmentResult,
} from './types'

const baseRules: FeasibilityRule[] = [
  {
    id: 'ura-plot-ratio',
    title: 'Plot ratio within URA master plan envelope',
    description:
      'Maximum gross plot ratio permitted for the planning area according to the 2025 URA master plan.',
    authority: 'URA',
    topic: 'zoning',
    parameterKey: 'planning.gross_plot_ratio',
    operator: '<=',
    value: '3.5',
    severity: 'critical',
    defaultSelected: true,
  },
  {
    id: 'bca-site-coverage',
    title: 'Site coverage for residential developments',
    description:
      'Site coverage must not exceed the prescribed limit to maintain environmental quality.',
    authority: 'BCA',
    topic: 'envelope',
    parameterKey: 'envelope.site_coverage_percent',
    operator: '<=',
    value: '45',
    unit: '%',
    severity: 'important',
    defaultSelected: true,
  },
  {
    id: 'scdf-access',
    title: 'Fire appliance access road width',
    description: 'Primary fire engine access roads must satisfy minimum width requirements.',
    authority: 'SCDF',
    topic: 'fire safety',
    parameterKey: 'fire.access.road_width_m',
    operator: '>=',
    value: '4.5',
    unit: 'm',
    severity: 'critical',
    defaultSelected: true,
  },
  {
    id: 'nea-bin-centre',
    title: 'Provision of bin centre',
    description: 'Residential developments above 40 units must provide an on-site bin centre.',
    authority: 'NEA',
    topic: 'environmental health',
    parameterKey: 'operations.bin_centre_required',
    operator: '=',
    value: 'true',
    severity: 'informational',
  },
]

const delay = (ms: number) => new Promise((resolve) => setTimeout(resolve, ms))

function buildRulesResponse(project: NewFeasibilityProjectInput): FeasibilityRulesResponse {
  return {
    projectId: `project-${project.name || 'draft'}`,
    rules: baseRules,
    recommendedRuleIds: baseRules.filter((rule) => rule.defaultSelected).map((rule) => rule.id),
    summary: {
      complianceFocus: 'Envelope controls and critical access provisions',
      notes: `Auto-selected based on ${project.landUse} land use profile`,
    },
  }
}

function calculateSummary(
  project: NewFeasibilityProjectInput,
  selectedRules: RuleAssessmentResult[],
): FeasibilityAssessmentResponse['summary'] {
  const maxPlotRatio = 3.5
  const maxGfa = Math.round(project.siteAreaSqm * maxPlotRatio)
  const achievableFactor = selectedRules.some((rule) => rule.status === 'fail') ? 0.65 : 0.82
  const achievableGfa = Math.round(maxGfa * achievableFactor)
  const averageUnitSize = project.landUse === 'residential' ? 85 : 120
  const estimatedUnits = Math.max(1, Math.round(achievableGfa / averageUnitSize))
  const coverageLimit = 45

  return {
    maxPermissibleGfaSqm: maxGfa,
    estimatedAchievableGfaSqm: achievableGfa,
    estimatedUnitCount: estimatedUnits,
    siteCoveragePercent: Math.min(coverageLimit, (achievableFactor * 100) / 2),
    remarks:
      selectedRules.every((rule) => rule.status === 'pass')
        ? 'All checked parameters comply with the default envelope.'
        : 'Certain parameters require design revisions before proceeding.',
  }
}

function buildAssessmentResponse(
  payload: FeasibilityAssessmentRequest,
): FeasibilityAssessmentResponse {
  const { project, selectedRuleIds } = payload
  const selected = baseRules.filter((rule) => selectedRuleIds.includes(rule.id))

  const results: RuleAssessmentResult[] = selected.map((rule, index) => {
    const status = index % 3 === 0 ? 'warning' : index % 2 === 0 ? 'pass' : 'fail'
    const actualValue = rule.parameterKey.includes('plot_ratio')
      ? project.targetGrossFloorAreaSqm
        ? (project.targetGrossFloorAreaSqm / project.siteAreaSqm).toFixed(2)
        : undefined
      : undefined

    return {
      ...rule,
      status,
      actualValue,
      notes:
        status === 'fail'
          ? 'Adjust design parameters or consult the respective authority.'
          : status === 'warning'
            ? 'Consider alternative layouts to increase compliance buffer.'
            : undefined,
    }
  })

  const recommendations = [
    'Share the feasibility snapshot with the wider design team to align on constraints.',
  ]

  if (results.some((rule) => rule.status === 'fail')) {
    recommendations.push('Schedule a coordination call with URA/BCA to clarify envelope outcomes.')
  }

  if (results.some((rule) => rule.status === 'warning')) {
    recommendations.push('Investigate design options to improve fire access compliance buffers.')
  }

  return {
    projectId: `project-${project.name || 'draft'}`,
    summary: calculateSummary(project, results),
    rules: results,
    recommendations,
  }
}

export async function fetchFeasibilityRules(
  project: NewFeasibilityProjectInput,
): Promise<FeasibilityRulesResponse> {
  await delay(200)
  return buildRulesResponse(project)
}

export async function submitFeasibilityAssessment(
  payload: FeasibilityAssessmentRequest,
): Promise<FeasibilityAssessmentResponse> {
  await delay(350)
  return buildAssessmentResponse(payload)
}
