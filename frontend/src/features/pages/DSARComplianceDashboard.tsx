import { ViewportFrame } from '@/components/layout/ViewportFrame'
import Panel from '@/components/layout/Panel'
import { PanelBody } from '@/components/layout/PanelBody'
import { TID } from '@/testing/testids'

export default function DSARComplianceDashboard() {
  return (
    <div className="bg-neutral-950 text-white" data-testid={TID.page.complianceDSAR}>
      <ViewportFrame className="flex h-full flex-col gap-6">
        <Panel title="DSAR Fulfillment">
          <PanelBody className="p-4 text-sm text-white/70">
            Generate export bundles for subject access requests.
          </PanelBody>
        </Panel>
      </ViewportFrame>
    </div>
  )
}
