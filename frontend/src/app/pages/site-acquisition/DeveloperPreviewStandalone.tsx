import { useEffect, useMemo, useState } from 'react'

import {
  DeveloperPreviewJob,
  listPreviewJobs,
  fetchPreviewJob,
} from '../../../api/siteAcquisition'
import { Preview3DViewer } from '../../components/site-acquisition/Preview3DViewer'
import { useRouterLocation } from '../../../router'
import {
  PreviewLayerMetadata,
  PreviewLegendEntry,
  normalisePreviewLayer,
  normaliseLegendEntry,
} from './previewMetadata'

const PATH_PATTERN = /^\/agents\/developers\/([^/]+)\/preview\/?$/
const DETAIL_LABELS: Record<'simple' | 'medium', string> = {
  medium: 'Medium (octagonal, setbacks, floor lines)',
  simple: 'Simple (fast box geometry)',
}

function renderDetailLabel(level: DeveloperPreviewJob['geometryDetailLevel']): string {
  if (level && DETAIL_LABELS[level]) {
    return DETAIL_LABELS[level]
  }
  return DETAIL_LABELS.medium
}

function toTitleCase(value: string): string {
  return value
    .split(/[\s_-]+/)
    .filter(Boolean)
    .map((token) => token.charAt(0).toUpperCase() + token.slice(1).toLowerCase())
    .join(' ')
}

export function DeveloperPreviewStandalone() {
  const { path } = useRouterLocation()
  const match = PATH_PATTERN.exec(path)
  const propertyId = match?.[1]
  const [previewJob, setPreviewJob] = useState<DeveloperPreviewJob | null>(null)
  const [isLoading, setIsLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [metadataLoading, setMetadataLoading] = useState(false)
  const [metadataError, setMetadataError] = useState<string | null>(null)
  const [layerMetadata, setLayerMetadata] = useState<PreviewLayerMetadata[]>([])
  const [layerVisibility, setLayerVisibility] = useState<Record<string, boolean>>({})
  const [focusLayerId, setFocusLayerId] = useState<string | null>(null)
  const [inspectionLayerId, setInspectionLayerId] = useState<string | null>(null)
  const [legendEntries, setLegendEntries] = useState<PreviewLegendEntry[]>([])

  useEffect(() => {
    let cancelled = false

    async function loadPreview() {
      if (!propertyId) {
        setError('Missing property id in route.')
        return
      }

      setIsLoading(true)
      setError(null)

      try {
        const jobs = await listPreviewJobs(propertyId)
        if (cancelled) {
          return
        }

        const readyJob =
          jobs.find((job) => job.status.toLowerCase() === 'ready') ?? jobs[0] ?? null

        if (!readyJob) {
          setError('No preview jobs are available for this property yet.')
          setPreviewJob(null)
          return
        }

        if (readyJob.status.toLowerCase() === 'ready') {
          setPreviewJob(readyJob)
          return
        }

        const fresh = await fetchPreviewJob(readyJob.id)
        if (!cancelled) {
          setPreviewJob(fresh ?? readyJob)
        }
      } catch (loadError) {
        if (cancelled) {
          return
        }
        console.error('Failed to load preview job:', loadError)
        setError('Unable to load preview job for this property.')
        setPreviewJob(null)
      } finally {
        if (!cancelled) {
          setIsLoading(false)
        }
      }
    }

    loadPreview()

    return () => {
      cancelled = true
    }
  }, [propertyId])
  useEffect(() => {
    if (!previewJob?.metadataUrl) {
      setLayerMetadata([])
      setLegendEntries([])
      setLayerVisibility({})
      setFocusLayerId(null)
      setMetadataError(null)
      setMetadataLoading(false)
      return undefined
    }
    const controller = new AbortController()
    let cancelled = false
    async function loadMetadata() {
      setMetadataLoading(true)
      setMetadataError(null)
      try {
        // previewJob and metadataUrl are guaranteed non-null due to early return check above
        const response = await fetch(previewJob!.metadataUrl!, {
          signal: controller.signal,
          cache: 'reload',
        })
        if (!response.ok) {
          throw new Error(`Metadata fetch failed (${response.status})`)
        }
        const payload = (await response.json()) as PreviewMetadataPayload
        if (cancelled) {
          return
        }
        const layers = Array.isArray(payload.layers)
          ? payload.layers
              .map((layer) => normalisePreviewLayer(layer))
              .filter((layer): layer is PreviewLayerMetadata => layer !== null)
          : []
        setLayerMetadata(layers)
        const legend = Array.isArray(payload.color_legend)
          ? payload.color_legend
              .map((entry) => normaliseLegendEntry(entry))
              .filter((entry): entry is PreviewLegendEntry => entry !== null)
          : []
        setLegendEntries(legend)
        const nextVisibility = layers.reduce<Record<string, boolean>>((acc, layer) => {
          acc[layer.id] = true
          return acc
        }, {})
        setLayerVisibility(nextVisibility)
        setFocusLayerId(null)
      } catch (metaError) {
        if (cancelled || controller.signal.aborted) {
          return
        }
        console.error('Failed to load preview metadata:', metaError)
        setMetadataError(
          metaError instanceof Error ? metaError.message : 'Unable to load preview metadata.',
        )
        setLayerMetadata([])
        setLegendEntries([])
        setLayerVisibility({})
      } finally {
        if (!cancelled) {
          setMetadataLoading(false)
        }
      }
    }
    loadMetadata()
    return () => {
      cancelled = true
      controller.abort()
    }
  }, [
    previewJob,
    setLayerMetadata,
    setLegendEntries,
    setLayerVisibility,
    setFocusLayerId,
  ])

  useEffect(() => {
    if (layerMetadata.length === 0) {
      setInspectionLayerId(null)
      return
    }
    setInspectionLayerId((current) => {
      if (current && layerMetadata.some((layer) => layer.id === current)) {
        return current
      }
      return layerMetadata[0]?.id ?? null
    })
  }, [layerMetadata])

  const statusNotice = useMemo(() => {
    if (!previewJob) {
      return null
    }
    const status = previewJob.status.toLowerCase()
    if (status === 'ready') {
      return 'Preview render is ready.'
    }
    if (status === 'processing') {
      return 'Preview render is still processing – refresh this page or return later.'
    }
    if (status === 'queued') {
      return 'Preview render has been queued and will begin shortly.'
    }
    if (status === 'failed') {
      return previewJob.message ?? 'Preview render failed. Try re-running the job.'
    }
    if (status === 'expired') {
      return 'Preview render has expired. Trigger a new preview from the Site Acquisition page.'
    }
    return null
  }, [previewJob])

  const hiddenLayerCount = useMemo(
    () =>
      layerMetadata.filter((layer) => layerVisibility[layer.id] === false).length,
    [layerMetadata, layerVisibility],
  )
  const hasHiddenLayers = hiddenLayerCount > 0

  const inspectedLayer = useMemo(
    () => layerMetadata.find((layer) => layer.id === inspectionLayerId) ?? null,
    [inspectionLayerId, layerMetadata],
  )

  const handleToggleLayerVisibility = (layerId: string) => {
    setLayerVisibility((prev) => {
      const next = { ...prev }
      const currentVisible = next[layerId] !== false
      next[layerId] = !currentVisible
      return next
    })
  }

  const handleShowAllLayers = () => {
    const next = layerMetadata.reduce<Record<string, boolean>>((acc, layer) => {
      acc[layer.id] = true
      return acc
    }, {})
    setLayerVisibility(next)
    setFocusLayerId(null)
  }

  const handleSoloLayer = (layerId: string) => {
    const next = layerMetadata.reduce<Record<string, boolean>>((acc, layer) => {
      acc[layer.id] = layer.id === layerId
      return acc
    }, {})
    setLayerVisibility(next)
    setFocusLayerId(layerId)
  }

  const handleFocusLayer = (layerId: string) => {
    setFocusLayerId((current) => (current === layerId ? null : layerId))
  }

  const handleResetFocus = () => {
    setFocusLayerId(null)
  }

  const handleInspectLayer = (layerId: string) => {
    setInspectionLayerId(layerId)
  }

  if (!propertyId) {
    return (
      <div className="developer-preview-standalone">
        <h1>Developer preview</h1>
        <p className="developer-preview-standalone__error">
          Missing property identifier in the URL. Provide a valid property id and reload.
        </p>
      </div>
    )
  }

  return (
    <div className="developer-preview-standalone">
      <header className="developer-preview-standalone__header">
        <h1>Developer preview</h1>
        <p className="developer-preview-standalone__subtitle">
          Property ID: <code>{propertyId}</code>
        </p>
        <p className="developer-preview-standalone__help">
          This route is intended for manual QA of the Phase 2B 3D viewer. To refresh the render,
          use the “Refresh preview render” action on the Site Acquisition page.
        </p>
      </header>

      {isLoading && (
        <div className="developer-preview-standalone__status">Loading preview job…</div>
      )}

      {!isLoading && error && (
        <div className="developer-preview-standalone__error">
          {error}
          <div className="developer-preview-standalone__hint">
            Confirm that preview jobs exist for this property (via Site Acquisition or the preview
            CLI) before using this route.
          </div>
        </div>
      )}

      {!isLoading && !error && previewJob && (
        <section className="developer-preview-standalone__viewer">
          <div className="developer-preview-standalone__status-row">
            <span className={`developer-preview-standalone__status-pill status-${previewJob.status.toLowerCase()}`}>
              {previewJob.status.toUpperCase()}
            </span>
            {statusNotice && (
              <span className="developer-preview-standalone__status-note">{statusNotice}</span>
            )}
          </div>
         <Preview3DViewer
            previewUrl={previewJob.previewUrl}
            metadataUrl={previewJob.metadataUrl}
            status={previewJob.status}
            thumbnailUrl={previewJob.thumbnailUrl}
            layerVisibility={layerVisibility}
            focusLayerId={focusLayerId}
          />

          <dl className="developer-preview-standalone__details">
            <div>
              <dt>Preview job ID</dt>
              <dd>
                <code>{previewJob.id}</code>
              </dd>
            </div>
            <div>
              <dt>Scenario</dt>
              <dd>{previewJob.scenario}</dd>
            </div>
            <div>
              <dt>Geometry detail</dt>
              <dd>{renderDetailLabel(previewJob.geometryDetailLevel)}</dd>
            </div>
            <div>
              <dt>Requested at</dt>
              <dd>{previewJob.requestedAt ? new Date(previewJob.requestedAt).toLocaleString() : '—'}</dd>
            </div>
            <div>
              <dt>Finished at</dt>
              <dd>{previewJob.finishedAt ? new Date(previewJob.finishedAt).toLocaleString() : '—'}</dd>
            </div>
            <div>
              <dt>Preview asset</dt>
              <dd>
                {previewJob.previewUrl ? (
                  <a href={previewJob.previewUrl} target="_blank" rel="noreferrer">
                    {previewJob.previewUrl}
                  </a>
                ) : (
                  'Not available yet'
                )}
              </dd>
            </div>
            <div>
              <dt>Metadata</dt>
              <dd>
                {previewJob.metadataUrl ? (
                  <a href={previewJob.metadataUrl} target="_blank" rel="noreferrer">
                    {previewJob.metadataUrl}
                  </a>
                ) : (
                  'Not available yet'
                )}
              </dd>
            </div>
            <div>
              <dt>Thumbnail</dt>
              <dd>
                {previewJob.thumbnailUrl ? (
                  <a href={previewJob.thumbnailUrl} target="_blank" rel="noreferrer">
                    {previewJob.thumbnailUrl}
                  </a>
                ) : (
                  'Not available yet'
                )}
              </dd>
            </div>
          </dl>

          <section className="developer-preview-standalone__layers">
            <div className="developer-preview-standalone__layers-header">
              <div>
                <h2>Layer breakdown</h2>
                <p>
                  Visual detail for the rendered massing. Each layer combines asset allocation,
                  estimated floors, and colour legend entries.
                </p>
              </div>
              <span className="developer-preview-standalone__layers-count">
                {layerMetadata.length} layers
              </span>
            </div>
            <div className="developer-preview-standalone__layers-controls">
              <button
                type="button"
                className="developer-preview-standalone__layers-button"
                onClick={handleShowAllLayers}
                disabled={!hasHiddenLayers && !focusLayerId}
              >
                Show all layers
              </button>
              <button
                type="button"
                className="developer-preview-standalone__layers-button"
                onClick={handleResetFocus}
                disabled={!focusLayerId}
              >
                Reset view
              </button>
            </div>
            {metadataLoading && (
              <p className="developer-preview-standalone__layers-status">Loading preview metadata…</p>
            )}
            {!metadataLoading && metadataError && (
              <p className="developer-preview-standalone__layers-error">{metadataError}</p>
            )}
            {!metadataLoading && !metadataError && layerMetadata.length === 0 && (
              <p className="developer-preview-standalone__layers-empty">
                Layer metrics will appear once the preview metadata is available.
              </p>
            )}
            {layerMetadata.length > 0 && (
              <div className="developer-preview-standalone__layers-table-wrapper">
                <table className="developer-preview-standalone__layers-table">
                  <thead>
                    <tr>
                      <th scope="col">Layer</th>
                      <th scope="col">Allocation</th>
                      <th scope="col">GFA (sqm)</th>
                      <th scope="col">NIA (sqm)</th>
                      <th scope="col">Est. height (m)</th>
                      <th scope="col">Est. floors</th>
                      <th scope="col">
                        <span className="sr-only">Layer controls</span>
                      </th>
                    </tr>
                  </thead>
                  <tbody>
                    {layerMetadata.map((layer) => (
                      <tr key={layer.id}>
                        <th scope="row">
                          <div className="developer-preview-standalone__layer-name">
                            <span
                              className="developer-preview-standalone__layer-swatch"
                              style={{ background: layer.color }}
                              aria-hidden="true"
                            />
                            <span>{toTitleCase(layer.name)}</span>
                          </div>
                        </th>
                        <td>{formatPercent(layer.metrics.allocationPct)}</td>
                        <td>{formatNumber(layer.metrics.gfaSqm)}</td>
                        <td>{formatNumber(layer.metrics.niaSqm)}</td>
                        <td>{formatNumber(layer.metrics.heightM)}</td>
                        <td>{formatNumber(layer.metrics.floors, 0)}</td>
                        <td className="developer-preview-standalone__layer-actions">
                          <button
                            type="button"
                            className="developer-preview-standalone__layer-action"
                            onClick={() => handleToggleLayerVisibility(layer.id)}
                          >
                            {layerVisibility[layer.id] === false ? 'Show' : 'Hide'}
                          </button>
                          <button
                            type="button"
                            className="developer-preview-standalone__layer-action"
                            onClick={() => handleSoloLayer(layer.id)}
                          >
                            Solo
                          </button>
                          <button
                            type="button"
                            className={`developer-preview-standalone__layer-action${
                              focusLayerId === layer.id ? ' is-active' : ''
                            }`}
                            onClick={() => handleFocusLayer(layer.id)}
                          >
                            {focusLayerId === layer.id ? 'Focused' : 'Zoom'}
                          </button>
                          <button
                            type="button"
                            className={`developer-preview-standalone__layer-action${
                              inspectionLayerId === layer.id ? ' is-active' : ''
                            }`}
                            onClick={() => handleInspectLayer(layer.id)}
                            aria-pressed={inspectionLayerId === layer.id}
                          >
                            Inspect
                          </button>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
            {inspectedLayer && (
              <div className="developer-preview-standalone__inspection">
                <div className="developer-preview-standalone__inspection-header">
                  <div className="developer-preview-standalone__inspection-title">
                    <span
                      className="developer-preview-standalone__inspection-swatch"
                      style={{ background: inspectedLayer.color }}
                      aria-hidden="true"
                    />
                    <div>
                      <p className="developer-preview-standalone__inspection-label">Inspecting</p>
                      <h3>{toTitleCase(inspectedLayer.name)}</h3>
                    </div>
                  </div>
                  <label className="developer-preview-standalone__inspection-select">
                    <span>Layer</span>
                    <select
                      value={inspectionLayerId ?? ''}
                      onChange={(event) => handleInspectLayer(event.target.value)}
                    >
                      {layerMetadata.map((layer) => (
                        <option key={layer.id} value={layer.id}>
                          {toTitleCase(layer.name)}
                        </option>
                      ))}
                    </select>
                  </label>
                </div>
                <div className="developer-preview-standalone__inspection-grid">
                  <div>
                    <dt>Detail level</dt>
                    <dd>{inspectedLayer.geometry?.detailLevel ?? '—'}</dd>
                  </div>
                  <div>
                    <dt>Base elevation</dt>
                    <dd>{formatMeters(inspectedLayer.geometry?.baseElevationM)}</dd>
                  </div>
                  <div>
                    <dt>Top elevation</dt>
                    <dd>{formatMeters(inspectedLayer.geometry?.topElevationM)}</dd>
                  </div>
                  <div>
                    <dt>Preview height</dt>
                    <dd>{formatMeters(inspectedLayer.geometry?.previewHeightM)}</dd>
                  </div>
                  <div>
                    <dt>Floors (est.)</dt>
                    <dd>{formatNumber(inspectedLayer.metrics.floors, 0)}</dd>
                  </div>
                  <div>
                    <dt>Allocation</dt>
                    <dd>{formatPercent(inspectedLayer.metrics.allocationPct)}</dd>
                  </div>
                </div>
                <div className="developer-preview-standalone__inspection-footprint">
                  <h4>Footprint metrics</h4>
                  <div className="developer-preview-standalone__inspection-grid">
                    <div>
                      <dt>Base area</dt>
                      <dd>{formatArea(inspectedLayer.geometry?.footprintAreaSqm)}</dd>
                    </div>
                    <div>
                      <dt>Base perimeter</dt>
                      <dd>{formatMeters(inspectedLayer.geometry?.footprintPerimeterM)}</dd>
                    </div>
                    <div>
                      <dt>Top area</dt>
                      <dd>{formatArea(inspectedLayer.geometry?.topFootprintAreaSqm)}</dd>
                    </div>
                    <div>
                      <dt>Top perimeter</dt>
                      <dd>{formatMeters(inspectedLayer.geometry?.topFootprintPerimeterM)}</dd>
                    </div>
                  </div>
                </div>
                {inspectedLayer.geometry?.floorLineHeights.length ? (
                  <div className="developer-preview-standalone__inspection-floorlines">
                    <h4>Floor line heights</h4>
                    <p>
                      {summariseFloorLines(inspectedLayer.geometry.floorLineHeights)}
                    </p>
                  </div>
                ) : null}
                <div className="developer-preview-standalone__inspection-controls">
                  <button
                    type="button"
                    onClick={() => handleSoloLayer(inspectedLayer.id)}
                    className="developer-preview-standalone__layers-button"
                  >
                    Solo layer
                  </button>
                  <button
                    type="button"
                    onClick={() => handleFocusLayer(inspectedLayer.id)}
                    className={`developer-preview-standalone__layers-button${
                      focusLayerId === inspectedLayer.id ? ' is-active' : ''
                    }`}
                  >
                    {focusLayerId === inspectedLayer.id ? 'Focused' : 'Zoom to layer'}
                  </button>
                </div>
              </div>
            )}
            {legendEntries.length > 0 && (
              <div className="developer-preview-standalone__legend">
                <h3>Colour legend</h3>
                <div className="developer-preview-standalone__legend-grid">
                  {legendEntries.map((entry) => (
                    <div key={entry.assetType} className="developer-preview-standalone__legend-item">
                      <span
                        className="developer-preview-standalone__legend-swatch"
                        style={{ background: entry.color }}
                        aria-hidden="true"
                      />
                      <div>
                        <p className="developer-preview-standalone__legend-label">{entry.label}</p>
                        {entry.description ? (
                          <p className="developer-preview-standalone__legend-description">
                            {entry.description}
                          </p>
                        ) : null}
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            )}
          </section>
        </section>
      )}
    </div>
  )
}

type PreviewMetadataPayload = {
  layers?: Array<Record<string, unknown>>
  color_legend?: Array<Record<string, unknown>>
}

function formatPercent(value: number | null | undefined): string {
  if (value === null || value === undefined) {
    return '—'
  }
  return `${value.toFixed(1)}%`
}

function formatNumber(value: number | null | undefined, fractionDigits = 1): string {
  if (value === null || value === undefined) {
    return '—'
  }
  return new Intl.NumberFormat(undefined, {
    minimumFractionDigits: fractionDigits,
    maximumFractionDigits: fractionDigits,
  }).format(value)
}

function formatMeters(value: number | null | undefined, fractionDigits = 1): string {
  if (value === null || value === undefined) {
    return '—'
  }
  return `${formatNumber(value, fractionDigits)} m`
}

function formatArea(value: number | null | undefined): string {
  if (value === null || value === undefined) {
    return '—'
  }
  return `${formatNumber(value, 1)} sqm`
}

const FLOOR_LINE_PREVIEW_COUNT = 5

function summariseFloorLines(heights: number[]): string {
  if (heights.length === 0) {
    return 'No floor lines provided.'
  }
  const sorted = [...heights].sort((a, b) => a - b)
  const preview = sorted.slice(0, FLOOR_LINE_PREVIEW_COUNT).map((height) => formatMeters(height))
  const remaining = sorted.length - preview.length
  return remaining > 0
    ? `${preview.join(', ')} … (+${remaining} more)`
    : preview.join(', ')
}
