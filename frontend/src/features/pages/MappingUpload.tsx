import { useState } from 'react';
import { ViewportFrame } from '@/components/layout/ViewportFrame';
import Panel from '@/components/layout/Panel';
import { PanelBody } from '@/components/layout/PanelBody';
import { TID } from '@/testing/testids';
import { ingestBlueprint, type UploadStatus } from '@/services/uploadBridge';

export default function MappingUploadPage() {
  const [status, setStatus] = useState<UploadStatus>({ kind: 'idle' });

  return (
    <div className="bg-neutral-950 text-white" data-testid={TID.page.mappingUpload}>
      <ViewportFrame className="flex h-full flex-col gap-6">
        <Panel title="Mapping Upload (Blueprint Manager)">
          <PanelBody className="p-4">
            <div className="mb-3 text-sm text-white/70">
              Upload SVG, DXF, DWG, or PNG schematics. Existing blueprint ingest handlers are invoked if present.
            </div>
            <input
              type="file"
              accept=".svg,.dxf,.dwg,.png,image/png,image/svg+xml"
              data-testid={TID.control.uploadInput}
              onChange={async (event) => {
                const file = event.target.files?.[0];
                if (!file) {
                  return;
                }
                setStatus({ kind: 'selecting' });
                await ingestBlueprint(file, setStatus);
              }}
            />
            <div className="mt-5 grid gap-3 md:grid-cols-2">
              <div className="text-sm">
                <div className="mb-1 text-white/80">Step 1: Calibrate scale</div>
                <div className="text-white/60">
                  Choose two reference points with known distance. Host integrations may override this workflow.
                </div>
              </div>
              <div className="text-sm">
                <div className="mb-1 text-white/80">Step 2: Assign doors</div>
                <div className="text-white/60">
                  Snap doors to rooms or zones. External blueprint tools remain in control when wired.
                </div>
              </div>
            </div>
            <div className="mt-4 text-sm">
              {status.kind === 'idle' && <span className="text-white/50">No file selected.</span>}
              {status.kind === 'selecting' && <span>Preparing upload…</span>}
              {status.kind === 'uploading' && (
                <span>
                  Uploading <b>{status.filename}</b>…
                </span>
              )}
              {status.kind === 'success' && (
                <span>
                  ✅ Uploaded <b>{status.filename}</b>
                  {status.runId ? ` (schema: ${status.runId})` : ''}
                </span>
              )}
              {status.kind === 'error' && (
                <span>
                  ❌ {status.message}
                  {status.filename ? ` – ${status.filename}` : ''}
                </span>
              )}
            </div>
          </PanelBody>
        </Panel>
      </ViewportFrame>
    </div>
  );
}
