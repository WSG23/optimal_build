import type { ReactNode } from 'react'

import { Link, useRouterPath } from './router'
import { useLocale } from './i18n/LocaleContext'
import type { Locale } from './i18n/strings'

export interface AppLayoutProps {
  title: string
  subtitle?: string
  actions?: ReactNode
  children: ReactNode
}

export function AppLayout({ title, subtitle, actions, children }: AppLayoutProps) {
  const { locale, strings, setLocale } = useLocale()
  const path = useRouterPath()

  const navItems = [
    { path: '/', label: strings.nav.home },
    { path: '/cad/upload', label: strings.nav.upload },
    { path: '/cad/detection', label: strings.nav.detection },
    { path: '/cad/pipelines', label: strings.nav.pipelines },
    { path: '/feasibility', label: strings.nav.feasibility },
  ]

  return (
    <div className="app-layout">
      <aside className="app-layout__nav">
        <div className="app-layout__brand">
          <h1>{strings.app.title}</h1>
          <p>{strings.app.tagline}</p>
        </div>
        <nav>
          <ul>
            {navItems.map((item) => {
              const isActive = item.path === '/' ? path === '/' : path.startsWith(item.path)
              return (
                <li key={item.path}>
                  <Link
                    to={item.path}
                    className={`app-layout__nav-link${isActive ? ' app-layout__nav-link--active' : ''}`}
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
            <label className="app-layout__locale">
              <span className="sr-only">{strings.app.helper}</span>
              <select value={locale} onChange={(event) => setLocale(event.target.value as Locale)}>
                <option value="en">EN</option>
                <option value="zh">中文</option>
              </select>
            </label>
            {actions}
          </div>
        </header>
        <div className="app-layout__content">{children}</div>
      </main>
    </div>
  )
}

export function HomeOverview() {
  const { strings } = useLocale()
  return (
    <AppLayout title={strings.nav.home} subtitle={strings.app.tagline}>
      <section className="app-home">
        <article className="app-home__card">
          <h3>{strings.nav.upload}</h3>
          <p>{strings.uploader.subtitle}</p>
          <Link to="/cad/upload" className="app-home__cta">
            {strings.nav.upload}
          </Link>
        </article>
        <article className="app-home__card">
          <h3>{strings.nav.detection}</h3>
          <p>{strings.detection.subtitle}</p>
          <Link to="/cad/detection" className="app-home__cta">
            {strings.nav.detection}
          </Link>
        </article>
        <article className="app-home__card">
          <h3>{strings.nav.pipelines}</h3>
          <p>{strings.pipelines.subtitle}</p>
          <Link to="/cad/pipelines" className="app-home__cta">
            {strings.nav.pipelines}
          </Link>
        </article>
        <article className="app-home__card">
          <h3>{strings.nav.feasibility}</h3>
          <p>Kick off planning studies with project context, rule packs and buildability checks.</p>
          <Link to="/feasibility" className="app-home__cta">
            {strings.nav.feasibility}
          </Link>
        </article>
      </section>
    </AppLayout>
  )
}

export default HomeOverview
