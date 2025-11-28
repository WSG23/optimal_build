import { useCallback, useEffect, useMemo, useRef, useState } from 'react'
// createPortal is used by modal components
import {
  capturePropertyForDevelopment,
  exportConditionReport,
  type DevelopmentScenario,
  type SiteAcquisitionResult,
  type DeveloperAssetOptimization,
  type GeometryDetailLevel,
} from '../../../api/siteAcquisition'
import { Preview3DViewer } from '../../components/site-acquisition/Preview3DViewer'
import { forwardGeocodeAddress, reverseGeocodeCoords } from '../../../api/geocoding'

// Extracted types, constants, utils, and hooks
import type { QuickAnalysisEntry } from './types'
import {
  // SCENARIO_OPTIONS and JURISDICTION_OPTIONS are used by PropertyCaptureForm
  CONDITION_RATINGS,
  CONDITION_RISK_LEVELS,
  PREVIEW_DETAIL_OPTIONS,
  PREVIEW_DETAIL_LABELS,
} from './constants'
import {
  toTitleCase,
  safeNumber,
  describeDetailLevel,
} from './utils'
// formatCategoryName and getSeverityVisuals are used by child components
import { usePreviewJob } from './hooks/usePreviewJob'
import { useChecklist } from './hooks/useChecklist'
import { useConditionAssessment } from './hooks/useConditionAssessment'
import { useScenarioComparison } from './hooks/useScenarioComparison'
import { DueDiligenceChecklistSection } from './components/checklist/DueDiligenceChecklistSection'
import {
  ConditionAssessmentSection,
  ConditionAssessmentEditor,
} from './components/condition-assessment'
// InspectionHistoryContent is used by InspectionHistoryModal component
import { PropertyOverviewSection } from './components/property-overview'
import { ScenarioFocusSection } from './components/scenario-focus'
import { MultiScenarioComparisonSection } from './components/multi-scenario-comparison'
import { QuickAnalysisHistoryModal, InspectionHistoryModal } from './components/modals'
import { PropertyCaptureForm } from './components/capture-form'

// Note: Constants, types, and utility functions are now imported from:
// - ./types - Page-specific types
// - ./constants - All constants (SCENARIO_OPTIONS, JURISDICTION_OPTIONS, etc.)
// - ./utils - Utility functions (formatters, insights, draftBuilders)
// - ./hooks - Custom hooks (usePreviewJob, useChecklist, useConditionAssessment, useScenarioComparison)

export function SiteAcquisitionPage() {
  const [jurisdictionCode, setJurisdictionCode] = useState('SG')
  const [latitude, setLatitude] = useState('1.3000')
  const [longitude, setLongitude] = useState('103.8500')
  const [address, setAddress] = useState('')
  const [geocodeError, setGeocodeError] = useState<string | null>(null)
  const [selectedScenarios, setSelectedScenarios] = useState<DevelopmentScenario[]>([])
  const [isCapturing, setIsCapturing] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [capturedProperty, setCapturedProperty] = useState<SiteAcquisitionResult | null>(null)

  // Preview job state - managed by usePreviewJob hook
  const {
    previewJob,
    setPreviewJob,
    previewDetailLevel,
    setPreviewDetailLevel,
    isRefreshingPreview,
    previewLayerMetadata,
    previewLayerVisibility,
    previewFocusLayerId,
    isPreviewMetadataLoading,
    previewMetadataError,
    hiddenLayerCount,
    colorLegendEntries,
    legendHasPendingChanges,
    previewViewerMetadataUrl,
    handleRefreshPreview,
    handleToggleLayerVisibility,
    handleSoloPreviewLayer,
    handleShowAllLayers,
    handleFocusLayer,
    handleResetLayerFocus,
    handleLegendEntryChange,
    handleLegendReset,
  } = usePreviewJob({ capturedProperty })

  // Checklist state - managed by useChecklist hook
  // Note: scenarioFilterOptions is computed locally (includes scenarioOverrideEntries)
  const {
    checklistItems,
    isLoadingChecklist,
    selectedCategory,
    setSelectedCategory,
    activeScenario,
    setActiveScenario,
    availableChecklistScenarios,
    filteredChecklistItems,
    displaySummary,
    activeScenarioDetails,
    scenarioChecklistProgress,
    scenarioLookup,
    handleChecklistUpdate,
  } = useChecklist({ capturedProperty })

  // Condition assessment state from hook
  const {
    conditionAssessment,
    isLoadingCondition,
    isEditingAssessment,
    assessmentEditorMode,
    assessmentDraft,
    isSavingAssessment,
    assessmentSaveMessage,
    assessmentHistory,
    isLoadingAssessmentHistory,
    assessmentHistoryError,
    historyViewMode,
    setHistoryViewMode,
    scenarioAssessments,
    isLoadingScenarioAssessments,
    scenarioAssessmentsError,
    latestAssessmentEntry,
    previousAssessmentEntry,
    openAssessmentEditor,
    closeAssessmentEditor,
    handleAssessmentFieldChange,
    handleAssessmentSystemChange,
    handleAssessmentSubmit,
    resetAssessmentDraft,
  } = useConditionAssessment({ capturedProperty, activeScenario })

  // Currency symbol for formatting (needed by useScenarioComparison)
  const currencySymbol = capturedProperty?.currencySymbol || 'S$'

  // Scenario comparison state from hook
  const {
    quickAnalysisScenarios,
    comparisonScenarios,
    scenarioOverrideEntries,
    scenarioComparisonData,
    scenarioComparisonTableRows,
    scenarioComparisonVisible,
    activeScenarioSummary,
    baseScenarioAssessment,
    setScenarioComparisonBase,
    scenarioComparisonEntries,
    systemComparisons,
    systemComparisonMap,
    combinedConditionInsights,
    insightSubtitle,
    recommendedActionDiff,
    comparisonSummary,
    quickAnalysisHistory,
    formatScenarioMetricValue,
    summariseScenarioMetrics,
    formatScenarioLabel,
    formatNumberMetric,
    formatCurrency,
  } = useScenarioComparison({
    capturedProperty,
    activeScenario,
    conditionAssessment,
    assessmentHistory,
    scenarioAssessments,
    scenarioChecklistProgress,
    displaySummary,
    currencySymbol,
  })

  const [isExportingReport, setIsExportingReport] = useState(false)
  const [reportExportMessage, setReportExportMessage] = useState<string | null>(null)
  const propertyId = capturedProperty?.propertyId ?? null
  const [isHistoryModalOpen, setHistoryModalOpen] = useState(false)
  const [isQuickAnalysisHistoryOpen, setQuickAnalysisHistoryOpen] = useState(false)
  useEffect(() => {
    if (quickAnalysisHistory.length === 0 && isQuickAnalysisHistoryOpen) {
      setQuickAnalysisHistoryOpen(false)
    }
  }, [quickAnalysisHistory.length, isQuickAnalysisHistoryOpen])

  // Escape key handling for modals (useConditionAssessment handles history view mode reset)
  useEffect(() => {
    if (!isHistoryModalOpen && !isEditingAssessment) {
      return
    }

    const handleKeyDown = (event: KeyboardEvent) => {
      if (event.key === 'Escape') {
        event.preventDefault()
        if (isEditingAssessment) {
          closeAssessmentEditor()
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
  }, [isHistoryModalOpen, isEditingAssessment, closeAssessmentEditor])

  // Note: Condition assessment reset is handled by useConditionAssessment hook
  // Note: quickAnalysisScenarios, comparisonScenarios, scenarioOverrideEntries are provided by useScenarioComparison hook

  // scenarioFilterOptions is computed locally because it includes scenarioOverrideEntries from hook
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
      ['all', ...scenarioFilterOptions] as Array<'all' | DevelopmentScenario>,
    [scenarioFilterOptions],
  )

  // Note: scenarioChecklistProgress is provided by useChecklist hook
  // Note: formatScenarioLabel, formatNumberMetric, formatCurrency, formatScenarioMetricValue,
  // summariseScenarioMetrics are provided by useScenarioComparison hook

  const scenarioComparisonRef = useRef<HTMLDivElement | null>(null)
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

      // Subtitle: show custom label or asset type, followed by allocation
      const labelForSubtitle = legend?.label ?? toTitleCase(layer.assetType)
      const subtitle = allocationValue !== '—'
        ? `${labelForSubtitle} · ${allocationValue}`
        : labelForSubtitle

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

  // Note: scenarioComparisonBase useEffect, baseScenarioAssessment, and scenarioComparisonEntries
  // are provided by useScenarioComparison hook

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
      type Rating = (typeof CONDITION_RATINGS)[number]
      const currentIndex = CONDITION_RATINGS.indexOf(current as Rating)
      const referenceIndex = CONDITION_RATINGS.indexOf(reference as Rating)
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
      type RiskLevel = (typeof CONDITION_RISK_LEVELS)[number]
      const currentIndex = CONDITION_RISK_LEVELS.indexOf(current as RiskLevel)
      const referenceIndex = CONDITION_RISK_LEVELS.indexOf(reference as RiskLevel)
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

  // Note: systemComparisons, systemComparisonMap, systemTrendInsights, backendInsightViews,
  // combinedConditionInsights, insightSubtitle, scenarioComparisonData, scenarioComparisonTableRows,
  // scenarioComparisonVisible, activeScenarioSummary, recommendedActionDiff, comparisonSummary,
  // and the quick analysis history snapshot effect are provided by useScenarioComparison hook

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
  }, [activeScenario, setSelectedCategory])

  // Note: All condition assessment loading, effects, and handlers are now provided by useConditionAssessment hook

  const handleForwardGeocode = useCallback(async () => {
    if (!address.trim()) {
      setGeocodeError('Please enter an address to geocode.')
      return
    }
    try {
      setGeocodeError(null)
      const result = await forwardGeocodeAddress(address.trim())
      setLatitude(result.latitude.toString())
      setLongitude(result.longitude.toString())
    } catch (err) {
      console.error('Forward geocode failed', err)
      setGeocodeError(
        err instanceof Error ? err.message : 'Unable to geocode address.',
      )
    }
  }, [address])

  const handleReverseGeocode = useCallback(async () => {
    const parsedLat = Number(latitude)
    const parsedLon = Number(longitude)
    if (!Number.isFinite(parsedLat) || !Number.isFinite(parsedLon)) {
      setGeocodeError(
        'Please provide valid coordinates before reverse geocoding.',
      )
      return
    }
    try {
      setGeocodeError(null)
      const result = await reverseGeocodeCoords(parsedLat, parsedLon)
      setAddress(result.formattedAddress)
    } catch (err) {
      console.error('Reverse geocode failed', err)
      setGeocodeError(
        err instanceof Error ? err.message : 'Unable to reverse geocode.',
      )
    }
  }, [latitude, longitude])

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
        jurisdictionCode,
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

  // Note: handleChecklistUpdate is provided by useChecklist hook

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
      <PropertyCaptureForm
        jurisdictionCode={jurisdictionCode}
        setJurisdictionCode={setJurisdictionCode}
        address={address}
        setAddress={setAddress}
        latitude={latitude}
        setLatitude={setLatitude}
        longitude={longitude}
        setLongitude={setLongitude}
        selectedScenarios={selectedScenarios}
        isCapturing={isCapturing}
        error={error}
        geocodeError={geocodeError}
        capturedProperty={capturedProperty}
        onCapture={handleCapture}
        onForwardGeocode={handleForwardGeocode}
        onReverseGeocode={handleReverseGeocode}
        onToggleScenario={toggleScenario}
      />

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
          <PropertyOverviewSection cards={propertyOverviewCards} />
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
                      <strong style={{ fontSize: '0.9rem', color: '#111827' }}>{toTitleCase(entry.label)}</strong>
                      <input
                        type="color"
                        aria-label={`Colour for ${toTitleCase(entry.label)}`}
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
                  disabled={colorLegendEntries.length === 0}
                  style={{
                    padding: '0.45rem 0.85rem',
                    borderRadius: '9999px',
                    border: '1px solid #d1d5db',
                    background: '#f9fafb',
                    fontWeight: 600,
                    color: '#111827',
                    fontSize: '0.85rem',
                    cursor: colorLegendEntries.length === 0 ? 'not-allowed' : 'pointer',
                    opacity: colorLegendEntries.length === 0 ? 0.5 : 1,
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
        <ScenarioFocusSection
          scenarioFocusOptions={scenarioFocusOptions}
          scenarioLookup={scenarioLookup}
          activeScenario={activeScenario}
          activeScenarioSummary={activeScenarioSummary}
          scenarioChecklistProgress={scenarioChecklistProgress}
          displaySummary={displaySummary}
          quickAnalysisHistoryCount={quickAnalysisHistory.length}
          scenarioComparisonVisible={scenarioComparisonVisible}
          setActiveScenario={setActiveScenario}
          onCompareScenarios={handleScenarioComparisonScroll}
          onOpenQuickAnalysisHistory={() => setQuickAnalysisHistoryOpen(true)}
          onOpenInspectionHistory={() => setHistoryModalOpen(true)}
          formatScenarioLabel={formatScenarioLabel}
        />
      )}

      {/* Due Diligence Checklist */}
      <DueDiligenceChecklistSection
        capturedProperty={capturedProperty}
        checklistItems={checklistItems}
        filteredChecklistItems={filteredChecklistItems}
        availableChecklistScenarios={availableChecklistScenarios}
        scenarioLookup={scenarioLookup}
        displaySummary={displaySummary}
        activeScenario={activeScenario}
        activeScenarioDetails={activeScenarioDetails}
        selectedCategory={selectedCategory}
        isLoadingChecklist={isLoadingChecklist}
        setActiveScenario={setActiveScenario}
        setSelectedCategory={setSelectedCategory}
        handleChecklistUpdate={handleChecklistUpdate}
      />

      <MultiScenarioComparisonSection
        capturedProperty={capturedProperty}
        quickAnalysisScenariosCount={quickAnalysisScenarios.length}
        scenarioComparisonData={scenarioComparisonData}
        feasibilitySignals={feasibilitySignals}
        comparisonScenariosCount={comparisonScenarios.length}
        activeScenario={activeScenario}
        scenarioLookup={scenarioLookup}
        propertyId={propertyId}
        isExportingReport={isExportingReport}
        reportExportMessage={reportExportMessage}
        setActiveScenario={setActiveScenario}
        handleReportExport={handleReportExport}
        formatRecordedTimestamp={formatRecordedTimestamp}
      />

      {/* Property Condition Assessment Section */}
      <ConditionAssessmentSection
        capturedProperty={capturedProperty}
        conditionAssessment={conditionAssessment}
        isLoadingCondition={isLoadingCondition}
        latestAssessmentEntry={latestAssessmentEntry}
        previousAssessmentEntry={previousAssessmentEntry}
        assessmentHistoryError={assessmentHistoryError}
        isLoadingAssessmentHistory={isLoadingAssessmentHistory}
        assessmentSaveMessage={assessmentSaveMessage}
        scenarioAssessments={scenarioAssessments}
        isLoadingScenarioAssessments={isLoadingScenarioAssessments}
        scenarioAssessmentsError={scenarioAssessmentsError}
        scenarioOverrideEntries={scenarioOverrideEntries}
        baseScenarioAssessment={baseScenarioAssessment}
        scenarioComparisonEntries={scenarioComparisonEntries}
        combinedConditionInsights={combinedConditionInsights}
        insightSubtitle={insightSubtitle}
        systemComparisonMap={systemComparisonMap}
        isExportingReport={isExportingReport}
        scenarioLookup={scenarioLookup}
        formatRecordedTimestamp={formatRecordedTimestamp}
        formatScenarioLabel={formatScenarioLabel}
        describeRatingChange={describeRatingChange}
        describeRiskChange={describeRiskChange}
        openAssessmentEditor={openAssessmentEditor}
        setScenarioComparisonBase={setScenarioComparisonBase}
        handleReportExport={handleReportExport}
        setHistoryModalOpen={setHistoryModalOpen}
        InlineInspectionHistorySummary={InlineInspectionHistorySummary}
      />

      {/* Condition Assessment Editor Modal */}
      <ConditionAssessmentEditor
        isOpen={isEditingAssessment}
        mode={assessmentEditorMode}
        draft={assessmentDraft}
        isSaving={isSavingAssessment}
        activeScenario={activeScenario}
        scenarioFocusOptions={scenarioFocusOptions}
        scenarioLookup={scenarioLookup}
        formatScenarioLabel={formatScenarioLabel}
        onClose={closeAssessmentEditor}
        onReset={resetAssessmentDraft}
        onSubmit={handleAssessmentSubmit}
        onFieldChange={handleAssessmentFieldChange}
        onSystemChange={handleAssessmentSystemChange}
        setActiveScenario={setActiveScenario}
      />

      <QuickAnalysisHistoryModal
        isOpen={isQuickAnalysisHistoryOpen}
        onClose={() => setQuickAnalysisHistoryOpen(false)}
        quickAnalysisHistory={quickAnalysisHistory}
        scenarioLookup={scenarioLookup}
        formatScenarioLabel={formatScenarioLabel}
        summariseScenarioMetrics={summariseScenarioMetrics}
        formatScenarioMetricValue={formatScenarioMetricValue}
      />

      <InspectionHistoryModal
        isOpen={isHistoryModalOpen}
        onClose={() => setHistoryModalOpen(false)}
        historyViewMode={historyViewMode}
        setHistoryViewMode={setHistoryViewMode}
        assessmentHistoryError={assessmentHistoryError}
        isLoadingAssessmentHistory={isLoadingAssessmentHistory}
        assessmentHistory={assessmentHistory}
        activeScenario={activeScenario}
        latestAssessmentEntry={latestAssessmentEntry}
        previousAssessmentEntry={previousAssessmentEntry}
        comparisonSummary={comparisonSummary}
        systemComparisons={systemComparisons}
        recommendedActionDiff={recommendedActionDiff}
        scenarioComparisonVisible={scenarioComparisonVisible}
        scenarioComparisonRef={scenarioComparisonRef}
        scenarioComparisonTableRows={scenarioComparisonTableRows}
        scenarioAssessments={scenarioAssessments}
        formatScenarioLabel={formatScenarioLabel}
        formatRecordedTimestamp={formatRecordedTimestamp}
      />
    </div>
  )
}
