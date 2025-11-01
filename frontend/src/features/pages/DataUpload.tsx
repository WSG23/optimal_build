import { useState } from 'react';
import { ViewportFrame } from '@/components/layout/ViewportFrame';
import Panel from '@/components/layout/Panel';
import { PanelBody } from '@/components/layout/PanelBody';
import { TID } from '@/testing/testids';
import { ingestDataFile, type UploadStatus } from '@/services/uploadBridge';

export default function DataUploadPage() {
  const [status, setStatus] = useState<UploadStatus>({ kind: 'idle' });

  return (
    <div className="bg-neutral-950 text-white" data-testid={TID.page.dataUpload}>
      <ViewportFrame className="flex h-full flex-col gap-6">
        <Panel title="Data Upload & Enhancement">
          <PanelBody className="p-4">
            <div className="mb-3 text-sm text-white/70">
              Upload CSV or JSON access logs. Existing host uploaders will run automatically when present.
            </div>
            <input
              type="file"
              accept=".csv,.json,application/json,text/csv"
              data-testid={TID.control.uploadInput}
              onChange={async (event) => {
                const file = event.target.files?.[0];
                if (!file) {
                  return;
                }
                setStatus({ kind: 'selecting' });
                await ingestDataFile(file, setStatus);
              }}
            />
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
                  {status.runId ? ` (runId: ${status.runId})` : ''}
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
