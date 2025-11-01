import { useState } from 'react'
import { ViewportFrame } from '@/components/layout/ViewportFrame'
import Panel from '@/components/layout/Panel'
import { PanelBody } from '@/components/layout/PanelBody'
import { ZenPageHeader } from './components/ZenPageHeader'
import { TID } from '@/testing/testids'

export default function SettingsPage() {
  const [gdprEnabled, setGdprEnabled] = useState(false)

  return (
    <div className="bg-neutral-950 text-white" data-testid={TID.page.settings}>
      <ViewportFrame className="flex h-full flex-col gap-6">
        <ZenPageHeader title="Settings" />
        <div
          className="grid flex-1 min-h-0 gap-6"
          style={{ gridTemplateColumns: 'minmax(0,1fr) minmax(0,1fr) minmax(0,1fr)' }}
        >
          <div className="min-h-0" style={{ gridColumn: '1', gridRow: '1 / span 2' }}>
            <Panel title="Privacy Controls" className="h-full">
              <PanelBody className="flex h-full flex-col gap-4 p-4 text-sm text-white/80">
                <label className="flex items-center gap-3 text-white">
                  <input
                    type="checkbox"
                    className="h-4 w-4"
                    checked={gdprEnabled}
                    onChange={(event) => setGdprEnabled(event.target.checked)}
                    data-testid={TID.control.enableGDPR}
                  />
                  <span>Enable GDPR mode</span>
                </label>
                <p className="text-xs text-white/60">
                  When enabled, personally identifiable information is redacted by default and compliance dashboards lock
                  down export features.
                </p>
                <div className="rounded border border-white/10 bg-white/5 p-3 text-xs text-white/70">
                  <p className="font-semibold text-white/80">Data retention</p>
                  <p>Aligns with facility policy once GDPR mode is active.</p>
                </div>
                <div className="rounded border border-white/10 bg-white/5 p-3 text-xs text-white/70">
                  <p className="font-semibold text-white/80">Mission sync</p>
                  <p>Propagates settings to Mission Control and Ticketing.</p>
                </div>
              </PanelBody>
            </Panel>
          </div>
          <div className="min-h-0" style={{ gridColumn: '2', gridRow: '1' }}>
            <Panel title="Account" className="h-full">
              <PanelBody className="flex h-full flex-col gap-3 p-4 text-sm text-white/70">
                <div className="rounded border border-white/10 bg-white/5 p-3 text-xs">
                  <p className="font-semibold text-white/80">Role</p>
                  <p>Facility administrator</p>
                </div>
                <div className="rounded border border-white/10 bg-white/5 p-3 text-xs">
                  <p className="font-semibold text-white/80">Last login</p>
                  <p>12 minutes ago</p>
                </div>
                <p className="mt-auto text-xs">
                  Account settings sync with identity provider; no local password storage.
                </p>
              </PanelBody>
            </Panel>
          </div>
          <div className="min-h-0" style={{ gridColumn: '3', gridRow: '1' }}>
            <Panel title="Integrations" className="h-full">
              <PanelBody className="flex h-full flex-col gap-3 p-4 text-sm text-white/70">
                <div className="rounded border border-white/10 bg-white/5 p-3 text-xs">
                  <p className="font-semibold text-white/80">Upload bridge</p>
                  <p>Active — defers to host-provided handlers.</p>
                </div>
                <div className="rounded border border-white/10 bg-white/5 p-3 text-xs">
                  <p className="font-semibold text-white/80">Mission Control</p>
                  <p>Notifications mirrored for alerts and tickets.</p>
                </div>
              </PanelBody>
            </Panel>
          </div>
          <div className="min-h-0" style={{ gridColumn: '2 / span 2', gridRow: '2' }}>
            <Panel title="Environment" className="h-full">
              <PanelBody className="grid h-full grid-cols-2 gap-3 p-4 text-xs text-white/70">
                <div className="rounded border border-white/10 bg-white/5 p-3">
                  <p className="font-semibold text-white/80">Release</p>
                  <p>Zen layout preview</p>
                </div>
                <div className="rounded border border-white/10 bg-white/5 p-3">
                  <p className="font-semibold text-white/80">Region</p>
                  <p>APAC-1</p>
                </div>
                <div className="rounded border border-white/10 bg-white/5 p-3">
                  <p className="font-semibold text-white/80">Support channel</p>
                  <p>mission-control@yosai</p>
                </div>
                <div className="rounded border border-white/10 bg-white/5 p-3">
                  <p className="font-semibold text-white/80">Feature flags</p>
                  <p>Upload enhancements enabled</p>
                </div>
              </PanelBody>
            </Panel>
          </div>
        </div>
      </ViewportFrame>
    </div>
  )
}
