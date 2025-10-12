export type NavItemKey =
  | 'performance'
  | 'gpsCapture'
  | 'marketing'
  | 'advisory'
  | 'integrations'

export interface NavItem {
  key: NavItemKey
  label: string
  path: string
  description?: string
  comingSoon?: boolean
}

export const NAV_ITEMS: NavItem[] = [
  {
    key: 'performance',
    label: 'Business Performance',
    path: '/app/performance',
    description: 'Pipeline, commissions, analytics, and ROI benchmarks.',
  },
  {
    key: 'gpsCapture',
    label: 'GPS Capture',
    path: '/app/gps-capture',
    description: 'Mobile-first site capture and quick feasibility analysis.',
  },
  {
    key: 'marketing',
    label: 'Marketing Packs',
    path: '/app/marketing',
    description: 'Document generator for site packages and investment memos.',
  },
  {
    key: 'advisory',
    label: 'Advisory Console',
    path: '/app/advisory',
    description: 'Asset mix strategy, pricing guidance, and absorption insights.',
  },
  {
    key: 'integrations',
    label: 'Listing Integrations',
    path: '/app/integrations',
    description: 'Account linking and listing publication workflows.',
  },
]
