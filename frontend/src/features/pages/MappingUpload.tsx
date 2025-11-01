import type { ChangeEvent } from 'react'
import { useState } from 'react'
import { ViewportFrame } from '@/components/layout/ViewportFrame'
import Panel from '@/components/layout/Panel'
import { PanelBody } from '@/components/layout/PanelBody'
import { ZenPageHeader } from './components/ZenPageHeader'
import { TID } from '@/testing/testids'
import { ingestBlueprint, type UploadStatus } from '@/services/uploadBridge'

export default function MappingUploadPage() {
  const [status, setStatus] = useState<UploadStatus>({ kind: 'idle' })

  const handleFileChange = async (event: ChangeEvent<HTMLInputElement>) => {
    const [file] = event.target.files ?? []
    if (!file) {
      return
    }

    setStatus({ kind: 'selecting' })

    try {
      setStatus({ kind: 'uploading', filename: file.name })
      const result = await ingestBlueprint(file)
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
    <div className="bg-neutral-950 text-white" data-testid={TID.page.mappingUpload}>
      <ViewportFrame className="flex h-full flex-col gap-6">
        <ZenPageHeader title="Mapping Upload" />
        <div
          className="grid flex-1 min-h-0 gap-6"
          style={{ gridTemplateColumns: 'minmax(0,1.4fr) minmax(0,1fr) minmax(0,1fr)' }}
        >
          <div className="min-h-0" style={{ gridColumn: '1', gridRow: '1 / span 2' }}>
            <Panel title="Upload Blueprint" className="h-full">
              <PanelBody className="flex h-full flex-col gap-4 p-4 text-sm">
                <p className="text-white/70">
                  Upload SVG, DXF, DWG, or PNG schematics. When a host blueprint ingestor is registered it runs through the
                  shared upload bridge.
                </p>
                <label className="flex flex-col gap-2">
                  <span className="text-xs uppercase tracking-wide text-white/60">Select blueprint</span>
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
                    <p className="font-semibold uppercase tracking-wide text-white/70">Calibration</p>
                    <p>Scale + door alignment steps remain controlled by the host blueprint module.</p>
                  </div>
                  <div className="rounded border border-white/10 bg-white/5 p-3">
                    <p className="font-semibold uppercase tracking-wide text-white/70">Outputs</p>
                    <p>Zones, rooms, and door topology sync directly to Mission Control.</p>
                  </div>
                </div>
              </PanelBody>
            </Panel>
          </div>
          <div className="min-h-0" style={{ gridColumn: '2', gridRow: '1' }}>
            <Panel title="Preview" className="h-full">
              <PanelBody className="flex h-full flex-col gap-4 p-4 text-sm text-white/70">
                <div className="flex-1 rounded border border-dashed border-white/20 bg-white/5">
                  <div className="flex h-full items-center justify-center text-xs text-white/50">
                    Blueprint preview renders here when provided by host.
                  </div>
                </div>
                <p>Supports pan, zoom, and host-provided annotations without altering upload flow.</p>
              </PanelBody>
            </Panel>
          </div>
          <div className="min-h-0" style={{ gridColumn: '3', gridRow: '1' }}>
            <Panel title="Schema Summary" className="h-full">
              <PanelBody className="flex h-full flex-col gap-3 p-4 text-sm text-white/70">
                <div className="rounded border border-white/10 bg-white/5 p-3 text-xs">
                  <p className="font-semibold text-white/80">Doors mapped</p>
                  <p>Pending host sync</p>
                </div>
                <div className="rounded border border-white/10 bg-white/5 p-3 text-xs">
                  <p className="font-semibold text-white/80">Rooms</p>
                  <p>Auto classified after upload</p>
                </div>
                <div className="rounded border border-white/10 bg-white/5 p-3 text-xs">
                  <p className="font-semibold text-white/80">Sensors</p>
                  <p>Linked by facility orchestrator</p>
                </div>
              </PanelBody>
            </Panel>
          </div>
          <div className="min-h-0" style={{ gridColumn: '2 / span 2', gridRow: '2' }}>
            <Panel title="Deployment Checklist" className="h-full">
              <PanelBody className="grid h-full grid-cols-2 gap-3 p-4 text-xs text-white/70">
                <div className="rounded border border-white/10 bg-white/5 p-3">
                  <p className="font-semibold text-white/80">Step 1</p>
                  <p>Verify facility coordinate alignment.</p>
                </div>
                <div className="rounded border border-white/10 bg-white/5 p-3">
                  <p className="font-semibold text-white/80">Step 2</p>
                  <p>Confirm ingress/egress nodes.</p>
                </div>
                <div className="rounded border border-white/10 bg-white/5 p-3">
                  <p className="font-semibold text-white/80">Step 3</p>
                  <p>Publish to Mission Control.</p>
                </div>
                <div className="rounded border border-white/10 bg-white/5 p-3">
                  <p className="font-semibold text-white/80">Step 4</p>
                  <p>Sync sensor overlays.</p>
                </div>
              </PanelBody>
            </Panel>
          </div>
        </div>
      </ViewportFrame>
    </div>
  )
}
