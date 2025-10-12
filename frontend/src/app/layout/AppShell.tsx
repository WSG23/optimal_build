import type { ReactNode } from 'react'
import type { NavItemKey } from '../navigation'
import { AppNavigation } from '../components/AppNavigation'
import { useRouterController } from '../../router'

interface AppShellProps {
  activeItem: NavItemKey
  title: string
  description?: string
  actions?: ReactNode
  children: ReactNode
}

export function AppShell({
  activeItem,
  title,
  description,
  actions,
  children,
}: AppShellProps) {
  const router = useRouterController()
  return (
    <div className="app-shell">
      <aside className="app-shell__sidebar">
        <AppNavigation
          activeItem={activeItem}
          currentPath={router?.path ?? '/'}
          onNavigate={(path) => router?.navigate(path)}
        />
      </aside>
      <div className="app-shell__main">
        <header className="app-shell__header">
          <div>
            <h1>{title}</h1>
            {description && <p className="app-shell__subtitle">{description}</p>}
          </div>
          {actions && <div className="app-shell__actions">{actions}</div>}
        </header>
        <main className="app-shell__content">{children}</main>
      </div>
    </div>
  )
}
