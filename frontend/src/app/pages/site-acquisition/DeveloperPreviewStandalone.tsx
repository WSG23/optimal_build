import { useEffect, useMemo, useState } from 'react'

import {
  DeveloperPreviewJob,
  listPreviewJobs,
  fetchPreviewJob,
} from '../../../api/siteAcquisition'
import { Preview3DViewer } from '../../components/site-acquisition/Preview3DViewer'
import { useRouterLocation } from '../../../router'

const PATH_PATTERN = /^\/agents\/developers\/([^/]+)\/preview\/?$/

export function DeveloperPreviewStandalone() {
  const { path } = useRouterLocation()
  const match = PATH_PATTERN.exec(path)
  const propertyId = match?.[1]
  const [previewJob, setPreviewJob] = useState<DeveloperPreviewJob | null>(null)
  const [isLoading, setIsLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

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
        </section>
      )}
    </div>
  )
}
