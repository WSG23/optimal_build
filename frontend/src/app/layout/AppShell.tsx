import {
  AppShell as BaseAppShell,
  AppShellProps as BaseAppShellProps,
} from '../../components/layout/YosaiShell'

interface AppShellProps extends Omit<BaseAppShellProps, 'subtitle'> {
  activeItem?: string // Kept for backward compatibility
  description?: string
}

export function AppShell({
  title,
  description,
  actions,
  children,
  hideSidebar,
}: AppShellProps) {
  return (
    <BaseAppShell
      title={title}
      subtitle={description}
      actions={actions}
      hideSidebar={hideSidebar}
    >
      {children}
    </BaseAppShell>
  )
}
