import { ViewportFrame } from '@/components/layout/ViewportFrame'
import Panel from '@/components/layout/Panel'
import { PanelBody } from '@/components/layout/PanelBody'
import { TID } from '@/testing/testids'

export default function ROPADashboard() {
  return (
    <div className="bg-neutral-950 text-white" data-testid={TID.page.complianceROPA}>
      <ViewportFrame className="flex h-full flex-col gap-6">
        <Panel title="ROPA Registry">
          <PanelBody className="p-4 text-sm text-white/70">
            Maintain records of processing activities and responsible owners.
          </PanelBody>
        </Panel>
      </ViewportFrame>
    </div>
  )
}
