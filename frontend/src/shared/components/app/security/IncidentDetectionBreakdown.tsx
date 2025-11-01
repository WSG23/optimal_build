import type { FC } from 'react';
import type { Ticket } from './types';

export interface IncidentDetectionBreakdownProps {
  locationFilter: string | null;
  selectedCategory: string | null;
  onCategoryClick: (category: string) => void;
  ticketId: string | null;
  ticketLabel: string | null;
  tickets?: Ticket[];
}

export const IncidentDetectionBreakdown: FC<IncidentDetectionBreakdownProps> = ({
  locationFilter,
  selectedCategory,
  onCategoryClick,
  ticketId,
  ticketLabel,
  tickets = [],
}) => {
  const filteredTickets = locationFilter
    ? tickets.filter((ticket) => ticket.location === locationFilter)
    : tickets;
  const categoryCounts = filteredTickets.reduce<Record<string, number>>((acc, ticket) => {
    acc[ticket.category] = (acc[ticket.category] ?? 0) + 1;
    return acc;
  }, {});
  const categories = Object.entries(categoryCounts);

  return (
    <div className="flex h-full flex-col gap-4">
      <div className="text-xs uppercase tracking-wide text-white/40">
        {locationFilter ? `Filtered by ${locationFilter}` : 'All Locations'}
      </div>
      <ul className="space-y-2">
        {categories.map(([category, count]) => {
          const active = selectedCategory === category;
          return (
            <li key={category}>
              <button
                type="button"
                className={`flex w-full items-center justify-between rounded-md border border-white/10 px-4 py-3 text-sm transition hover:bg-white/10 ${
                  active ? 'bg-white/15 text-white' : 'text-white/80'
                }`}
                onClick={() => onCategoryClick(category)}
              >
                <span>{category}</span>
                <span className="text-xs text-white/60">{count}</span>
              </button>
            </li>
          );
        })}
      </ul>
      {ticketId ? (
        <div className="mt-auto rounded-md border border-dashed border-white/10 p-3 text-xs text-white/50">
          Focused Ticket: {ticketLabel ?? ticketId}
        </div>
      ) : null}
    </div>
  );
};

export default IncidentDetectionBreakdown;
