import type { FC } from 'react';
import type { Ticket } from './types';

export interface IncidentMapViewProps {
  tickets: Ticket[];
  selectedTicket: Ticket | null;
  onLocationClick: (location: string) => void;
  selectedLocation: string | null;
}

export const IncidentMapView: FC<IncidentMapViewProps> = ({
  tickets,
  selectedTicket,
  onLocationClick,
  selectedLocation,
}) => {
  const locations = Array.from(new Set(tickets.map((ticket) => ticket.location)));

  return (
    <div className="flex h-full flex-col gap-4 p-4">
      <div className="flex flex-wrap gap-2">
        {locations.map((location) => {
          const active = selectedLocation === location;
          return (
            <button
              key={location}
              type="button"
              className={`rounded-full border border-white/10 px-3 py-1 text-xs uppercase tracking-wide transition hover:bg-white/10 ${
                active ? 'bg-white/15 text-white' : 'text-white/70'
              }`}
              onClick={() => onLocationClick(location)}
            >
              {location}
            </button>
          );
        })}
      </div>
      <div className="flex-1 overflow-y-auto rounded-lg border border-white/10 bg-neutral-900/50 p-4 text-sm text-white/70">
        {selectedTicket ? (
          <div>
            <div className="text-lg font-semibold text-white">{selectedTicket.title}</div>
            <p className="mt-1">{selectedTicket.description}</p>
            <p className="mt-2 text-xs uppercase tracking-wide text-white/40">
              {selectedTicket.location}
            </p>
          </div>
        ) : (
          <p>Select a ticket from the alerts list to focus on the map.</p>
        )}
      </div>
    </div>
  );
};

export default IncidentMapView;
