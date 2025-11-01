import { ViewportFrame } from '@/components/layout/ViewportFrame'
import Panel from '@/components/layout/Panel'
import { PanelBody } from '@/components/layout/PanelBody'
import { TID } from '@/testing/testids'

export default function MissionControlPage() {
  return (
    <div className="bg-neutral-950 text-white" data-testid={TID.page.mission}>
      <ViewportFrame className="flex h-full flex-col gap-6">
        <Panel title="Mission Timeline" className="h-full">
          <PanelBody className="flex h-full flex-col gap-4 p-4">
            <div
              className="h-24 rounded-md border border-white/10 bg-white/5"
              data-testid={TID.control.timelineBrush}
            />
            <div className="grid flex-1 grid-cols-1 gap-3 text-sm text-white/70">
              <div className="rounded-md border border-white/10 bg-white/5 p-3">
                Timeline visualization placeholder
              </div>
              <div className="rounded-md border border-white/10 bg-white/5 p-3">
                Event feed placeholder
              </div>
            </div>
          </PanelBody>
        </Panel>
      </ViewportFrame>
    </div>
  )
}
