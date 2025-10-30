import { useCallback, useEffect, useMemo, useState } from 'react'

import type {
  AuditEvent,
  CadImportSummary,
  OverlaySuggestion,
} from '../api/client'
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

import {
  DEFAULT_VISIBLE_SEVERITIES,
  OverlaySeverity,
  SeverityBuckets,
  aggregateOverlaySuggestions,
  calculateSeverityPercentages,
  countSeverityBuckets,
  deriveAreaSqm,
  filterLatestUnitSpaceSuggestions,
  normaliseStatus,
} from './cadDetectionHelpers'

const DEFAULT_PROJECT_ID = 5821
const ALL_LAYERS: DetectionStatus[] = [
  'source',
  'pending',
  'approved',
  'rejected',
]
const DEFAULT_LAYERS: DetectionStatus[] = ['source', 'pending']

const STATUS_LABEL_KEYS: Record<DetectionStatus, string> = {
  source: 'controls.source',
  pending: 'controls.pending',
  approved: 'controls.approved',
  rejected: 'controls.rejected',
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
  const [importSummary, setImportSummary] = useState<CadImportSummary | null>(
    null,
  )
  const [loadingImport, setLoadingImport] = useState(false)
  const [activeLayers, setActiveLayers] = useState<DetectionStatus[]>([
    ...DEFAULT_LAYERS,
  ])
  const [activeSeverities, setActiveSeverities] = useState<OverlaySeverity[]>([
    ...DEFAULT_VISIBLE_SEVERITIES,
  ])
  const [savedSeverities, setSavedSeverities] = useState<
    OverlaySeverity[] | null
  >(null)
  const [customSeverityPreset, setCustomSeverityPreset] = useState<
    OverlaySeverity[] | null
  >(null)

  useEffect(() => {
    const handler = (event: KeyboardEvent) => {
      if (event.shiftKey && (event.key === 'H' || event.key === 'h')) {
        event.preventDefault()
        setActiveSeverities((current) => {
          const isFocused = savedSeverities !== null
          if (isFocused) {
            const restore = savedSeverities ?? DEFAULT_VISIBLE_SEVERITIES
            setSavedSeverities(null)
            return [...restore]
          }
          setSavedSeverities(current)
          return ['high', 'medium']
        })
      }
    }

    window.addEventListener('keydown', handler)
    return () => {
      window.removeEventListener('keydown', handler)
    }
  }, [savedSeverities])

  const fetchLatestImport = useCallback(async () => {
    setLoadingImport(true)
    try {
      const summary = await apiClient.getLatestImport(projectId)
      setImportSummary(summary)
    } catch (err) {
      setImportSummary(null)
      setError(
        (prev) =>
          prev ??
          (err instanceof Error ? err.message : t('detection.loadError')),
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

  const filteredByStatus = useMemo(
    () =>
      aggregatedSuggestions.filter((item) =>
        activeLayers.includes(item.status),
      ),
    [activeLayers, aggregatedSuggestions],
  )

  const filteredBySeverity = useMemo(() => {
    return filteredByStatus.filter((item) => {
      const severityKey: OverlaySeverity =
        item.severity === 'high' ||
        item.severity === 'medium' ||
        item.severity === 'low'
          ? item.severity
          : 'none'
      return activeSeverities.includes(severityKey)
    })
  }, [activeSeverities, filteredByStatus])

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

  const overlays = useMemo(
    () =>
      filteredBySeverity.map((item) => {
        const metricLabel =
          item.missingMetricKey &&
          metricLabels[item.missingMetricKey as keyof typeof metricLabels]
            ? metricLabels[item.missingMetricKey as keyof typeof metricLabels]
            : (item.missingMetricKey ?? null)
        const baseLabel =
          metricLabel ??
          item.suggestion.title ??
          item.suggestion.code ??
          item.key
        const severityKey: OverlaySeverity =
          item.severity === 'high' ||
          item.severity === 'medium' ||
          item.severity === 'low'
            ? item.severity
            : 'none'
        const severityLabel =
          severityKey === 'none'
            ? t('detection.severity.none')
            : t(`detection.severity.${severityKey}`)
        return {
          key: item.key,
          title: baseLabel,
          count: item.count,
          statusLabel: t(STATUS_LABEL_KEYS[item.status]),
          severity: severityKey,
          severityLabel,
        }
      }),
    [filteredBySeverity, metricLabels, t],
  )

  const severitySummary = useMemo(
    () => countSeverityBuckets(aggregatedSuggestions, activeLayers),
    [activeLayers, aggregatedSuggestions],
  )

  const isSeverityFiltered = useMemo(
    () => activeSeverities.length !== DEFAULT_VISIBLE_SEVERITIES.length,
    [activeSeverities],
  )

  const severityPercentages = useMemo(
    () => calculateSeverityPercentages(severitySummary),
    [severitySummary],
  )

  const hiddenSeverityCounts = useMemo(() => {
    return DEFAULT_VISIBLE_SEVERITIES.reduce((acc, severity) => {
      acc[severity] = activeSeverities.includes(severity)
        ? 0
        : severitySummary[severity]
      return acc
    }, {} as SeverityBuckets)
  }, [activeSeverities, severitySummary])

  const hiddenPendingCount = useMemo(() => {
    const totalPending = aggregatedSuggestions.filter(
      (item) => item.status === 'pending',
    )
    const visiblePending = filteredBySeverity.filter(
      (item) => item.status === 'pending',
    )
    return totalPending.length - visiblePending.length
  }, [aggregatedSuggestions, filteredBySeverity])

  const hiddenByStatus = useMemo(
    () => aggregatedSuggestions.length > 0 && filteredByStatus.length === 0,
    [aggregatedSuggestions.length, filteredByStatus.length],
  )

  const hiddenBySeverity = useMemo(
    () =>
      !hiddenByStatus &&
      filteredByStatus.length > 0 &&
      filteredBySeverity.length === 0,
    [hiddenByStatus, filteredByStatus.length, filteredBySeverity.length],
  )

  const filtersHideAll = hiddenByStatus || hiddenBySeverity

  const severityFilterSummary = useMemo(() => {
    if (activeSeverities.length === DEFAULT_VISIBLE_SEVERITIES.length) {
      return t('detection.severitySummary.filters.all')
    }
    const labels = activeSeverities.map((severity) =>
      severity === 'none'
        ? t('detection.severitySummary.info')
        : t(`detection.severitySummary.${severity}`),
    )
    return t('detection.severitySummary.filters.active', {
      list: labels.join(', '),
    })
  }, [activeSeverities, t])

  const hints = useMemo(
    () =>
      filteredBySeverity
        .filter((item) => Boolean(item.suggestion.rationale))
        .map((item) => ({
          key: item.key,
          text: item.suggestion.rationale as string,
        })),
    [filteredBySeverity],
  )

  const units = useMemo<DetectedUnit[]>(() => {
    const overrides = importSummary?.overrides ?? {}
    return filteredBySeverity.map((entry, index) => {
      const missingMetricKey = entry.missingMetricKey ?? null
      const overrideValue =
        missingMetricKey && typeof overrides[missingMetricKey] === 'number'
          ? overrides[missingMetricKey]
          : null
      const metricLabel =
        missingMetricKey &&
        metricLabels[missingMetricKey as keyof typeof metricLabels]
          ? metricLabels[missingMetricKey as keyof typeof metricLabels]
          : (missingMetricKey ?? undefined)
      const severityKey: OverlaySeverity =
        entry.severity === 'high' ||
        entry.severity === 'medium' ||
        entry.severity === 'low'
          ? entry.severity
          : 'none'
      const baseLabel =
        entry.suggestion.title || entry.suggestion.code || entry.key
      const label =
        entry.count > 1
          ? `${baseLabel} ${t('detection.countSuffix', { count: entry.count })}`
          : baseLabel
      const areaSqm =
        entry.totalArea > 0 ? entry.totalArea : deriveAreaSqm(entry.suggestion)
      const overrideDisplay =
        missingMetricKey && overrideValue != null
          ? `${metricLabel ?? missingMetricKey}: ${new Intl.NumberFormat(
              undefined,
              {
                maximumFractionDigits: 2,
                minimumFractionDigits: Number.isInteger(overrideValue) ? 0 : 2,
              },
            ).format(overrideValue)}`
          : undefined
      return {
        id: entry.key,
        floor: index + 1,
        unitLabel: label,
        areaSqm,
        status: entry.status,
        severity: severityKey,
        missingMetricKey: missingMetricKey ?? undefined,
        overrideValue,
        overrideDisplay,
        metricLabel,
      }
    })
  }, [filteredBySeverity, importSummary?.overrides, metricLabels, t])

  const visibleUnits = useMemo(() => units, [units])

  const pendingCount = useMemo(
    () => filteredByStatus.filter((entry) => entry.status === 'pending').length,
    [filteredByStatus],
  )

  const statusCounts = useMemo(() => {
    const counts: Record<DetectionStatus, number> = {
      source: 0,
      pending: 0,
      approved: 0,
      rejected: 0,
    }
    filteredByStatus.forEach((entry) => {
      counts[entry.status] += 1
    })
    return counts
  }, [filteredByStatus])

  const totalStatusCounts = useMemo(() => {
    const counts: Record<DetectionStatus, number> = {
      source: 0,
      pending: 0,
      approved: 0,
      rejected: 0,
    }
    aggregatedSuggestions.forEach((entry) => {
      counts[entry.status] += 1
    })
    return counts
  }, [aggregatedSuggestions])

  const hiddenStatusCounts = useMemo(() => {
    const counts: Record<DetectionStatus, number> = {
      source: Math.max(0, totalStatusCounts.source - statusCounts.source),
      pending: Math.max(0, totalStatusCounts.pending - statusCounts.pending),
      approved: Math.max(0, totalStatusCounts.approved - statusCounts.approved),
      rejected: Math.max(0, totalStatusCounts.rejected - statusCounts.rejected),
    }
    return counts
  }, [statusCounts, totalStatusCounts])

  const hasSeverityPreset = customSeverityPreset !== null

  const canApplySeverityPreset = useMemo(() => {
    if (!customSeverityPreset) {
      return false
    }
    if (customSeverityPreset.length !== activeSeverities.length) {
      return true
    }
    const set = new Set(customSeverityPreset)
    return activeSeverities.some((severity) => !set.has(severity))
  }, [activeSeverities, customSeverityPreset])

  const statusFilterSummary = useMemo(() => {
    const pendingOnly = activeLayers.length === 1 && activeLayers[0] === 'pending'
    const isAll =
      activeLayers.length === ALL_LAYERS.length &&
      ALL_LAYERS.every((status) => activeLayers.includes(status))
    if (isAll) {
      return t('detection.statusFilters.pendingOnly')
    }
    if (pendingOnly) {
      return t('detection.statusFilters.all')
    }
    const approved = statusCounts.approved
    const rejected = statusCounts.rejected
    return `${t('detection.statusFilters.approvedCount', { count: approved })} · ${t('detection.statusFilters.rejectedCount', { count: rejected })}`
  }, [activeLayers, statusCounts, t])

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

  const handleSeverityToggle = useCallback((severity: OverlaySeverity) => {
    setActiveSeverities((current) => {
      if (current.includes(severity)) {
        if (current.length === 1) {
          return current
        }
        return current.filter((value) => value !== severity)
      }
      return [...current, severity]
    })
  }, [])

  const handleSeverityReset = useCallback(() => {
    setActiveSeverities([...DEFAULT_VISIBLE_SEVERITIES])
    setSavedSeverities(null)
  }, [])

  const handleLayerReset = useCallback(() => {
    setActiveLayers([...DEFAULT_LAYERS])
  }, [])

  const handleResetAllFilters = useCallback(() => {
    setActiveLayers([...ALL_LAYERS])
    setActiveSeverities([...DEFAULT_VISIBLE_SEVERITIES])
    setSavedSeverities(null)
    setCustomSeverityPreset(null)
  }, [])

  const handleSaveSeverityPreset = useCallback(() => {
    setCustomSeverityPreset([...activeSeverities])
  }, [activeSeverities])

  const handleApplySeverityPreset = useCallback(() => {
    if (customSeverityPreset) {
      setActiveSeverities([...customSeverityPreset])
    }
  }, [customSeverityPreset])

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
        setError(err instanceof Error ? err.message : t('detection.loadError'))
        return false
      } finally {
        setMutationPending(false)
      }
    },
    [
      apiClient,
      fetchLatestImport,
      importSummary,
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
        <button
          type="button"
          className="cad-detection__filters-pill cad-detection__filters-pill--clickable"
          onClick={() => {
            setActiveSeverities((current) => {
              const isFocused = savedSeverities !== null
              if (isFocused) {
                const restore = savedSeverities ?? DEFAULT_VISIBLE_SEVERITIES
                setSavedSeverities(null)
                return [...restore]
              }
              setSavedSeverities(current)
              return ['high', 'medium']
            })
          }}
        >
          {savedSeverities === null
            ? t('detection.severitySummary.toolbar.focus')
            : t('detection.severitySummary.toolbar.restore')}
        </button>
        <button
          type="button"
          className="cad-detection__filters-pill cad-detection__filters-pill--clickable"
          onClick={handleResetAllFilters}
        >
          {t('detection.filtersBanner.resetAll')}
        </button>
        <span
          className="cad-detection__filters-pill"
          title={severityFilterSummary}
        >
          {severityFilterSummary}
        </span>
        <button
          type="button"
          className="cad-detection__filters-pill cad-detection__filters-pill--clickable"
          onClick={() => {
            setActiveLayers((current) => {
              const pendingOnly = current.length === 1 && current[0] === 'pending'
              const isAll =
                current.length === ALL_LAYERS.length &&
                ALL_LAYERS.every((status) => current.includes(status))
              if (pendingOnly) {
                return [...ALL_LAYERS]
              }
              if (isAll) {
                return ['pending']
              }
              return [...ALL_LAYERS]
            })
          }}
        >
          {statusFilterSummary}
        </button>
        <span className="cad-detection__shortcut-hint">
          {t('detection.severitySummary.toolbar.shortcut')}
        </span>
      </div>

      {filtersHideAll && (
        <div className="cad-detection__filter-banner">
          <strong>{t('detection.filtersBanner.title')}</strong>
          <div className="cad-detection__filter-banner-text">
            {hiddenByStatus && (
              <span>{t('detection.filtersBanner.status')}</span>
            )}
            {hiddenBySeverity && (
              <span>{t('detection.filtersBanner.severity')}</span>
            )}
          </div>
          <div className="cad-detection__filter-banner-actions">
            {hiddenByStatus && (
              <button type="button" onClick={handleLayerReset}>
                {t('detection.filtersBanner.resetStatus')}
              </button>
            )}
            {hiddenBySeverity && (
              <button type="button" onClick={handleSeverityReset}>
                {t('detection.filtersBanner.resetSeverity')}
              </button>
            )}
            <button type="button" onClick={handleResetAllFilters}>
              {t('detection.filtersBanner.resetAll')}
            </button>
          </div>
        </div>
      )}

      {error && <p className="cad-detection__error">{error}</p>}

      <CadDetectionPreview
        units={visibleUnits}
        overlays={overlays}
        hints={hints}
        severitySummary={severitySummary}
        severityPercentages={severityPercentages}
        hiddenSeverityCounts={hiddenSeverityCounts}
        statusCounts={statusCounts}
        hiddenStatusCounts={hiddenStatusCounts}
        activeStatuses={activeLayers}
        activeSeverities={activeSeverities}
        onToggleSeverity={handleSeverityToggle}
        onResetSeverity={handleSeverityReset}
        onSaveSeverityPreset={handleSaveSeverityPreset}
        onApplySeverityPreset={handleApplySeverityPreset}
        hasSeverityPreset={hasSeverityPreset}
        canApplySeverityPreset={canApplySeverityPreset}
        isSeverityFiltered={isSeverityFiltered}
        hiddenPendingCount={hiddenPendingCount}
        severityFilterSummary={severityFilterSummary}
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
