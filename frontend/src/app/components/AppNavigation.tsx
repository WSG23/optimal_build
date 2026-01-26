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
}

export function AppNavigation({
  activeItem,
  onNavigate,
  currentPath,
}: AppNavigationProps) {
  const { isDeveloperMode } = useDeveloperMode()
  const { currentProject } = useProject()
  // Determine initial workspace based on active item
  const initialWorkspace: Workspace = DEVELOPER_NAV_ITEMS.find(
    (item) => item.key === activeItem,
  )
    ? 'developer'
    : 'agent'

  const [selectedWorkspace, setSelectedWorkspace] =
    useState<Workspace>(initialWorkspace)

  // Show items for selected workspace only
  const navItems = (
    selectedWorkspace === 'agent' ? AGENT_NAV_ITEMS : DEVELOPER_NAV_ITEMS
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
          {selectedWorkspace === 'agent'
            ? 'Agent workspace'
            : 'Developer workspace'}
        </span>
      </div>

      {/* Workspace Switcher */}
      <div
        style={{
          display: 'flex',
          gap: 'var(--ob-space-100)',
          padding: 'var(--ob-space-150) 1rem',
          borderBottom: '1px solid var(--ob-color-surface-overlay)',
        }}
      >
        <button
          type="button"
          onClick={() => handleWorkspaceSwitch('agent')}
          style={{
            flex: 1,
            padding: 'var(--ob-space-100)',
            fontSize: '0.875rem',
            fontWeight: 500,
            color:
              selectedWorkspace === 'agent'
                ? '#fff'
                : 'rgba(255, 255, 255, 0.6)',
            background:
              selectedWorkspace === 'agent'
                ? 'var(--ob-color-surface-overlay)'
                : 'transparent',
            border: '1px solid var(--ob-color-surface-overlay-medium)',
            borderRadius: 'var(--ob-radius-md)',
            cursor: 'pointer',
            transition: 'all 0.2s ease',
          }}
        >
          Agent
        </button>
        <button
          type="button"
          onClick={() => handleWorkspaceSwitch('developer')}
          style={{
            flex: 1,
            padding: 'var(--ob-space-100)',
            fontSize: '0.875rem',
            fontWeight: 500,
            color:
              selectedWorkspace === 'developer'
                ? '#fff'
                : 'rgba(255, 255, 255, 0.6)',
            background:
              selectedWorkspace === 'developer'
                ? 'var(--ob-color-surface-overlay)'
                : 'transparent',
            border: '1px solid var(--ob-color-surface-overlay-medium)',
            borderRadius: 'var(--ob-radius-md)',
            cursor: 'pointer',
            transition: 'all 0.2s ease',
          }}
        >
          Developer
        </button>
      </div>

      <ul className="app-nav__list">
        {navItems.map(renderItem)}
        {isDeveloperMode &&
          renderItem({
            key: 'developer_console' as unknown as NavItemKey,
            label: 'Developer Console',
            path: '/developer',
            description: 'Debug tools & experiments',
            workspace: 'developer',
          })}
      </ul>
    </nav>
  )
}
