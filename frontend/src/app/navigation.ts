export type NavItemKey =
  | 'performance'
  | 'gpsCapture'
  | 'marketing'
  | 'advisory'
  | 'integrations'
  | 'siteAcquisition'
  | 'assetFeasibility'
  | 'financialControl'
  | 'phaseManagement'
  | 'teamCoordination'
  | 'regulatory'
  | 'construction'
  | 'revenueOptimization'
  | 'documentation'

export interface NavItem {
  key: NavItemKey
  label: string
  path: string
  description?: string
  comingSoon?: boolean
  workspace?: 'agent' | 'developer'
}

// Agent Workspace Tools (Phase 1)
export const AGENT_NAV_ITEMS: NavItem[] = [
  {
    key: 'performance',
    label: 'Business Performance',
    path: '/app/performance',
    description: 'Pipeline, commissions, analytics, and ROI benchmarks.',
    workspace: 'agent',
  },
  {
    key: 'gpsCapture',
    label: 'GPS Capture',
    path: '/app/gps-capture',
    description: 'Mobile-first site capture and quick feasibility analysis.',
    workspace: 'agent',
  },
  {
    key: 'marketing',
    label: 'Marketing Packs',
    path: '/app/marketing',
    description: 'Document generator for site packages and investment memos.',
    workspace: 'agent',
  },
  {
    key: 'advisory',
    label: 'Advisory Console',
    path: '/app/advisory',
    description: 'Asset mix strategy, pricing guidance, and absorption insights.',
    workspace: 'agent',
  },
  {
    key: 'integrations',
    label: 'Listing Integrations',
    path: '/app/integrations',
    description: 'Account linking and listing publication workflows.',
    workspace: 'agent',
  },
]

// Developer Workspace Tools (Phase 2)
export const DEVELOPER_NAV_ITEMS: NavItem[] = [
  {
    key: 'siteAcquisition',
    label: 'Site Acquisition',
    path: '/app/site-acquisition',
    description: 'GPS capture and comprehensive due diligence for developers.',
    workspace: 'developer',
  },
  {
    key: 'assetFeasibility',
    label: 'Asset Feasibility',
    path: '/app/asset-feasibility',
    description: 'Multi-use optimizer and asset-specific modeling.',
    workspace: 'developer',
  },
  {
    key: 'financialControl',
    label: 'Financial Control',
    path: '/app/financial-control',
    description: 'Development economics and financing architecture.',
    workspace: 'developer',
  },
  {
    key: 'phaseManagement',
    label: 'Phase Management',
    path: '/app/phase-management',
    description: 'Multi-phase development and renovation sequencing.',
    workspace: 'developer',
  },
  {
    key: 'teamCoordination',
    label: 'Team Coordination',
    path: '/app/team-coordination',
    description: 'Consultant network and approval workflows.',
    workspace: 'developer',
    comingSoon: true,
  },
  {
    key: 'regulatory',
    label: 'Regulatory Navigation',
    path: '/app/regulatory',
    description: 'Multi-authority coordination and compliance tracking.',
    workspace: 'developer',
    comingSoon: true,
  },
  {
    key: 'construction',
    label: 'Construction Delivery',
    path: '/app/construction',
    description: 'Project delivery and contractor coordination.',
    workspace: 'developer',
    comingSoon: true,
  },
  {
    key: 'revenueOptimization',
    label: 'Revenue Optimization',
    path: '/app/revenue-optimization',
    description: 'Sales/leasing management and exit strategy.',
    workspace: 'developer',
    comingSoon: true,
  },
  {
    key: 'documentation',
    label: 'Export & Documentation',
    path: '/app/documentation',
    description: 'Capital raise materials and authority submissions.',
    workspace: 'developer',
    comingSoon: true,
  },
]

// Combined navigation (temporary - will add workspace switcher later)
// Shows both Agent and Developer tools for now
export const NAV_ITEMS: NavItem[] = [
  ...AGENT_NAV_ITEMS,
  ...DEVELOPER_NAV_ITEMS,
]
