import type { ReactNode } from 'react'

import { useTranslation } from './i18n'
import { Link } from './router'
import { YosaiShell } from './components/layout/YosaiShell'

export interface AppLayoutProps {
  title: string
  subtitle?: string
  actions?: ReactNode
  children: ReactNode
}

export function AppLayout({
  title,
  subtitle,
  actions,
  children,
}: AppLayoutProps) {
  return (
    <YosaiShell title={title} subtitle={subtitle} actions={actions}>
      {children}
    </YosaiShell>
  )
}

export function HomeOverview() {
  const { t } = useTranslation()
  return (
    <AppLayout title={t('nav.home')} subtitle={t('app.tagline')}>
      <section className="app-home">
        <article className="app-home__card">
          <h3>{t('nav.upload')}</h3>
          <p>{t('uploader.subtitle')}</p>
          <Link to="/cad/upload" className="app-home__cta">
            {t('nav.upload')}
          </Link>
        </article>
        <article className="app-home__card">
          <h3>{t('nav.detection')}</h3>
          <p>{t('detection.subtitle')}</p>
          <Link to="/cad/detection" className="app-home__cta">
            {t('nav.detection')}
          </Link>
        </article>
        <article className="app-home__card">
          <h3>{t('nav.pipelines')}</h3>
          <p>{t('pipelines.subtitle')}</p>
          <Link to="/cad/pipelines" className="app-home__cta">
            {t('nav.pipelines')}
          </Link>
        </article>
        <article className="app-home__card">
          <h3>{t('nav.feasibility')}</h3>
          <p>{t('home.cards.feasibility.description')}</p>
          <Link to="/feasibility" className="app-home__cta">
            {t('nav.feasibility')}
          </Link>
        </article>
        <article className="app-home__card">
          <h3>{t('nav.finance')}</h3>
          <p>{t('home.cards.finance.description')}</p>
          <Link to="/finance" className="app-home__cta">
            {t('nav.finance')}
          </Link>
        </article>
      </section>
    </AppLayout>
  )
}

export default HomeOverview
