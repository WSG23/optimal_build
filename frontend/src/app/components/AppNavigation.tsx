import type { NavItem, NavItemKey } from '../navigation'
import { NAV_ITEMS } from '../navigation'

interface AppNavigationProps {
  activeItem: NavItemKey
  onNavigate: (path: string) => void
  currentPath: string
}

export function AppNavigation({
  activeItem,
  onNavigate,
  currentPath,
}: AppNavigationProps) {
  const handleClick = (path: string, disabled: boolean | undefined) => {
    if (disabled) {
      return
    }
    onNavigate(path)
  }

  const renderItem = (item: NavItem) => {
    const isActive = activeItem === item.key || currentPath === item.path
    const isDisabled = Boolean(item.comingSoon)
    const className = [
      'app-nav__item',
      isActive ? 'app-nav__item--active' : '',
      isDisabled ? 'app-nav__item--disabled' : '',
    ]
      .filter(Boolean)
      .join(' ')

    return (
      <li key={item.key} className={className}>
        <button
          type="button"
          onClick={() => handleClick(item.path, isDisabled)}
          disabled={isDisabled}
        >
          <span className="app-nav__label">{item.label}</span>
          {item.description && (
            <span className="app-nav__description">{item.description}</span>
          )}
          {item.comingSoon && (
            <span className="app-nav__badge">Coming soon</span>
          )}
        </button>
      </li>
    )
  }

  return (
    <nav className="app-nav" aria-label="Primary">
      <div className="app-nav__header">
        <span className="app-nav__product">Optimal Build Studio</span>
        <span className="app-nav__subheading">Agent workspace</span>
      </div>
      <ul className="app-nav__list">{NAV_ITEMS.map(renderItem)}</ul>
    </nav>
  )
}

