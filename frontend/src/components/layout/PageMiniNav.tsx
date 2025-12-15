import type { FC } from 'react'

export interface PageMiniNavItem {
  label: string
  to: string
}

export interface PageMiniNavProps {
  items: PageMiniNavItem[]
}

export const PageMiniNav: FC<PageMiniNavProps> = ({ items }) => {
  return (
    <nav className="flex items-center gap-3 text-xs uppercase tracking-wide text-white/60">
      {items.map((item) => (
        <a
          key={item.to}
          href={item.to}
          className="transition-colors hover:text-white"
        >
          {item.label}
        </a>
      ))}
    </nav>
  )
}

export default PageMiniNav
