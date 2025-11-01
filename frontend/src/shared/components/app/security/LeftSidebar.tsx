import Panel from '@/components/layout/Panel';
import { PanelBody } from '@/components/layout/PanelBody';
import type { TicketsByStatus } from './IncidentAlertsPanel';

export interface LeftSidebarProps {
  facilityLabel: string;
  threatScore: number;
  ticketsByStatus: TicketsByStatus;
}

export function LeftSidebar({ facilityLabel, threatScore, ticketsByStatus }: LeftSidebarProps) {
  const row = (label: string, count: number) => (
    <div className="flex items-center justify-between border-t border-white/10 py-2 text-sm">
      <span className="text-white/80">{label}</span>
      <span className="text-white/90">{count}</span>
    </div>
  );

  return (
    <aside className="flex min-h-0 flex-col gap-3">
      <Panel title="Threat Potential" className="flex-none">
        <PanelBody className="p-4">
          <div className="text-5xl font-semibold leading-none">{threatScore}</div>
          <div className="mt-2 text-xs text-white/60">{facilityLabel}</div>
        </PanelBody>
      </Panel>

      <Panel title="Tickets" className="flex-1">
        <PanelBody className="p-0">
          {row('Open Tickets', ticketsByStatus.open.length)}
          {row('Locked Tickets', ticketsByStatus.locked.length)}
          {row('Resolved as Harmful', ticketsByStatus.resolved_harmful.length)}
          {row('Resolved as Tech. Malfunction', ticketsByStatus.resolved_malfunction.length)}
          {row('Resolved as Normal', ticketsByStatus.resolved_normal.length)}
          {row('Dismissed Tickets', ticketsByStatus.dismissed.length)}
        </PanelBody>
      </Panel>
    </aside>
  );
}

export default LeftSidebar;
