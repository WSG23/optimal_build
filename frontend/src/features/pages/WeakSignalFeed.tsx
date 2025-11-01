import { ViewportFrame } from '@/components/layout/ViewportFrame'
import Panel from '@/components/layout/Panel'
import { PanelBody } from '@/components/layout/PanelBody'
import { LiveFeedPanel } from '@/shared/components/app/security/LiveFeedPanel'
import { ZenPageHeader } from './components/ZenPageHeader'
import { TID } from '@/testing/testids'

export default function WeakSignalFeed() {
  return (
    <div className="bg-neutral-950 text-white" data-testid={TID.page.weakSignal}>
      <ViewportFrame className="flex h-full flex-col gap-6">
        <ZenPageHeader title="Weak-Signal Feed" />
        <div
          className="grid flex-1 min-h-0 gap-6"
          style={{ gridTemplateColumns: 'minmax(0,1fr) minmax(0,1.4fr) minmax(0,1fr)' }}
        >
          <div className="min-h-0" style={{ gridColumn: '1', gridRow: '1 / span 2' }}>
            <Panel title="Signal Health" className="h-full">
              <PanelBody className="flex h-full flex-col gap-3 p-4 text-sm text-white/70">
                <div className="rounded border border-white/10 bg-white/5 p-3 text-xs">
                  <p className="font-semibold text-white/80">Sensors online</p>
                  <p>94%</p>
                </div>
                <div className="rounded border border-white/10 bg-white/5 p-3 text-xs">
                  <p className="font-semibold text-white/80">Weak signals</p>
                  <p>12 flagged in last hour</p>
                </div>
                <div className="rounded border border-white/10 bg-white/5 p-3 text-xs">
                  <p className="font-semibold text-white/80">Escalations</p>
                  <p>4 routed to Ticketing</p>
                </div>
                <p className="mt-auto text-xs">
                  Feed synchronizes with live mission state; host overrides still flow via WebSocket bridge.
                </p>
              </PanelBody>
            </Panel>
          </div>
          <div className="min-h-0" style={{ gridColumn: '2', gridRow: '1 / span 2' }}>
            <Panel title="Weak-Signal Feed" className="h-full">
              <PanelBody className="h-full overflow-y-auto p-3">
                <LiveFeedPanel />
              </PanelBody>
            </Panel>
          </div>
          <div className="min-h-0" style={{ gridColumn: '3', gridRow: '1' }}>
            <Panel title="Priority Channels" className="h-full">
              <PanelBody className="flex h-full flex-col gap-3 p-4 text-sm text-white/70">
                <div className="rounded border border-white/10 bg-white/5 p-3 text-xs">
                  <p className="font-semibold text-white/80">Thermal anomalies</p>
                  <p>Watching labs 2 &amp; 5</p>
                </div>
                <div className="rounded border border-white/10 bg-white/5 p-3 text-xs">
                  <p className="font-semibold text-white/80">Access drift</p>
                  <p>Badge patterns deviating from baseline</p>
                </div>
              </PanelBody>
            </Panel>
          </div>
          <div className="min-h-0" style={{ gridColumn: '3', gridRow: '2' }}>
            <Panel title="Next Actions" className="h-full">
              <PanelBody className="flex h-full flex-col gap-2 p-4 text-xs text-white/70">
                <div className="rounded border border-white/10 bg-white/5 p-3">
                  <p className="font-semibold text-white/80">Sync with Mission Control</p>
                  <p>Auto share cross-floor patterns.</p>
                </div>
                <div className="rounded border border-white/10 bg-white/5 p-3">
                  <p className="font-semibold text-white/80">Escalate anomalies</p>
                  <p>Send critical drift to Ticketing queue.</p>
                </div>
              </PanelBody>
            </Panel>
          </div>
        </div>
      </ViewportFrame>
    </div>
  )
}
