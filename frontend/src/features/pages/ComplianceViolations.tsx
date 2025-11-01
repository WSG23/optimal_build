import { ViewportFrame } from '@/components/layout/ViewportFrame'
import Panel from '@/components/layout/Panel'
import { PanelBody } from '@/components/layout/PanelBody'
import { ZenPageHeader } from './components/ZenPageHeader'
import { TID } from '@/testing/testids'

export default function ComplianceViolationsPage() {
  return (
    <div className="bg-neutral-950 text-white" data-testid={TID.page.complianceViolations}>
      <ViewportFrame className="flex h-full flex-col gap-6">
        <ZenPageHeader title="Compliance Violations" />
        <div
          className="grid flex-1 min-h-0 gap-6"
          style={{ gridTemplateColumns: 'minmax(0,1fr) minmax(0,1fr) minmax(0,1fr)' }}
        >
          <div className="min-h-0" style={{ gridColumn: '1 / span 2', gridRow: '1' }}>
            <Panel title="Violation Feed" className="h-full">
              <PanelBody className="flex h-full flex-col gap-3 p-4 text-sm text-white/70">
                <div className="rounded border border-white/10 bg-white/5 p-3 text-xs">
                  <p className="font-semibold text-white/80">Last 24 hours</p>
                  <p>No violations detected.</p>
                </div>
                <div className="rounded border border-white/10 bg-white/5 p-3 text-xs">
                  <p className="font-semibold text-white/80">Escalations</p>
                  <p>Automatic escalations route to DPIA and DSAR dashboards.</p>
                </div>
                <p className="mt-auto text-xs">
                  Data flows remain connected to <code>uploadBridge</code> outputs ensuring lineage is preserved for audits.
                </p>
              </PanelBody>
            </Panel>
          </div>
          <div className="min-h-0" style={{ gridColumn: '3', gridRow: '1 / span 2' }}>
            <Panel title="Policy Monitoring" className="h-full">
              <PanelBody className="flex h-full flex-col gap-3 p-4 text-sm text-white/70">
                <div className="rounded border border-white/10 bg-white/5 p-3 text-xs">
                  <p className="font-semibold text-white/80">GDPR</p>
                  <p>Real-time checks across DPIA, DSAR, and ROPA.</p>
                </div>
                <div className="rounded border border-white/10 bg-white/5 p-3 text-xs">
                  <p className="font-semibold text-white/80">CBT</p>
                  <p>Cross-border transfer records linked to upload metadata.</p>
                </div>
                <div className="rounded border border-white/10 bg-white/5 p-3 text-xs">
                  <p className="font-semibold text-white/80">Audit readiness</p>
                  <p>Exports pull directly from compliance store for regulators.</p>
                </div>
              </PanelBody>
            </Panel>
          </div>
          <div className="min-h-0" style={{ gridColumn: '1 / span 2', gridRow: '2' }}>
            <Panel title="Remediation Checklist" className="h-full">
              <PanelBody className="grid h-full grid-cols-2 gap-3 p-4 text-xs text-white/70">
                <div className="rounded border border-white/10 bg-white/5 p-3">
                  <p className="font-semibold text-white/80">1. Validate data source</p>
                  <p>Confirm originating upload and host acknowledgements.</p>
                </div>
                <div className="rounded border border-white/10 bg-white/5 p-3">
                  <p className="font-semibold text-white/80">2. Assign owner</p>
                  <p>Route to facility compliance lead.</p>
                </div>
                <div className="rounded border border-white/10 bg-white/5 p-3">
                  <p className="font-semibold text-white/80">3. Document mitigation</p>
                  <p>Attach ticketing references and notes.</p>
                </div>
                <div className="rounded border border-white/10 bg-white/5 p-3">
                  <p className="font-semibold text-white/80">4. Close out</p>
                  <p>Push resolution back to Mission Control.</p>
                </div>
              </PanelBody>
            </Panel>
          </div>
        </div>
      </ViewportFrame>
    </div>
  )
}
