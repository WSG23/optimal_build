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

export function CadDetectionPage() {
  const apiClient = useApiClient()
  const { t } = useTranslation()
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
  const [activeLayers, setActiveLayers] = useState<DetectionStatus[]>([
    'source',
    'pending',
    'approved',
    'rejected',
  ])

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

  const overlays = useMemo(
    () => suggestions.map((item) => item.code),
    [suggestions],
  )
  const hints = useMemo(
    () =>
      suggestions
        .map((item) => item.rationale)
        .filter((value): value is string => Boolean(value)),
    [suggestions],
  )

  const overrides = importSummary?.overrides ?? {}
  const units = useMemo<DetectedUnit[]>(
    () =>
      suggestions.map((suggestion, index) => {
        const missingMetricKey =
          typeof (suggestion.enginePayload as { missing_metric?: unknown })
            ?.missing_metric === 'string'
            ? ((suggestion.enginePayload as { missing_metric?: string }).missing_metric ?? null)
            : null
        const overrideValue =
          missingMetricKey && typeof overrides[missingMetricKey] === 'number'
            ? overrides[missingMetricKey]
            : null
        return {
          id: suggestion.id.toString(),
          floor: index + 1,
          unitLabel: suggestion.title || suggestion.code,
          areaSqm: deriveAreaSqm(suggestion),
          status: normaliseStatus(suggestion.status),
          missingMetricKey: missingMetricKey ?? undefined,
          overrideValue,
        }
      }),
    [overrides, suggestions],
  )

  const visibleUnits = useMemo(
    () => units.filter((unit) => activeLayers.includes(unit.status)),
    [units, activeLayers],
  )

  const pendingCount = useMemo(
    () => units.filter((unit) => unit.status === 'pending').length,
    [units],
  )

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

  const metricLabels = useMemo(
    () => ({
      front_setback_m: t('detection.override.prompts.frontSetback'),
      max_height_m: t('detection.override.prompts.maxHeight'),
      site_area_sqm: t('detection.override.prompts.siteArea'),
      gross_floor_area_sqm: t('detection.override.prompts.grossFloorArea'),
    }),
    [t],
  )

  const handleProvideMetric = useCallback(
    async (metricKey: string, currentValue?: number | null) => {
      if (!importSummary) {
        return
      }
      const label = metricLabels[metricKey as keyof typeof metricLabels] ?? metricKey
      const input = window.prompt(
        t('detection.override.prompt', { metric: label }),
        currentValue != null ? currentValue.toString() : '',
      )
      if (input === null) {
        return
      }
      const parsed = Number.parseFloat(input)
      if (!Number.isFinite(parsed) || parsed <= 0) {
        window.alert(t('common.errors.generic'))
        return
      }
      setMutationPending(true)
      try {
        await apiClient.updateImportOverrides(importSummary.importId, {
          [metricKey]: parsed,
        })
        await apiClient.runOverlay(projectId)
        await refreshSuggestions()
        await fetchLatestImport()
        await refreshAudit()
      } catch (err) {
        setError(
          err instanceof Error ? err.message : t('detection.loadError'),
        )
      } finally {
        setMutationPending(false)
      }
    },
    [
      apiClient,
      fetchLatestImport,
      importSummary,
      metricLabels,
      projectId,
      refreshAudit,
      refreshSuggestions,
      t,
    ],
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
        />
      </div>

      <AuditTimelinePanel events={auditEvents} loading={auditLoading} />
    </AppLayout>
  )
}

export default CadDetectionPage
