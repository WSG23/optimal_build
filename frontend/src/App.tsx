import type { ReactNode } from 'react'

import { useTranslation } from './i18n'
import { Link } from './router'
import { AppShell } from './components/layout/Shell'
import './styles/home-overview.css'

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
      <div className="home-overview__grid">
        {/* Ops: Upload & Process */}
        <article className="app-home__card">
          <div className="home-overview__card-header">
            <h3>{t('nav.upload')}</h3>
            <div className="home-overview__icon-badge home-overview__icon-badge--brand">
              📂
            </div>
          </div>
          <p>{t('uploader.subtitle')}</p>
          <Link to="/cad/upload" className="app-home__cta home-overview__cta">
            {t('nav.upload')}
          </Link>
        </article>

        {/* Ops: Floor Detection */}
        <article className="app-home__card">
          <div className="home-overview__card-header">
            <h3>{t('nav.detection')}</h3>
            <div className="home-overview__icon-badge home-overview__icon-badge--success">
              ✨
            </div>
          </div>
          <p>{t('detection.subtitle')}</p>
          <Link
            to="/cad/detection"
            className="app-home__cta home-overview__cta"
          >
            {t('nav.detection')}
          </Link>
        </article>

        {/* Business: Pipeline Worth */}
        <article className="app-home__card home-overview__pipeline-card">
          <div className="home-overview__pipeline-header">
            <h3 className="home-overview__pipeline-title">Total Pipeline</h3>
            <span className="home-overview__pipeline-change">+12.5% ↗</span>
          </div>
          <div className="home-overview__pipeline-value">$42.8M</div>
          <p className="home-overview__pipeline-desc">
            Weighted probability across 12 active deals.
          </p>
          {/* Sparkline Placeholder */}
          <div className="home-overview__sparkline">
            <div className="home-overview__sparkline-fill"></div>
            <svg width="100%" height="100%" preserveAspectRatio="none">
              <path
                d="M0,30 L50,20 L100,25 L150,10 L200,15 L250,5 L300,20"
                fill="none"
                stroke="var(--ob-brand-500)"
                strokeWidth="2"
              />
            </svg>
          </div>
          <Link
            to="/cad/pipelines"
            className="app-home__cta home-overview__pipeline-cta"
          >
            View Operations
          </Link>
        </article>

        {/* Business: ROI / Feasibility */}
        <article className="app-home__card">
          <div className="home-overview__card-header">
            <h3>{t('nav.feasibility')}</h3>
            <div className="home-overview__icon-badge home-overview__icon-badge--warning">
              🏗️
            </div>
          </div>
          <p>{t('home.cards.feasibility.description')}</p>
          <Link to="/feasibility" className="app-home__cta home-overview__cta">
            {t('nav.feasibility')}
          </Link>
        </article>

        {/* Business: Finance */}
        <article className="app-home__card">
          <div className="home-overview__card-header">
            <h3>{t('nav.finance')}</h3>
            <div className="home-overview__icon-badge home-overview__icon-badge--error">
              💰
            </div>
          </div>
          <p>{t('home.cards.finance.description')}</p>
          <Link to="/finance" className="app-home__cta home-overview__cta">
            {t('nav.finance')}
          </Link>
        </article>
      </div>
    </AppLayout>
  )
}

export default HomeOverview
