import type { ReactNode } from 'react'

import { useTranslation } from './i18n'
import { Link } from './router'
import { AppShell } from './components/layout/YosaiShell'

export interface AppLayoutProps {
  title: string
  subtitle?: string
  actions?: ReactNode
  children: ReactNode
  hideHeader?: boolean
}

export function AppLayout({
  title,
  subtitle,
  actions,
  children,
  hideHeader,
}: AppLayoutProps) {
  return (
    <AppShell
      title={title}
      subtitle={subtitle}
      actions={actions}
      hideHeader={hideHeader}
    >
      {children}
    </AppShell>
  )
}

export function HomeOverview() {
  const { t } = useTranslation()
  return (
    <AppLayout title={t('nav.home')} subtitle={t('app.tagline')}>
      {/* Bento Grid Layout */}
      <div
        style={{
          display: 'grid',
          gridTemplateColumns: 'repeat(auto-fit, minmax(300px, 1fr))',
          gap: '1.5rem',
          maxWidth: '1600px',
          margin: '0 auto',
        }}
      >
        {/* Ops: Upload & Process (2 cols wide on large screens if possible, here using span-2 logic if we had specific grid) */}
        <article className="app-home__card" style={{ gridColumn: 'span 1' }}>
          <div
            style={{
              display: 'flex',
              justifyContent: 'space-between',
              alignItems: 'center',
              marginBottom: '1rem',
            }}
          >
            <h3>{t('nav.upload')}</h3>
            {/* Placeholder for Sparkline or Metric */}
            <div
              style={{
                width: '40px',
                height: '40px',
                borderRadius: '50%',
                background: 'rgba(59, 130, 246, 0.1)',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
              }}
            >
              📂
            </div>
          </div>
          <p style={{ flex: 1 }}>{t('uploader.subtitle')}</p>
          <Link
            to="/cad/upload"
            className="app-home__cta"
            style={{ marginTop: '1rem', width: '100%' }}
          >
            {t('nav.upload')}
          </Link>
        </article>

        {/* Ops: Floor Detection */}
        <article className="app-home__card">
          <div
            style={{
              display: 'flex',
              justifyContent: 'space-between',
              alignItems: 'center',
              marginBottom: '1rem',
            }}
          >
            <h3>{t('nav.detection')}</h3>
            <div
              style={{
                width: '40px',
                height: '40px',
                borderRadius: '50%',
                background: 'rgba(16, 185, 129, 0.1)',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
              }}
            >
              ✨
            </div>
          </div>
          <p style={{ flex: 1 }}>{t('detection.subtitle')}</p>
          <Link
            to="/cad/detection"
            className="app-home__cta"
            style={{ marginTop: '1rem', width: '100%' }}
          >
            {t('nav.detection')}
          </Link>
        </article>

        {/* Business: Pipeline Worth */}
        <article
          className="app-home__card"
          style={{
            background:
              'linear-gradient(135deg, rgba(30,41,59,0.9) 0%, rgba(15,23,42,1) 100%)',
            border: '1px solid rgba(59,130,246,0.3)',
          }}
        >
          <div
            style={{
              display: 'flex',
              justifyContent: 'space-between',
              alignItems: 'center',
              marginBottom: '0.5rem',
            }}
          >
            <h3
              style={{
                color: '#94A3B8',
                fontSize: '0.875rem',
                textTransform: 'uppercase',
                letterSpacing: '0.05em',
              }}
            >
              Total Pipeline
            </h3>
            <span
              style={{
                color: '#10B981',
                fontSize: '0.875rem',
                fontWeight: 600,
              }}
            >
              +12.5% ↗
            </span>
          </div>
          <div
            style={{
              fontSize: '2.5rem',
              fontWeight: 700,
              color: '#F8FAFC',
              fontFamily: 'JetBrains Mono, monospace',
              marginBottom: '0.5rem',
            }}
          >
            $42.8M
          </div>
          <p style={{ fontSize: '0.875rem', color: '#64748B' }}>
            Weighted probability across 12 active deals.
          </p>
          {/* Sparkline Placeholder */}
          <div
            style={{
              height: '30px',
              marginTop: '1rem',
              background: 'rgba(255,255,255,0.05)',
              borderRadius: '4px',
              position: 'relative',
              overflow: 'hidden',
            }}
          >
            <div
              style={{
                position: 'absolute',
                bottom: 0,
                left: 0,
                width: '100%',
                height: '100%',
                background:
                  'linear-gradient(90deg, transparent 0%, rgba(59,130,246,0.2) 100%)',
              }}
            ></div>
            <svg width="100%" height="100%" preserveAspectRatio="none">
              <path
                d="M0,30 L50,20 L100,25 L150,10 L200,15 L250,5 L300,20"
                fill="none"
                stroke="#3B82F6"
                strokeWidth="2"
              />
            </svg>
          </div>
          <Link
            to="/cad/pipelines"
            className="app-home__cta"
            style={{
              marginTop: '1rem',
              width: '100%',
              background: 'rgba(59,130,246,0.1)',
              color: '#60A5FA',
            }}
          >
            View Operations
          </Link>
        </article>

        {/* Business: ROI / Feasibility */}
        <article className="app-home__card">
          <div
            style={{
              display: 'flex',
              justifyContent: 'space-between',
              alignItems: 'center',
              marginBottom: '1rem',
            }}
          >
            <h3>{t('nav.feasibility')}</h3>
            <div
              style={{
                width: '40px',
                height: '40px',
                borderRadius: '50%',
                background: 'rgba(245, 158, 11, 0.1)',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
              }}
            >
              🏗️
            </div>
          </div>
          <p style={{ flex: 1 }}>{t('home.cards.feasibility.description')}</p>
          <Link
            to="/feasibility"
            className="app-home__cta"
            style={{ marginTop: '1rem', width: '100%' }}
          >
            {t('nav.feasibility')}
          </Link>
        </article>

        {/* Business: Finance */}
        <article className="app-home__card">
          <div
            style={{
              display: 'flex',
              justifyContent: 'space-between',
              alignItems: 'center',
              marginBottom: '1rem',
            }}
          >
            <h3>{t('nav.finance')}</h3>
            <div
              style={{
                width: '40px',
                height: '40px',
                borderRadius: '50%',
                background: 'rgba(239, 68, 68, 0.1)',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
              }}
            >
              💰
            </div>
          </div>
          <p style={{ flex: 1 }}>{t('home.cards.finance.description')}</p>
          <Link
            to="/finance"
            className="app-home__cta"
            style={{ marginTop: '1rem', width: '100%' }}
          >
            {t('nav.finance')}
          </Link>
        </article>
      </div>
    </AppLayout>
  )
}

export default HomeOverview
