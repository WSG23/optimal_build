import type { ReactNode } from 'react'

import { LocaleSwitcher } from './i18n/LocaleSwitcher'
import { useTranslation } from './i18n'
import { Link, useRouterPath } from './router'

export interface AppLayoutProps {
  title: string
  subtitle?: string
  actions?: ReactNode
  children: ReactNode
}

export function AppLayout({ title, subtitle, actions, children }: AppLayoutProps) {
  const { t } = useTranslation()
  const path = useRouterPath()

  const navItems = [
    { path: '/', label: t('nav.home') },
    { path: '/cad/upload', label: t('nav.upload') },
    { path: '/cad/detection', label: t('nav.detection') },
    { path: '/cad/pipelines', label: t('nav.pipelines') },
    { path: '/feasibility', label: t('nav.feasibility') },
  ]

  return (
    <div className="app-layout">
      <aside className="app-layout__nav">
        <div className="app-layout__brand">
          <h1>{t('app.title')}</h1>
          <p>{t('app.tagline')}</p>
        </div>
        <nav>
          <ul>
            {navItems.map((item) => {
              const isActive = item.path === '/' ? path === '/' : path.startsWith(item.path)
              return (
                <li key={item.path}>
                  <Link
                    to={item.path}
                    className={`app-layout__nav-link${
                      isActive ? ' app-layout__nav-link--active' : ''
                    }`}
                  >
                    {item.label}
                  </Link>
                </li>
              )
            })}
          </ul>
        </nav>
      </aside>
      <main className="app-layout__main">
        <header className="app-layout__header">
          <div>
            <h2>{title}</h2>
            {subtitle && <p>{subtitle}</p>}
          </div>
          <div className="app-layout__toolbar">
            <LocaleSwitcher />
            {actions}
          </div>
        </header>
        <div className="app-layout__content">{children}</div>
      </main>
    </div>
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
      </section>
    </AppLayout>
  )
}

export default HomeOverview
