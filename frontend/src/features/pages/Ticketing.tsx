import { ViewportFrame } from '@/components/layout/ViewportFrame';
import Panel from '@/components/layout/Panel';
import { PanelBody } from '@/components/layout/PanelBody';
import { IncidentAlertsPanel } from '@/shared/components/app/security/IncidentAlertsPanel';
import { TID } from '@/testing/testids';

export default function TicketingPage() {
  return (
    <div className="bg-neutral-950 text-white" data-testid={TID.page.ticketing}>
      <ViewportFrame className="flex h-full flex-col gap-6">
        <Panel title="Ticketing">
          <PanelBody className="p-3">
            <IncidentAlertsPanel
              ticketsByStatus={{
                open: [],
                locked: [],
                resolved_harmful: [],
                resolved_malfunction: [],
                resolved_normal: [],
                dismissed: [],
              }}
              selectedTicket={null}
              onTicketSelect={(ticket) => {
                void ticket;
              }}
            />
          </PanelBody>
        </Panel>
      </ViewportFrame>
    </div>
  );
}
