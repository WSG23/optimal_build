import { useCallback, useEffect, useMemo, useState } from 'react'

import type { AuditEvent, CadImportSummary, OverlaySuggestion } from '../api/client'
import { AppLayout } from '../App'
import { useApiClient } from '../api/client'
import { useTranslation } from '../i18n'
import AuditTimelinePanel from '../modules/cad/AuditTimelinePanel'
import BulkReviewControls from '../modules/cad/BulkReviewControls'
import CadDetectionPreview from '../modules/cad/CadDetectionPreview'
import ExportDialog from '../modules/cad/ExportDialog'
import LayerTogglePanel from '../modules/cad/LayerTogglePanel'
import ZoneLockControls from '../modules/cad/ZoneLockControls'
import { DetectionStatus, DetectedUnit } from '../modules/cad/types'

const DEFAULT_PROJECT_ID = 5821

interface AggregatedSuggestion {
  key: string
  suggestion: OverlaySuggestion
  count: number
  status: DetectionStatus
  missingMetricKey?: string
  totalArea: number
}

function normaliseStatus(status: string): DetectionStatus {
  const value = status.toLowerCase()
  if (value === 'approved') {
    return 'approved'
  }
  if (value === 'rejected') {
    return 'rejected'
  }
  if (value === 'pending') {
    return 'pending'
  }
  return 'source'
}

function deriveAreaSqm(suggestion: OverlaySuggestion): number {
  const payload = suggestion.enginePayload
  const payloadWithArea = payload as { area_sqm?: unknown }
  const payloadWithAffectedArea = payload as { affected_area_sqm?: unknown }
  const directArea =
    typeof payloadWithArea.area_sqm === 'number'
      ? payloadWithArea.area_sqm
      : typeof payloadWithAffectedArea.affected_area_sqm === 'number'
        ? payloadWithAffectedArea.affected_area_sqm
        : null
  if (typeof directArea === 'number') {
    return directArea
  }
  if (typeof suggestion.score === 'number') {
    return Math.max(0, Math.round(suggestion.score * 1000) / 10)
  }
  return 0
}

const STATUS_PRIORITY: DetectionStatus[] = [
  'pending',
  'rejected',
  'approved',
  'source',
]

const STATUS_LABEL_KEYS: Record<DetectionStatus, string> = {
  source: 'controls.source',
  pending: 'controls.pending',
  approved: 'controls.approved',
  rejected: 'controls.rejected',
}

function getStatusPriority(status: DetectionStatus): number {
  const priority = STATUS_PRIORITY.indexOf(status)
  return priority === -1 ? STATUS_PRIORITY.length : priority
}

function getSuggestionTimestamp(suggestion: OverlaySuggestion): number {
  const updated = Date.parse(suggestion.updatedAt)
  if (Number.isFinite(updated)) {
    return updated
  }
  const created = Date.parse(suggestion.createdAt)
  if (Number.isFinite(created)) {
    return created
  }
  return 0
}

function getMissingMetricKey(suggestion: OverlaySuggestion): string | undefined {
  const payload = suggestion.enginePayload as {
    missing_metric?: unknown
  }
  const props = suggestion.props as {
    metric?: unknown
  }
  if (typeof payload?.missing_metric === 'string') {
    return payload.missing_metric
  }
  if (typeof props?.metric === 'string') {
    return props.metric
  }
  return undefined
}

export function filterLatestUnitSpaceSuggestions(
  suggestions: OverlaySuggestion[],
): OverlaySuggestion[] {
  const latestByCode = new Map<string, number>()
  for (const suggestion of suggestions) {
    if (!suggestion.code.startsWith('unit_space_')) {
      continue
    }
    const timestamp = getSuggestionTimestamp(suggestion)
    const existing = latestByCode.get(suggestion.code)
    if (existing == null || timestamp > existing) {
      latestByCode.set(suggestion.code, timestamp)
    }
  }

  const seen = new Set<string>()
  return suggestions.filter((suggestion) => {
    if (!suggestion.code.startsWith('unit_space_')) {
      return true
    }
    const latestTimestamp = latestByCode.get(suggestion.code)
    if (latestTimestamp == null) {
      return true
    }
    const timestamp = getSuggestionTimestamp(suggestion)
    if (timestamp !== latestTimestamp) {
      return false
    }
    if (seen.has(suggestion.code)) {
      return false
    }
    seen.add(suggestion.code)
    return true
  })
}

export function aggregateOverlaySuggestions(
  suggestions: OverlaySuggestion[],
): AggregatedSuggestion[] {
  const groups = new Map<
    string,
    {
      key: string
      latest: OverlaySuggestion
      latestTimestamp: number
      status: DetectionStatus
      firstIndex: number
      missingMetricKey?: string
      count: number
      totalArea: number
    }
  >()

  suggestions.forEach((suggestion, index) => {
    const status = normaliseStatus(suggestion.status)
    const missingMetricKey = getMissingMetricKey(suggestion)
    const groupKey = missingMetricKey ?? suggestion.code
    const timestamp = getSuggestionTimestamp(suggestion)
    const area = deriveAreaSqm(suggestion)
    const existing = groups.get(groupKey)
    if (!existing) {
      groups.set(groupKey, {
        key: groupKey,
        latest: suggestion,
        latestTimestamp: timestamp,
        status,
        firstIndex: index,
        missingMetricKey,
        count: 1,
        totalArea: area,
      })
      return
    }

    existing.count += 1
    existing.totalArea += area
    if (getStatusPriority(status) < getStatusPriority(existing.status)) {
      existing.status = status
    }
    if (!existing.missingMetricKey && missingMetricKey) {
      existing.missingMetricKey = missingMetricKey
    }
    if (timestamp >= existing.latestTimestamp) {
      existing.latest = suggestion
      existing.latestTimestamp = timestamp
    }
  })

  return Array.from(groups.values())
    .sort((a, b) => a.firstIndex - b.firstIndex)
    .map((group) => ({
      key: group.key,
      suggestion: group.latest,
      count: group.count,
      status: group.status,
      missingMetricKey: group.missingMetricKey,
      totalArea: group.totalArea,
    }))
}

export function CadDetectionPage() {
  const apiClient = useApiClient()
  const { t, i18n } = useTranslation()
  const [projectId] = useState<number>(DEFAULT_PROJECT_ID)
  const [suggestions, setSuggestions] = useState<OverlaySuggestion[]>([])
  const [loadingSuggestions, setLoadingSuggestions] = useState(false)
  const [mutationPending, setMutationPending] = useState(false)
  const [locked, setLocked] = useState(false)
  const [auditEvents, setAuditEvents] = useState<AuditEvent[]>([])
  const [auditLoading, setAuditLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [exporting, setExporting] = useState(false)
  const [importSummary, setImportSummary] = useState<CadImportSummary | null>(null)
  const [loadingImport, setLoadingImport] = useState(false)
  const [activeLayers, setActiveLayers] = useState<DetectionStatus[]>(['source', 'pending'])

  const fetchLatestImport = useCallback(async () => {
    setLoadingImport(true)
    try {
      const summary = await apiClient.getLatestImport(projectId)
      setImportSummary(summary)
    } catch (err) {
      setImportSummary(null)
      setError(
        (prev) =>
          prev ?? (err instanceof Error ? err.message : t('detection.loadError')),
      )
    } finally {
      setLoadingImport(false)
    }
  }, [apiClient, projectId, t])

  const refreshAudit = useCallback(async () => {
    setAuditLoading(true)
    try {
      const events = await apiClient.listAuditTrail(projectId, {
        eventType: 'overlay_decision',
      })
      setAuditEvents(events)
    } catch (err) {
      // Surface audit errors in the shared error banner
      setError(
        (prev) =>
          prev ??
          (err instanceof Error ? err.message : t('detection.auditError')),
      )
    } finally {
      setAuditLoading(false)
    }
  }, [apiClient, projectId, t])

  const refreshSuggestions = useCallback(async () => {
    setLoadingSuggestions(true)
    setError(null)
    try {
      const items = await apiClient.listOverlaySuggestions(projectId)
      setSuggestions(items)
    } catch (err) {
      setError(err instanceof Error ? err.message : t('detection.loadError'))
    } finally {
      setLoadingSuggestions(false)
    }
  }, [apiClient, projectId, t])

  useEffect(() => {
    let cancelled = false
    const initialise = async () => {
      await refreshSuggestions()
      if (!cancelled) {
        await fetchLatestImport()
      }
      if (!cancelled) {
        await refreshAudit()
      }
    }
    initialise().catch((err) => {
      setError(
        (prev) =>
          prev ??
          (err instanceof Error ? err.message : t('detection.loadError')),
      )
    })
    return () => {
      cancelled = true
    }
  }, [fetchLatestImport, refreshAudit, refreshSuggestions, t])

  const filteredSuggestions = useMemo(
    () => filterLatestUnitSpaceSuggestions(suggestions),
    [suggestions],
  )

  const aggregatedSuggestions = useMemo(
    () => aggregateOverlaySuggestions(filteredSuggestions),
    [filteredSuggestions],
  )

  const overlays = useMemo(
    () => aggregatedSuggestions.map((item) => item.suggestion.code),
    [aggregatedSuggestions],
  )
  const hints = useMemo(
    () =>
      aggregatedSuggestions
        .map((item) => item.suggestion.rationale)
        .filter((value): value is string => Boolean(value)),
    [aggregatedSuggestions],
  )

  const metricLabels = useMemo(
    () => ({
      front_setback_m: t('detection.override.prompts.frontSetback'),
      side_setback_m: t('detection.override.prompts.sideSetback'),
      rear_setback_m: t('detection.override.prompts.rearSetback'),
      max_height_m: t('detection.override.prompts.maxHeight'),
      site_area_sqm: t('detection.override.prompts.siteArea'),
      gross_floor_area_sqm: t('detection.override.prompts.grossFloorArea'),
    }),
    [t],
  )

  const units = useMemo<DetectedUnit[]>(
    () => {
      const overrides = importSummary?.overrides ?? {}
      return aggregatedSuggestions.map((entry, index) => {
        const missingMetricKey = entry.missingMetricKey ?? null
        const overrideValue =
          missingMetricKey && typeof overrides[missingMetricKey] === 'number'
            ? overrides[missingMetricKey]
            : null
        const metricLabel =
          missingMetricKey && metricLabels[missingMetricKey as keyof typeof metricLabels]
            ? metricLabels[missingMetricKey as keyof typeof metricLabels]
            : missingMetricKey ?? undefined
        const baseLabel =
          entry.suggestion.title || entry.suggestion.code || entry.key
        const label =
          entry.count > 1
            ? `${baseLabel} ${t('detection.countSuffix', { count: entry.count })}`
            : baseLabel
        const areaSqm =
          entry.totalArea > 0
            ? entry.totalArea
            : deriveAreaSqm(entry.suggestion)
        const overrideDisplay =
          missingMetricKey && overrideValue != null
            ? `${metricLabel ?? missingMetricKey}: ${new Intl.NumberFormat(undefined, {
                maximumFractionDigits: 2,
                minimumFractionDigits: Number.isInteger(overrideValue) ? 0 : 2,
              }).format(overrideValue)}`
            : undefined
        return {
          id: entry.key,
          floor: index + 1,
          unitLabel: label,
          areaSqm,
          status: entry.status,
          missingMetricKey: missingMetricKey ?? undefined,
          overrideValue,
          overrideDisplay,
          metricLabel,
        }
      })
    },
    [aggregatedSuggestions, importSummary?.overrides, metricLabels, t],
  )

  const visibleUnits = useMemo(
    () => units.filter((unit) => activeLayers.includes(unit.status)),
    [units, activeLayers],
  )

  const pendingCount = useMemo(
    () => aggregatedSuggestions.filter((entry) => entry.status === 'pending').length,
    [aggregatedSuggestions],
  )

  const hiddenStatusLabels = useMemo(() => {
    const focus: DetectionStatus[] = ['approved', 'rejected']
    const hidden = focus.filter((status) => !activeLayers.includes(status))
    if (hidden.length === 0) {
      return []
    }
    return hidden.map((status) => t(STATUS_LABEL_KEYS[status]))
  }, [activeLayers, t])

  const statusListSeparator = i18n.resolvedLanguage === 'ja' ? '、' : ', '

  const handleLayerToggle = useCallback(
    (_: DetectionStatus, next: DetectionStatus[]) => {
      setActiveLayers(next)
    },
    [],
  )

  const applyDecisionBatch = useCallback(
    async (decision: 'approved' | 'rejected') => {
      if (locked) {
        return
      }
      const pendingSuggestions = suggestions.filter(
        (item) => normaliseStatus(item.status) === 'pending',
      )
      if (pendingSuggestions.length === 0) {
        return
      }
      setMutationPending(true)
      try {
        for (const suggestion of pendingSuggestions) {
          await apiClient.decideOverlay(projectId, {
            suggestionId: suggestion.id,
            decision,
            decidedBy: 'Planner',
          })
        }
        await refreshSuggestions()
        await refreshAudit()
      } catch (err) {
        setError(
          err instanceof Error ? err.message : t('detection.decisionError'),
        )
      } finally {
        setMutationPending(false)
      }
    },
    [
      apiClient,
      locked,
      projectId,
      refreshAudit,
      refreshSuggestions,
      suggestions,
      t,
    ],
  )

  const handleApproveAll = useCallback(() => {
    void applyDecisionBatch('approved')
  }, [applyDecisionBatch])

  const handleRejectAll = useCallback(() => {
    void applyDecisionBatch('rejected')
  }, [applyDecisionBatch])

  const handleProvideMetric = useCallback(
    async (metricKey: string, value: number): Promise<boolean> => {
      if (!importSummary) {
        return false
      }
      if (!Number.isFinite(value) || value <= 0) {
        window.alert(t('common.errors.generic'))
        return false
      }
      setMutationPending(true)
      try {
        await apiClient.updateImportOverrides(importSummary.importId, {
          [metricKey]: value,
        })
        await apiClient.runOverlay(projectId)
        await refreshSuggestions()
        await fetchLatestImport()
        await refreshAudit()
        return true
      } catch (err) {
        setError(
          err instanceof Error ? err.message : t('detection.loadError'),
        )
        return false
      } finally {
        setMutationPending(false)
      }
    },
    [apiClient, fetchLatestImport, importSummary, projectId, refreshAudit, refreshSuggestions, t],
  )

  const handleExport = useCallback(
    async (format: string) => {
      if (pendingCount > 0) {
        return
      }
      setExporting(true)
      try {
        const lower = format.toLowerCase()
        const artifact = await apiClient.exportProject(projectId, {
          format: lower as 'dxf' | 'dwg' | 'ifc' | 'pdf',
          includeSource: activeLayers.includes('source'),
          includeApprovedOverlays: activeLayers.includes('approved'),
          includePendingOverlays: activeLayers.includes('pending'),
          includeRejectedOverlays: activeLayers.includes('rejected'),
        })
        if (artifact.fallback) {
          setError(t('detection.exportFallback'))
          return
        }
        if (typeof window !== 'undefined') {
          const urlFactory = window.URL
          if (typeof urlFactory.createObjectURL !== 'function') {
            return
          }
          const url = urlFactory.createObjectURL(artifact.blob)
          const anchor = document.createElement('a')
          anchor.href = url
          anchor.download = artifact.filename ?? `overlay.${lower}`
          document.body.appendChild(anchor)
          anchor.click()
          anchor.remove()
          if (typeof urlFactory.revokeObjectURL === 'function') {
            urlFactory.revokeObjectURL(url)
          }
        }
      } catch (err) {
        setError(
          err instanceof Error ? err.message : t('detection.exportError'),
        )
      } finally {
        setExporting(false)
      }
    },
    [activeLayers, apiClient, pendingCount, projectId, t],
  )

  return (
    <AppLayout title={t('detection.title')} subtitle={t('detection.subtitle')}>
      <div className="cad-detection__toolbar">
        <p>{t('detection.projectSummary', { id: projectId })}</p>
        {loadingSuggestions && <span>{t('common.loading')}</span>}
        {loadingImport && <span>{t('common.loading')}</span>}
      </div>

      {error && <p className="cad-detection__error">{error}</p>}

      <CadDetectionPreview
        units={visibleUnits}
        overlays={overlays}
        hints={hints}
        zoneCode={importSummary?.zoneCode ?? null}
        locked={locked}
        onProvideMetric={handleProvideMetric}
        provideMetricDisabled={mutationPending}
      />

      <div className="cad-detection__grid">
        <LayerTogglePanel
          activeLayers={activeLayers}
          onToggle={handleLayerToggle}
          disabled={mutationPending}
          hint={
            hiddenStatusLabels.length > 0
              ? t('detection.layerHint', {
                  statuses: hiddenStatusLabels.join(statusListSeparator),
                })
              : undefined
          }
        />
        <BulkReviewControls
          pendingCount={pendingCount}
          onApproveAll={handleApproveAll}
          onRejectAll={handleRejectAll}
          disabled={locked || mutationPending}
        />
        <ZoneLockControls locked={locked} onToggle={setLocked} />
        <ExportDialog
          onExport={(format) => {
            void handleExport(format)
          }}
          disabled={pendingCount > 0 || exporting || mutationPending}
          pendingCount={pendingCount}
        />
      </div>

      <AuditTimelinePanel events={auditEvents} loading={auditLoading} />
    </AppLayout>
  )
}

export default CadDetectionPage
