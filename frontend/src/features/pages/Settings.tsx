import { ViewportFrame } from '@/components/layout/ViewportFrame';
import Panel from '@/components/layout/Panel';
import { PanelBody } from '@/components/layout/PanelBody';
import { TID } from '@/testing/testids';

export default function SettingsPage() {
  return (
    <div className="bg-neutral-950 text-white" data-testid={TID.page.settings}>
      <ViewportFrame className="flex h-full flex-col gap-6">
        <Panel title="Settings">
          <PanelBody className="p-4">
            <label className="flex items-center gap-3 text-sm text-white/80">
              <input type="checkbox" data-testid={TID.control.enableGDPR} />
              <span>Enable GDPR mode</span>
            </label>
          </PanelBody>
        </Panel>
      </ViewportFrame>
    </div>
  );
}
