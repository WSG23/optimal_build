import { useMemo } from 'react'
import { NavLink } from 'react-router-dom'

import { useTranslation } from '../i18n'

const Sidebar = () => {
  const { t } = useTranslation()

  const navItems = useMemo(
    () => [
      { to: '/', label: t('sidebar.nav.sources') },
      { to: '/documents', label: t('sidebar.nav.documents') },
      { to: '/clauses', label: t('sidebar.nav.clauses') },
      { to: '/rules', label: t('sidebar.nav.rules') },
      { to: '/diffs', label: t('sidebar.nav.diffs') },
      { to: '/entitlements', label: t('sidebar.nav.entitlements') },
    ],
    [t],
  )

  return (
    <aside className="w-64 bg-slate-900 border-r border-slate-800">
      <div className="px-6 py-4 border-b border-slate-800">
        <h1 className="text-lg font-semibold">{t('sidebar.title')}</h1>
        <p className="text-xs text-slate-400">{t('sidebar.description')}</p>
      </div>
      <nav className="flex flex-col px-2 py-4 space-y-2">
        {navItems.map((item) => (
          <NavLink
            key={item.to}
            to={item.to}
            end={item.to === '/'}
            className={({ isActive }) =>
              `px-4 py-2 rounded-md text-sm font-medium transition-colors duration-150 ${
                isActive
                  ? 'bg-slate-700 text-white'
                  : 'text-slate-300 hover:bg-slate-800'
              }`
            }
          >
            {item.label}
          </NavLink>
        ))}
      </nav>
    </aside>
  )
}

export default Sidebar
