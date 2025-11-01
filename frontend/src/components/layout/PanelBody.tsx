import type { PropsWithChildren } from 'react';

export interface PanelBodyProps extends PropsWithChildren {
  className?: string;
}

export function PanelBody({ className, children }: PanelBodyProps) {
  return <div className={`h-full w-full ${className ?? ''}`.trim()}>{children}</div>;
}
