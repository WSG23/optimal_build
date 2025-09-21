import { useCallback, useEffect, useMemo, useState } from 'react'

import { Link } from './router'

interface HealthStatus {
  status: string
  service: string
}

function App() {
  const [healthStatus, setHealthStatus] = useState<HealthStatus | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  const rawBaseUrl = import.meta.env.VITE_API_BASE_URL ?? '/'
  const resolvedBaseUrl = useMemo<URL | null>(() => {
    if (typeof window === 'undefined') {
      return null
    }

    try {
      return new URL(rawBaseUrl, window.location.origin)
    } catch (err) {
      console.error('Invalid VITE_API_BASE_URL, falling back to window.location.origin', err)
      return new URL(window.location.origin)
    }
  }, [rawBaseUrl])

  const buildApiUrl = useCallback(
    (path: string) => {
      if (!resolvedBaseUrl) {
        return path
      }

      return new URL(path, resolvedBaseUrl).toString()
    },
    [resolvedBaseUrl],
  )

  useEffect(() => {
    const checkHealth = async () => {
      try {
        const response = await fetch(buildApiUrl('health'))
        if (response.ok) {
          const data = await response.json()
          setHealthStatus(data)
        } else {
          setError('Backend not responding')
        }
      } catch (err) {
        setError('Cannot connect to backend')
      } finally {
        setLoading(false)
      }
    }

    checkHealth()
  }, [buildApiUrl])

  return (
    <div className="app-shell">
      <header className="app-shell__header">
        <h1>Optimal Build Studio</h1>
        <p>
          Explore automated compliance insights, land intelligence and feasibility analysis for
          Singapore developments.
        </p>
      </header>

      <nav className="app-shell__nav">
        <Link className="app-shell__nav-link" to="/feasibility">
          Launch feasibility wizard
        </Link>
        <a
          className="app-shell__nav-link"
          href={buildApiUrl('docs')}
          target="_blank"
          rel="noreferrer"
        >
          View API reference
        </a>
      </nav>

      <section className="app-shell__section">
        <h2>System status</h2>
        {loading && <p>Checking backend connection…</p>}
        {error && <p style={{ color: '#b91c1c' }}>❌ {error}</p>}
        {healthStatus && (
          <p style={{ color: '#15803d' }}>
            ✅ Backend Status: {healthStatus.status} ({healthStatus.service})
          </p>
        )}
      </section>

      <section className="app-shell__section">
        <h2>Quick links</h2>
        <ul>
          <li>
            <a href={buildApiUrl('health')} target="_blank" rel="noreferrer">
              Backend health check
            </a>
          </li>
          <li>
            <a href={buildApiUrl('docs')} target="_blank" rel="noreferrer">
              API documentation
            </a>
          </li>
          <li>
            <a href={buildApiUrl('api/v1/test')} target="_blank" rel="noreferrer">
              API test endpoint
            </a>
          </li>
        </ul>
      </section>

      <section className="app-shell__section">
        <h2>Why start here?</h2>
        <ul>
          <li>Capture project basics once and reuse across compliance workflows.</li>
          <li>Review cross-agency rules synthesised from the knowledge platform.</li>
          <li>Generate buildability insights with clear next steps for the team.</li>
        </ul>
      </section>

      <section className="app-shell__section">
        <h2>Next steps</h2>
        <ol>
          <li>✅ Frontend and backend are connected.</li>
          <li>🔄 Add database integration.</li>
          <li>🔄 Implement buildable analysis.</li>
          <li>🔄 Add Singapore building codes.</li>
        </ol>
      </section>
    </div>
  )
}

export default App
