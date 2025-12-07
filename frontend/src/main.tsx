import React from 'react'
import ReactDOM from 'react-dom/client'
import { createBrowserRouter, RouterProvider } from './router'
import { HomeOverview } from './App'
import { TranslationProvider } from './i18n'
import { DeveloperProvider } from './contexts/DeveloperContext'
import { CadDetectionPage } from './pages/CadDetectionPage'
import { CadPipelinesPage } from './pages/CadPipelinesPage'
import { CadUploadPage } from './pages/CadUploadPage'
import AgentsGpsCapturePage from './pages/AgentsGpsCapturePage'
import { FeasibilityWizard } from './modules/feasibility/FeasibilityWizard'
import { FinanceWorkspace } from './modules/finance'
import AdvancedIntelligencePage from './pages/visualizations/AdvancedIntelligence'
import { AppThemeProvider } from './theme/YosaiThemeProvider'
import '@ob/tokens.css'
import './styles/index.css'
import AgentAdvisoryPage from './pages/AgentAdvisoryPage'
import AgentIntegrationsPage from './pages/AgentIntegrationsPage'
import AgentPerformancePage from './pages/AgentPerformancePage'
import { AppShell } from './app/layout/AppShell'
import { BaseLayout } from './app/layout/BaseLayout'
import { BusinessPerformancePage } from './app/pages/business-performance/BusinessPerformancePage'
import { GpsCapturePage } from './app/pages/gps-capture/GpsCapturePage'
import { MarketingPage } from './app/pages/marketing/MarketingPage'
import { AdvisoryPage } from './app/pages/advisory/AdvisoryPage'
import { IntegrationsPage } from './app/pages/integrations/IntegrationsPage'
import { SiteAcquisitionPage } from './app/pages/site-acquisition/SiteAcquisitionPage'
import { ChecklistTemplateManager } from './app/pages/site-acquisition/ChecklistTemplateManager'
import { DeveloperPreviewStandalone } from './app/pages/site-acquisition/DeveloperPreviewStandalone'
import { PhaseManagementPage } from './app/pages/phase-management'
import { TeamManagementPage } from './app/pages/team/TeamManagementPage'
import { RegulatoryDashboardPage } from './app/pages/regulatory/RegulatoryDashboardPage'
import { DeveloperControlPanel } from './app/pages/developer/DeveloperControlPanel'

const hash = window.location.hash
if (hash.startsWith('#/')) {
  const targetPath = hash.slice(1)
  window.history.replaceState(null, '', targetPath)
}

const businessPerformanceElement = (
  <AppShell
    activeItem="performance"
    title="Business performance"
    description="Track deal momentum, commissions, analytics, and automation ROI across your Singapore commercial pipeline."
    hideSidebar
  >
    <BusinessPerformancePage />
  </AppShell>
)

const gpsCaptureElement = (
  <AppShell
    activeItem="gpsCapture"
    title="GPS capture & quick analysis"
    description="Capture sites in the field, run instant scenario analysis, review market intelligence, and generate marketing packs."
    hideSidebar
  >
    <GpsCapturePage />
  </AppShell>
)

const marketingElement = (
  <AppShell
    activeItem="marketing"
    title="Marketing packs"
    description="Generate, track, and share professional marketing packs for developers and investors."
    hideSidebar
  >
    <MarketingPage />
  </AppShell>
)

const advisoryElement = (
  <AppShell
    activeItem="advisory"
    title="Advisory console"
    description="Review asset mix strategy, pricing guidance, absorption forecasts, and market feedback in one workspace."
    hideSidebar
  >
    <AdvisoryPage />
  </AppShell>
)

const integrationsElement = (
  <AppShell
    activeItem="integrations"
    title="Listing integrations"
    description="Connect PropertyGuru, EdgeProp, Zoho, and future portals to publish and monitor listings."
    hideSidebar
  >
    <IntegrationsPage />
  </AppShell>
)

const siteAcquisitionElement = (
  <AppShell
    activeItem="siteAcquisition"
    title="Site acquisition"
    description="Comprehensive property capture and development feasibility analysis for developers."
    hideSidebar
  >
    <SiteAcquisitionPage />
  </AppShell>
)

const developerPreviewStandaloneElement = (
  <AppShell
    activeItem="siteAcquisition"
    title="Developer preview"
    description="Standalone preview viewer for manual QA of Phase 2B renders."
    hideSidebar
  >
    <DeveloperPreviewStandalone />
  </AppShell>
)

const checklistTemplateManagerElement = (
  <AppShell
    activeItem="siteAcquisition"
    title="Checklist templates"
    description="Author and import scenario-specific due diligence checklists."
    hideSidebar
  >
    <ChecklistTemplateManager />
  </AppShell>
)

const developerFeasibilityElement = (
  <AppShell
    activeItem="assetFeasibility"
    title="Feasibility workspace"
    description="Run feasibility checks, document pack generation, and advisory workflows."
    hideSidebar
  >
    <FeasibilityWizard withLayout={false} />
  </AppShell>
)

const financialControlElement = <FinanceWorkspace />

const phaseManagementElement = (
  <AppShell
    activeItem="phaseManagement"
    title="Phase management"
    description="Multi-phase development scheduling, heritage tracking, and tenant coordination."
    hideSidebar
  >
    <PhaseManagementPage />
  </AppShell>
)

const teamCoordinationElement = (
  <AppShell
    activeItem="teamCoordination"
    title="Team coordination"
    description="Manage project team, consultants, and approval workflows."
    hideSidebar
  >
    <TeamManagementPage />
  </AppShell>
)

const regulatoryNavigationElement = (
  <AppShell
    activeItem="regulatoryNavigation"
    title="Regulatory Navigation"
    description="Singapore authority submissions and compliance tracking."
    hideSidebar
  >
    <RegulatoryDashboardPage />
  </AppShell>
)

const developerControlPanelElement = (
  <AppShell
    activeItem="performance"
    title="Developer Console"
    description="Internal tools and configuration."
  >
    <DeveloperControlPanel />
  </AppShell>
)

const router = createBrowserRouter([
  {
    path: '/',
    element: businessPerformanceElement,
  },
  {
    path: '/app/performance',
    element: businessPerformanceElement,
  },
  {
    path: '/agents/performance',
    element: businessPerformanceElement,
  },
  {
    path: '/app/gps-capture',
    element: gpsCaptureElement,
  },
  {
    path: '/agents/site-capture',
    element: gpsCaptureElement,
  },
  {
    path: '/app/marketing',
    element: marketingElement,
  },
  {
    path: '/agents/marketing',
    element: marketingElement,
  },
  {
    path: '/app/advisory',
    element: advisoryElement,
  },
  {
    path: '/agents/advisory',
    element: advisoryElement,
  },
  {
    path: '/app/integrations',
    element: integrationsElement,
  },
  {
    path: '/agents/integrations',
    element: integrationsElement,
  },
  {
    path: '/app/site-acquisition',
    element: siteAcquisitionElement,
  },
  {
    path: '/developers/site-acquisition',
    element: siteAcquisitionElement,
  },
  {
    path: '/agents/developers/:propertyId/preview',
    element: developerPreviewStandaloneElement,
  },
  {
    path: '/app/site-acquisition/checklist-templates',
    element: checklistTemplateManagerElement,
  },
  {
    path: '/app/asset-feasibility',
    element: developerFeasibilityElement,
  },
  {
    path: '/developers/asset-feasibility',
    element: developerFeasibilityElement,
  },
  {
    path: '/app/financial-control',
    element: financialControlElement,
  },
  {
    path: '/developers/financial-control',
    element: financialControlElement,
  },
  {
    path: '/developers/finance',
    element: financialControlElement,
  },
  {
    path: '/app/phase-management',
    element: phaseManagementElement,
  },
  {
    path: '/app/team-coordination',
    element: teamCoordinationElement,
  },
  {
    path: '/developers/team-coordination',
    element: teamCoordinationElement,
  },
  {
    path: '/app/regulatory',
    element: regulatoryNavigationElement,
  },
  {
    path: '/developers/regulatory',
    element: regulatoryNavigationElement,
  },
  {
    path: '/projects/:projectId/regulatory',
    element: regulatoryNavigationElement,
  },
  {
    path: '/developer',
    element: developerControlPanelElement,
  },
  {
    path: '/legacy/home',
    element: <HomeOverview />,
  },
  {
    path: '/legacy/cad/upload',
    element: <CadUploadPage />,
  },
  {
    path: '/legacy/cad/detection',
    element: <CadDetectionPage />,
  },
  {
    path: '/legacy/cad/pipelines',
    element: <CadPipelinesPage />,
  },
  {
    path: '/cad/pipelines',
    element: <CadPipelinesPage />,
  },
  {
    path: '/cad/upload',
    element: <CadUploadPage />,
  },
  {
    path: '/cad/detection',
    element: <CadDetectionPage />,
  },
  {
    path: '/legacy/feasibility',
    element: developerFeasibilityElement,
  },
  {
    path: '/feasibility',
    element: developerFeasibilityElement,
  },
  {
    path: '/finance',
    element: financialControlElement,
  },
  {
    path: '/legacy/finance',
    element: financialControlElement,
  },
  {
    path: '/legacy/agents/site-capture',
    element: <AgentsGpsCapturePage />,
  },
  {
    path: '/legacy/agents/advisory',
    element: <AgentAdvisoryPage />,
  },
  {
    path: '/legacy/agents/integrations',
    element: <AgentIntegrationsPage />,
  },
  {
    path: '/legacy/agents/performance',
    element: <AgentPerformancePage />,
  },
  {
    path: '/visualizations/intelligence',
    element: <AdvancedIntelligencePage />,
  },
  {
    path: '/legacy/visualizations/intelligence',
    element: <AdvancedIntelligencePage />,
  },
])

const container = document.getElementById('root')

if (!container) {
  throw new Error('Root element with id "root" not found')
}

ReactDOM.createRoot(container).render(
  <React.StrictMode>
    <TranslationProvider>
      <AppThemeProvider>
        <DeveloperProvider>
          <RouterProvider router={router} layout={BaseLayout} />
        </DeveloperProvider>
      </AppThemeProvider>
    </TranslationProvider>
  </React.StrictMode>,
)
