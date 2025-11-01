import type { ChangeEvent } from 'react'
import { useState } from 'react'
import { ViewportFrame } from '@/components/layout/ViewportFrame'
import Panel from '@/components/layout/Panel'
import { PanelBody } from '@/components/layout/PanelBody'
import { ZenPageHeader } from './components/ZenPageHeader'
import { TID } from '@/testing/testids'
import { ingestDataFile, type UploadStatus } from '@/services/uploadBridge'

export default function DataUploadPage() {
  const [status, setStatus] = useState<UploadStatus>({ kind: 'idle' })

  const handleFileChange = async (event: ChangeEvent<HTMLInputElement>) => {
    const [file] = event.target.files ?? []
    if (!file) {
      return
    }

    setStatus({ kind: 'selecting' })

    try {
      setStatus({ kind: 'uploading', filename: file.name })
      const result = await ingestDataFile(file)
      const runId = result && 'runId' in result ? result.runId : undefined
      setStatus({ kind: 'success', filename: file.name, runId })
    } catch (error) {
      const message = error instanceof Error ? error.message : 'Upload failed'
      setStatus({ kind: 'error', filename: file.name, message })
    } finally {
      event.target.value = ''
    }
  }

  return (
    <div className="bg-neutral-950 text-white" data-testid={TID.page.dataUpload}>
      <ViewportFrame className="flex h-full flex-col gap-6">
        <ZenPageHeader title="Data Upload & Enhancement" />
        <div
          className="grid flex-1 min-h-0 gap-6"
          style={{ gridTemplateColumns: 'minmax(0,1.4fr) minmax(0,1fr) minmax(0,1fr)' }}
        >
          <div className="min-h-0" style={{ gridColumn: '1', gridRow: '1 / span 2' }}>
            <Panel title="Upload Source File" className="h-full">
              <PanelBody className="flex h-full flex-col gap-4 p-4 text-sm">
                <p className="text-white/70">
                  Upload CSV or JSON access logs. Host-specific upload handlers continue to run through the bridge.
                </p>
                <label className="flex flex-col gap-2">
                  <span className="text-xs uppercase tracking-wide text-white/60">Select file</span>
                  <input
                    type="file"
                    data-testid={TID.control.uploadInput}
                    className="rounded border border-white/10 bg-neutral-900 px-3 py-2 text-white"
                    onChange={handleFileChange}
                  />
                </label>
                <div className="mt-2 min-h-[1.5rem] text-xs text-white/70">
                  {status.kind === 'idle' && <span>No file selected.</span>}
                  {status.kind === 'selecting' && <span>Preparing upload…</span>}
                  {status.kind === 'uploading' && (
                    <span>
                      Uploading <b>{status.filename}</b>…
                    </span>
                  )}
                  {status.kind === 'success' && (
                    <span>
                      ✅ Uploaded <b>{status.filename}</b>
                      {status.runId ? ` (runId: ${status.runId})` : ''}
                    </span>
                  )}
                  {status.kind === 'error' && (
                    <span className="text-red-300">
                      ❌ {status.message}
                      {status.filename ? ` – ${status.filename}` : ''}
                    </span>
                  )}
                </div>
                <div className="mt-auto grid gap-3 text-xs text-white/60">
                  <div className="rounded border border-white/10 bg-white/5 p-3">
                    <p className="font-semibold uppercase tracking-wide text-white/70">Pipeline</p>
                    <p>Extraction → Schema harmonization → Enhancement.</p>
                  </div>
                  <div className="rounded border border-white/10 bg-white/5 p-3">
                    <p className="font-semibold uppercase tracking-wide text-white/70">Host integration</p>
                    <p>Delegates to <code>window.__YOSAI_UPLOAD__</code> when present.</p>
                  </div>
                </div>
              </PanelBody>
            </Panel>
          </div>
          <div className="min-h-0" style={{ gridColumn: '2', gridRow: '1' }}>
            <Panel title="Schema Detection" className="h-full">
              <PanelBody className="flex h-full flex-col justify-between gap-4 p-4 text-sm text-white/70">
                <p>
                  Auto-map fields to canonical names. Unmapped columns surface for manual confirmation without blocking the
                  upload pipeline.
                </p>
                <div className="rounded border border-white/10 bg-white/5 p-3">
                  <p className="text-xs uppercase tracking-wide text-white/60">Last detected</p>
                  <p className="text-base text-white">Badge ID → visitor_id</p>
                </div>
              </PanelBody>
            </Panel>
          </div>
          <div className="min-h-0" style={{ gridColumn: '3', gridRow: '1' }}>
            <Panel title="Enhancement Summary" className="h-full">
              <PanelBody className="flex h-full flex-col justify-between gap-4 p-4 text-sm text-white/70">
                <p>Cross-reference uploads with threat intelligence, geo tags, and compliance obligations.</p>
                <ul className="space-y-2 text-xs">
                  <li>• Geo anomalies queued for review</li>
                  <li>• Policy lookups applied per facility</li>
                  <li>• Risk tags forwarded to Mission Control</li>
                </ul>
              </PanelBody>
            </Panel>
          </div>
          <div className="min-h-0" style={{ gridColumn: '2 / span 2', gridRow: '2' }}>
            <Panel title="Processing Timeline" className="h-full">
              <PanelBody className="flex h-full flex-col gap-4 p-4 text-sm text-white/70">
                <p>Track ingestion states from upload bridge through compliance validation.</p>
                <div className="grid grid-cols-3 gap-3 text-xs">
                  <div className="rounded border border-white/10 bg-white/5 p-3">
                    <p className="font-semibold text-white/80">Stage</p>
                    <p>Ingestion</p>
                  </div>
                  <div className="rounded border border-white/10 bg-white/5 p-3">
                    <p className="font-semibold text-white/80">Next</p>
                    <p>Schema review</p>
                  </div>
                  <div className="rounded border border-white/10 bg-white/5 p-3">
                    <p className="font-semibold text-white/80">SLA</p>
                    <p>&lt; 5 minutes</p>
                  </div>
                </div>
              </PanelBody>
            </Panel>
          </div>
        </div>
      </ViewportFrame>
    </div>
  )
}
