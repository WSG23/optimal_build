import type { FC } from 'react';
import type { Ticket } from './types';

export interface IncidentResponsePanelProps {
  ticket: Ticket;
  onResolve: (ticket: Ticket) => void;
  onDismiss: (ticket: Ticket) => void;
  onClose: (ticket: Ticket) => void;
}

export const IncidentResponsePanel: FC<IncidentResponsePanelProps> = ({
  ticket,
  onResolve,
  onDismiss,
  onClose,
}) => {
  return (
    <div className="flex h-full flex-col gap-3">
      <div>
        <div className="text-base font-semibold text-white">{ticket.title}</div>
        <p className="mt-1 text-sm text-white/70">{ticket.description}</p>
        <p className="mt-1 text-xs uppercase tracking-wide text-white/40">{ticket.location}</p>
      </div>
      <div className="mt-auto flex flex-wrap gap-2 text-sm">
        <button
          type="button"
          className="rounded-md bg-emerald-500/80 px-3 py-2 font-medium text-white transition hover:bg-emerald-500"
          onClick={() => onResolve(ticket)}
        >
          Resolve
        </button>
        <button
          type="button"
          className="rounded-md bg-amber-500/80 px-3 py-2 font-medium text-white transition hover:bg-amber-500"
          onClick={() => onDismiss(ticket)}
        >
          Dismiss
        </button>
        <button
          type="button"
          className="rounded-md bg-white/10 px-3 py-2 font-medium text-white transition hover:bg-white/20"
          onClick={() => onClose(ticket)}
        >
          Close
        </button>
      </div>
    </div>
  );
};

export default IncidentResponsePanel;
