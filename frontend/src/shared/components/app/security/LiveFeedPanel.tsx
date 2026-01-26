export interface LiveFeedEvent {
  id: string | number
  message: string
  timestamp: string
}

export function LiveFeedPanel({ events = [] }: { events?: LiveFeedEvent[] }) {
  if (events.length === 0) {
    return (
      <div className="text-sm text-white/60">No live events available.</div>
    )
  }

  return (
    <ul className="space-y-3">
      {events.map((event) => (
        <li
          key={event.id}
          className="rounded-md border border-white/10 bg-white/5 p-3"
        >
          <div className="text-xs uppercase tracking-wide text-white/40">
            {event.timestamp}
          </div>
          <div className="text-sm text-white/80">{event.message}</div>
        </li>
      ))}
    </ul>
  )
}

export default LiveFeedPanel
