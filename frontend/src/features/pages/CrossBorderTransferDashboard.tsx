import { ViewportFrame } from '@/components/layout/ViewportFrame'
import Panel from '@/components/layout/Panel'
import { PanelBody } from '@/components/layout/PanelBody'
import { TID } from '@/testing/testids'

export default function CrossBorderTransferDashboard() {
  return (
    <div className="bg-neutral-950 text-white" data-testid={TID.page.complianceCBT}>
      <ViewportFrame className="flex h-full flex-col gap-6">
        <Panel title="Cross-Border Transfers">
          <PanelBody className="p-4 text-sm text-white/70">
            Review transfers by destination region and legal basis.
          </PanelBody>
        </Panel>
      </ViewportFrame>
    </div>
  )
}
