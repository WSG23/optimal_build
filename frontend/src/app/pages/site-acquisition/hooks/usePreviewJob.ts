/**
 * Hook for managing preview job state, polling, and metadata
 *
 * Handles:
 * - Preview job selection and status polling
 * - Preview layer metadata loading
 * - Layer visibility and focus controls
 * - Legend customization
 * - Preview refresh with detail level changes
 */

import { useCallback, useEffect, useMemo, useRef, useState } from 'react'
import {
  fetchPreviewJob,
  refreshPreviewJob,
  listPreviewJobs,
  type DeveloperPreviewJob,
  type DeveloperColorLegendEntry,
  type GeometryDetailLevel,
  type SiteAcquisitionResult,
} from '../../../../api/siteAcquisition'
import {
  normalisePreviewLayer,
  normaliseLegendEntry,
  type PreviewLayerMetadata,
  type PreviewLegendEntry,
} from '../previewMetadata'

// ============================================================================
// Types
// ============================================================================

export interface UsePreviewJobOptions {
  /** The captured property result (may be null before capture) */
  capturedProperty: SiteAcquisitionResult | null
}

export interface UsePreviewJobResult {
  // Preview job state
  previewJob: DeveloperPreviewJob | null
  setPreviewJob: React.Dispatch<React.SetStateAction<DeveloperPreviewJob | null>>
  previewDetailLevel: GeometryDetailLevel
  setPreviewDetailLevel: React.Dispatch<React.SetStateAction<GeometryDetailLevel>>
  isRefreshingPreview: boolean

  // Layer metadata
  previewLayerMetadata: PreviewLayerMetadata[]
  previewLayerVisibility: Record<string, boolean>
  previewFocusLayerId: string | null
  isPreviewMetadataLoading: boolean
  previewMetadataError: string | null
  hiddenLayerCount: number

  // Legend state
  legendEntries: PreviewLegendEntry[]
  setLegendEntries: React.Dispatch<React.SetStateAction<PreviewLegendEntry[]>>
  colorLegendEntries: PreviewLegendEntry[]
  legendPayloadForPreview: DeveloperColorLegendEntry[]
  legendHasPendingChanges: boolean

  // Derived values
  previewViewerMetadataUrl: string | null

  // Actions
  handleRefreshPreview: () => Promise<void>
  handleToggleLayerVisibility: (layerId: string) => void
  handleSoloPreviewLayer: (layerId: string) => void
  handleShowAllLayers: () => void
  handleFocusLayer: (layerId: string) => void
  handleResetLayerFocus: () => void
  handleLegendEntryChange: (
    assetType: string,
    field: 'label' | 'color' | 'description',
    value: string,
  ) => void
  handleLegendReset: () => void
}

// ============================================================================
// Hook Implementation
// ============================================================================

export function usePreviewJob({
  capturedProperty,
}: UsePreviewJobOptions): UsePreviewJobResult {
  // Preview job state
  const [previewJob, setPreviewJob] = useState<DeveloperPreviewJob | null>(null)
  const [previewDetailLevel, setPreviewDetailLevel] =
    useState<GeometryDetailLevel>('medium')
  const [isRefreshingPreview, setIsRefreshingPreview] = useState(false)

  // Layer metadata state
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

  // Legend state
  const [legendEntries, setLegendEntries] = useState<PreviewLegendEntry[]>([])
  const legendBaselineRef = useRef<PreviewLegendEntry[]>([])

  // Derived values
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

  const hiddenLayerCount = useMemo(
    () =>
      previewLayerMetadata.filter(
        (layer) => previewLayerVisibility[layer.id] === false,
      ).length,
    [previewLayerMetadata, previewLayerVisibility],
  )

  // ============================================================================
  // Effects
  // ============================================================================

  // Set preview job from captured property
  useEffect(() => {
    if (!capturedProperty?.previewJobs?.length) {
      setPreviewJob(null)
      return
    }
    setPreviewJob(capturedProperty.previewJobs[0])
  }, [capturedProperty?.previewJobs])

  // Fetch preview jobs if not included in captured property
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

  // Poll for preview job status updates
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

  // Sync detail level from preview job
  useEffect(() => {
    if (previewJob?.geometryDetailLevel) {
      setPreviewDetailLevel(previewJob.geometryDetailLevel)
    } else {
      setPreviewDetailLevel('medium')
    }
  }, [previewJob?.geometryDetailLevel])

  // Load legend entries from captured property
  useEffect(() => {
    if (!capturedProperty?.propertyId) {
      setLegendEntries([])
      legendBaselineRef.current = []
      return
    }
    const savedLegend = (capturedProperty.visualization?.colorLegend ?? []).map(
      (entry) => ({ ...entry }),
    )
    setLegendEntries(savedLegend)
  }, [capturedProperty?.propertyId, capturedProperty?.visualization?.colorLegend])

  // Load preview metadata
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
        const response = await fetch(previewViewerMetadataUrl!, {
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
        // Set baseline only on first load
        if (legendBaselineRef.current.length === 0) {
          legendBaselineRef.current = clonedLegend
        }
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

  // ============================================================================
  // Callbacks
  // ============================================================================

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

  // ============================================================================
  // Return
  // ============================================================================

  return {
    // Preview job state
    previewJob,
    setPreviewJob,
    previewDetailLevel,
    setPreviewDetailLevel,
    isRefreshingPreview,

    // Layer metadata
    previewLayerMetadata,
    previewLayerVisibility,
    previewFocusLayerId,
    isPreviewMetadataLoading,
    previewMetadataError,
    hiddenLayerCount,

    // Legend state
    legendEntries,
    setLegendEntries,
    colorLegendEntries,
    legendPayloadForPreview,
    legendHasPendingChanges,

    // Derived values
    previewViewerMetadataUrl,

    // Actions
    handleRefreshPreview,
    handleToggleLayerVisibility,
    handleSoloPreviewLayer,
    handleShowAllLayers,
    handleFocusLayer,
    handleResetLayerFocus,
    handleLegendEntryChange,
    handleLegendReset,
  }
}
