import { useState } from 'react'
import { ViewportFrame } from '@/components/layout/ViewportFrame'
import Panel from '@/components/layout/Panel'
import { PanelBody } from '@/components/layout/PanelBody'
import { TID } from '@/testing/testids'

export default function SettingsPage() {
  const [gdprEnabled, setGdprEnabled] = useState(false)

  return (
    <div className="bg-neutral-950 text-white" data-testid={TID.page.settings}>
      <ViewportFrame className="flex h-full flex-col gap-6">
        <Panel title="Settings">
          <PanelBody className="p-4 text-sm text-white/80">
            <label className="flex items-center gap-3">
              <input
                type="checkbox"
                className="h-4 w-4"
                checked={gdprEnabled}
                onChange={(event) => setGdprEnabled(event.target.checked)}
                data-testid={TID.control.enableGDPR}
              />
              <span>Enable GDPR mode</span>
            </label>
            <p className="mt-3 text-xs text-white/60">
              When enabled, personally identifiable information is redacted by default.
            </p>
          </PanelBody>
        </Panel>
      </ViewportFrame>
    </div>
  )
}
