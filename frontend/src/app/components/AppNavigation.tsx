import { useState } from 'react'
import type { NavItem, NavItemKey } from '../navigation'
import {
  AGENT_NAV_ITEMS,
  DEVELOPER_NAV_ITEMS,
  resolveNavPath,
} from '../navigation'
import { useDeveloperMode } from '../../contexts/useDeveloperMode'
import { useProject } from '../../contexts/useProject'

type Workspace = 'agent' | 'developer'

interface AppNavigationProps {
  activeItem: NavItemKey
  onNavigate: (path: string) => void
  currentPath: string
  workspace?: Workspace
}

export function AppNavigation({
  activeItem,
  onNavigate,
  currentPath,
  workspace,
}: AppNavigationProps) {
  const { isDeveloperMode } = useDeveloperMode()
  const { currentProject } = useProject()
  // Determine initial workspace based on active item
  const initialWorkspace: Workspace = DEVELOPER_NAV_ITEMS.find(
    (item) => item.key === activeItem,
  )
    ? 'developer'
    : 'agent'

  const [selectedWorkspace, setSelectedWorkspace] = useState<Workspace>(
    workspace ?? initialWorkspace,
  )
  const effectiveWorkspace = workspace ?? selectedWorkspace

  // Show items for selected workspace only
  const navItems = (
    effectiveWorkspace === 'agent' ? AGENT_NAV_ITEMS : DEVELOPER_NAV_ITEMS
  ).filter((item) => !item.comingSoon)

  const handleClick = (path: string, disabled: boolean | undefined) => {
    if (disabled) {
      return
    }
    onNavigate(path)
  }

  const handleWorkspaceSwitch = (workspace: Workspace) => {
    setSelectedWorkspace(workspace)
    // Navigate to first item of the selected workspace
    const firstItem =
      workspace === 'agent' ? AGENT_NAV_ITEMS[0] : DEVELOPER_NAV_ITEMS[0]
    onNavigate(resolveNavPath(firstItem, currentProject?.id))
  }

  const renderItem = (item: NavItem) => {
    const resolvedPath = resolveNavPath(item, currentProject?.id)
    const isActive = activeItem === item.key || currentPath === resolvedPath
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
          onClick={() => handleClick(resolvedPath, isDisabled)}
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
        <span className="app-nav__subheading">
          {effectiveWorkspace === 'agent'
            ? 'Agent workspace'
            : 'Singapore developer workspace'}
        </span>
      </div>

      {!workspace ? (
        <div className="app-nav__workspace-switcher">
          <button
            type="button"
            className={`app-nav__workspace-btn${selectedWorkspace === 'agent' ? ' app-nav__workspace-btn--active' : ''}`}
            onClick={() => handleWorkspaceSwitch('agent')}
          >
            Agent
          </button>
          <button
            type="button"
            className={`app-nav__workspace-btn${selectedWorkspace === 'developer' ? ' app-nav__workspace-btn--active' : ''}`}
            onClick={() => handleWorkspaceSwitch('developer')}
          >
            Developer
          </button>
        </div>
      ) : null}

      <ul className="app-nav__list">
        {navItems.map(renderItem)}
        {isDeveloperMode &&
          renderItem({
            key: 'developerConsole',
            label: 'Developer Console',
            path: '/developer',
            description: 'Debug tools & experiments',
            workspace: 'developer',
          })}
      </ul>
    </nav>
  )
}
