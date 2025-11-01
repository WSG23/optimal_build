import { useEffect, useState } from 'react';

export function ClockTicker() {
  const [now, setNow] = useState(() => new Date());

  useEffect(() => {
    const timer = window.setInterval(() => setNow(new Date()), 1000);
    return () => window.clearInterval(timer);
  }, []);

  return (
    <time className="text-sm font-mono text-white/70" dateTime={now.toISOString()}>
      {now.toLocaleTimeString()}
    </time>
  );
}

export default ClockTicker;
