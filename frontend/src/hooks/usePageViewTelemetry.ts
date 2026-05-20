/**
 * Track every distinct pathname the user lands on as a single ``page_view``
 * event. Mounted once near the root of the app; relies on the global
 * telemetry queue, so the call is cheap and never blocks render.
 */

import { useEffect, useRef } from 'react'

import { track } from '../services/telemetry/telemetry'

export function usePageViewTelemetry(): void {
  const lastPath = useRef<string | null>(null)

  useEffect(() => {
    if (typeof window === 'undefined') return

    const fire = () => {
      const path = window.location.pathname
      if (lastPath.current === path) return
      lastPath.current = path
      track({
        eventType: 'navigation',
        eventName: 'page_view',
        path,
        payload: {
          title: typeof document !== 'undefined' ? document.title : undefined,
          search: window.location.search || undefined,
        },
      })
    }

    fire()
    window.addEventListener('popstate', fire)
    window.addEventListener('hashchange', fire)
    return () => {
      window.removeEventListener('popstate', fire)
      window.removeEventListener('hashchange', fire)
    }
  }, [])
}
