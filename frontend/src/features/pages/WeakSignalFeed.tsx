import { ViewportFrame } from '@/components/layout/ViewportFrame'
import Panel from '@/components/layout/Panel'
import { PanelBody } from '@/components/layout/PanelBody'
import { LiveFeedPanel } from '@/shared/components/app/security/LiveFeedPanel'
import { TID } from '@/testing/testids'

export default function WeakSignalFeed() {
  return (
    <div className="bg-neutral-950 text-white" data-testid={TID.page.weakSignal}>
      <ViewportFrame className="flex h-full flex-col gap-6">
        <Panel title="Weak-Signal Feed">
          <PanelBody className="p-3">
            <LiveFeedPanel />
          </PanelBody>
        </Panel>
      </ViewportFrame>
    </div>
  )
}
