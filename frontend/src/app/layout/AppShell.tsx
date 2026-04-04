import {
  AppShell as BaseAppShell,
  AppShellProps as BaseAppShellProps,
} from '../../components/layout/YosaiShell'

interface AppShellProps extends Omit<BaseAppShellProps, 'subtitle'> {
  activeItem?: string // Kept for backward compatibility
  description?: string
  hideHeader?: boolean
  workspace?: 'agent' | 'developer'
}

export function AppShell({
  title,
  description,
  actions,
  children,
  hideSidebar,
  hideHeader,
  workspace,
}: AppShellProps) {
  return (
    <BaseAppShell
      title={title}
      subtitle={description}
      actions={actions}
      hideSidebar={hideSidebar}
      hideHeader={hideHeader}
      workspace={workspace}
    >
      {children}
    </BaseAppShell>
  )
}
