import type { ReactNode } from 'react';
import PageMiniNav, { type PageMiniNavItem } from '@/components/layout/PageMiniNav';
import ClockTicker from '@/shared/components/app/security/ClockTicker';
import logoSrc from '@/shared/media/yosai-logo';
import { ZEN_MINI_NAV_ITEMS } from './zenMiniNavItems';

interface ZenPageHeaderProps {
  title: string;
  centerSlot?: ReactNode;
  miniNavItems?: PageMiniNavItem[];
}

export function ZenPageHeader({ title, centerSlot, miniNavItems = ZEN_MINI_NAV_ITEMS }: ZenPageHeaderProps) {
  return (
    <header className="mb-4 grid grid-cols-12 items-center gap-6">
      <div className="col-span-3 flex items-center gap-3">
        <img src={logoSrc} alt="YŌSAI INTEL" className="h-7 select-none" />
      </div>
      <div className="col-span-6">
        {centerSlot ?? (
          <h1 className="text-center text-2xl font-semibold">
            {title}
          </h1>
        )}
      </div>
      <div className="col-span-3 flex items-center justify-end gap-4">
        <PageMiniNav items={miniNavItems} />
        <ClockTicker />
      </div>
    </header>
  );
}

export default ZenPageHeader;
