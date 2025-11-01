import { ViewportFrame } from '@/components/layout/ViewportFrame'
import Panel from '@/components/layout/Panel'
import { PanelBody } from '@/components/layout/PanelBody'
import { TID } from '@/testing/testids'

export default function MappingUploadPage() {
  return (
    <div className="bg-neutral-950 text-white" data-testid={TID.page.mappingUpload}>
      <ViewportFrame className="flex h-full flex-col gap-6">
        <Panel title="Mapping Upload (Blueprint Manager)">
          <PanelBody className="p-4">
            <input type="file" data-testid={TID.control.uploadInput} className="block w-full text-sm text-white" />
            <p className="mt-3 text-sm text-white/60">
              Upload blueprint files to calibrate spatial layouts for mission planning.
            </p>
          </PanelBody>
        </Panel>
      </ViewportFrame>
    </div>
  )
}
