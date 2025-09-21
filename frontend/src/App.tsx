import { useCallback, useEffect, useMemo, useState } from 'react'

import { useTranslation } from './i18n'
import { LocaleSwitcher } from './i18n/LocaleSwitcher'
import { Link } from './router'

interface HealthStatus {
  status: string
  service: string
}

type HealthErrorKey = 'backendNotResponding' | 'cannotConnect'

function App() {
  const { t } = useTranslation()
  const [healthStatus, setHealthStatus] = useState<HealthStatus | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<HealthErrorKey | null>(null)

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
          setError(null)
        } else {
          setError('backendNotResponding')
        }
      } catch (err) {
        setError('cannotConnect')
      } finally {
        setLoading(false)
      }
    }

    checkHealth()
  }, [buildApiUrl])

  const reasons = useMemo(
    () => t('app.why.items', { returnObjects: true }) as string[],
    [t],
  )

  const nextSteps = useMemo(
    () => t('app.nextSteps.items', { returnObjects: true }) as string[],
    [t],
  )

  return (
    <div className="app-shell">
      <header className="app-shell__header">
        <div className="app-shell__toolbar">
          <LocaleSwitcher />
        </div>
        <h1>{t('app.title')}</h1>
        <p>{t('app.tagline')}</p>
      </header>

      <nav className="app-shell__nav">
        <Link className="app-shell__nav-link" to="/feasibility">
          {t('app.nav.feasibility')}
        </Link>
        <a
          className="app-shell__nav-link"
          href={buildApiUrl('docs')}
          target="_blank"
          rel="noreferrer"
        >
          {t('app.nav.docs')}
        </a>
      </nav>

      <section className="app-shell__section">
        <h2>{t('app.status.heading')}</h2>
        {loading && <p>{t('app.status.loading')}</p>}
        {error && (
          <p style={{ color: '#b91c1c' }}>❌ {t(`app.status.errors.${error}`)}</p>
        )}
        {healthStatus && (
          <p style={{ color: '#15803d' }}>
            {t('app.status.success', {
              status: healthStatus.status,
              service: healthStatus.service,
            })}
          </p>
        )}
      </section>

      <section className="app-shell__section">
        <h2>{t('app.quickLinks.heading')}</h2>
        <ul>
          <li>
            <a href={buildApiUrl('health')} target="_blank" rel="noreferrer">
              {t('app.quickLinks.health')}
            </a>
          </li>
          <li>
            <a href={buildApiUrl('docs')} target="_blank" rel="noreferrer">
              {t('app.quickLinks.docs')}
            </a>
          </li>
          <li>
            <a href={buildApiUrl('api/v1/test')} target="_blank" rel="noreferrer">
              {t('app.quickLinks.test')}
            </a>
          </li>
        </ul>
      </section>

      <section className="app-shell__section">
        <h2>{t('app.why.heading')}</h2>
        <ul>
          {reasons.map((reason, index) => (
            <li key={index}>{reason}</li>
          ))}
        </ul>
      </section>

      <section className="app-shell__section">
        <h2>{t('app.nextSteps.heading')}</h2>
        <ol>
          {nextSteps.map((step, index) => (
            <li key={index}>{step}</li>
          ))}
        </ol>
      </section>
    </div>
  )
}

export default App
