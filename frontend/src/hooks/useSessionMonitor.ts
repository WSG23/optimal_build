import { useCallback, useEffect, useRef, useState } from 'react'

/**
 * Monitors for HTTP 401 responses by patching `window.fetch`.
 * When a 401 is detected, `isSessionExpired` becomes true so the
 * UI can prompt the user to re-authenticate.
 *
 * Known limitations:
 * - Only intercepts fetch() calls, not XMLHttpRequest or library-specific clients
 * - If another library patches fetch after this hook mounts, detection may break
 * - Designed for fetch-only codebases; pair with Axios interceptors for full coverage
 */
export function useSessionMonitor(): {
  isSessionExpired: boolean
  dismissExpiry: () => void
} {
  const [isSessionExpired, setIsSessionExpired] = useState(false)
  const originalFetchRef = useRef<typeof window.fetch | null>(null)

  const dismissExpiry = useCallback(() => {
    setIsSessionExpired(false)
  }, [])

  useEffect(() => {
    if (typeof window === 'undefined') return

    // Avoid patching more than once if the hook re-mounts.
    if (originalFetchRef.current) return
    const originalFetch = window.fetch
    originalFetchRef.current = originalFetch

    window.fetch = async (...args: Parameters<typeof fetch>) => {
      const response = await originalFetch(...args)
      if (response.status === 401) {
        setIsSessionExpired(true)
      }
      return response
    }

    return () => {
      if (originalFetchRef.current) {
        window.fetch = originalFetchRef.current
        originalFetchRef.current = null
      }
    }
  }, [])

  return { isSessionExpired, dismissExpiry }
}
