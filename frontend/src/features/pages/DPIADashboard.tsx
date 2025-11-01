import { ViewportFrame } from '@/components/layout/ViewportFrame'
import Panel from '@/components/layout/Panel'
import { PanelBody } from '@/components/layout/PanelBody'
import { TID } from '@/testing/testids'

export default function DPIADashboard() {
  return (
    <div className="bg-neutral-950 text-white" data-testid={TID.page.complianceDPIA}>
      <ViewportFrame className="flex h-full flex-col gap-6">
        <Panel title="DPIA Risk Matrix">
          <PanelBody className="p-4 text-sm text-white/70">
            Configure impact and likelihood to evaluate privacy risk.
          </PanelBody>
        </Panel>
      </ViewportFrame>
    </div>
  )
}
