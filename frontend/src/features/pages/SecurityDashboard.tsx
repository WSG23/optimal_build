import { ViewportFrame } from '@/components/layout/ViewportFrame'
import Panel from '@/components/layout/Panel'
import { PanelBody } from '@/components/layout/PanelBody'
import { TID } from '@/testing/testids'

export default function SecurityDashboardPage() {
  return (
    <div className="bg-neutral-950 text-white" data-testid={TID.page.securityDashboard}>
      <ViewportFrame className="flex h-full flex-col gap-6">
        <Panel title="Security Overview" className="h-full">
          <PanelBody className="flex h-full flex-col gap-6 p-4">
            <div className="kpi-strip">
              <div className="rounded-md border border-white/10 bg-white/5 p-4">
                <div className="text-xs uppercase tracking-wide text-white/50">MTTA</div>
                <div className="text-2xl font-semibold">12m</div>
              </div>
              <div className="rounded-md border border-white/10 bg-white/5 p-4">
                <div className="text-xs uppercase tracking-wide text-white/50">MTTR</div>
                <div className="text-2xl font-semibold">38m</div>
              </div>
              <div className="rounded-md border border-white/10 bg-white/5 p-4">
                <div className="text-xs uppercase tracking-wide text-white/50">Incident Volume</div>
                <div className="text-2xl font-semibold">24</div>
              </div>
            </div>
            <div className="flex-1 rounded-md border border-white/10 bg-white/5 p-4 text-sm text-white/70">
              Aggregation chart placeholder
            </div>
          </PanelBody>
        </Panel>
      </ViewportFrame>
    </div>
  )
}
