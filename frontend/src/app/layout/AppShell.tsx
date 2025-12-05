import { YosaiShell, YosaiShellProps } from '../../components/layout/YosaiShell'

interface AppShellProps extends Omit<YosaiShellProps, 'subtitle'> {
  activeItem?: string // Kept for backward compatibility, but YosaiShell uses router path
  description?: string
}

export function AppShell({
  title,
  description,
  actions,
  children,
}: AppShellProps) {
  return (
    <YosaiShell title={title} subtitle={description} actions={actions}>
      {children}
    </YosaiShell>
  )
}
