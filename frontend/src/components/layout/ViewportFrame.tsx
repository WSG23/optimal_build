import type { PropsWithChildren } from 'react'

export interface ViewportFrameProps extends PropsWithChildren {
  className?: string
}

export function ViewportFrame({ className, children }: ViewportFrameProps) {
  return (
    <div
      className={`mx-auto flex h-screen max-h-screen w-full max-w-[1600px] px-6 py-4 ${className ?? ''}`.trim()}
    >
      {children}
    </div>
  )
}
