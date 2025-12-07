import type { PropsWithChildren, ReactNode } from 'react'

export interface PanelProps extends PropsWithChildren {
  title?: ReactNode
  className?: string
}

export default function Panel({ title, className, children }: PanelProps) {
  return (
    <section
      className={`rounded-lg border border-white/10 bg-neutral-900/70 shadow-inner ${className ?? ''}`.trim()}
    >
      {title ? (
        <header className="border-b border-white/10 px-4 py-3 text-sm font-semibold uppercase tracking-wide text-white/80">
          {title}
        </header>
      ) : null}
      {children}
    </section>
  )
}
