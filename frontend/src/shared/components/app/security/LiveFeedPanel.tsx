const sampleEvents = [
  { id: 1, message: 'Camera 12 detected unusual motion', timestamp: '09:20' },
  { id: 2, message: 'Badge rejected at Loading Dock', timestamp: '09:24' },
  { id: 3, message: 'Thermal alert triggered in Lab 4', timestamp: '09:32' },
]

export function LiveFeedPanel() {
  return (
    <ul className="space-y-3">
      {sampleEvents.map((event) => (
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
