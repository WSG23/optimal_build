import { ViewportFrame } from '@/components/layout/ViewportFrame'
import Panel from '@/components/layout/Panel'
import { PanelBody } from '@/components/layout/PanelBody'
import { TID } from '@/testing/testids'

export default function ComplianceViolationsPage() {
  return (
    <div className="bg-neutral-950 text-white" data-testid={TID.page.complianceViolations}>
      <ViewportFrame className="flex h-full flex-col gap-6">
        <Panel title="Compliance Violations">
          <PanelBody className="p-4 text-sm text-white/70">
            Violation feed placeholder for pending remediation tasks.
          </PanelBody>
        </Panel>
      </ViewportFrame>
    </div>
  )
}
