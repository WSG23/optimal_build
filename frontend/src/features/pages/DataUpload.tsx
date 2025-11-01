import { ViewportFrame } from '@/components/layout/ViewportFrame'
import Panel from '@/components/layout/Panel'
import { PanelBody } from '@/components/layout/PanelBody'
import { TID } from '@/testing/testids'

export default function DataUploadPage() {
  return (
    <div className="bg-neutral-950 text-white" data-testid={TID.page.dataUpload}>
      <ViewportFrame className="flex h-full flex-col gap-6">
        <Panel title="Data Upload & Enhancement">
          <PanelBody className="p-4">
            <input type="file" data-testid={TID.control.uploadInput} className="block w-full text-sm text-white" />
            <p className="mt-3 text-sm text-white/60">
              Import CSV or JSON files to enrich facility telemetry and compliance datasets.
            </p>
          </PanelBody>
        </Panel>
      </ViewportFrame>
    </div>
  )
}
