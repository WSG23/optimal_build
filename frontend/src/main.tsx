import React from 'react'
import ReactDOM from 'react-dom/client'
import { createBrowserRouter, RouterProvider } from './router'
import { HomeOverview } from './App'
import { TranslationProvider } from './i18n'
import { DeveloperProvider } from './contexts/DeveloperContext'
import { AppThemeProvider } from './theme/YosaiThemeProvider'
import '@ob/tokens.css'
import './styles/index.css'
import './styles/premium-effects.css'
import { AppShell } from './app/layout/AppShell'
import { BaseLayout } from './app/layout/BaseLayout'

const hash = window.location.hash
if (hash.startsWith('#/')) {
  const targetPath = hash.slice(1)
  window.history.replaceState(null, '', targetPath)
}

function suspense(element: React.ReactNode) {
  return <React.Suspense fallback={null}>{element}</React.Suspense>
}

const CadDetectionPage = React.lazy(async () => {
  const module = await import('./pages/CadDetectionPage')
  return { default: module.CadDetectionPage }
})
const CadPipelinesPage = React.lazy(async () => {
  const module = await import('./pages/CadPipelinesPage')
  return { default: module.CadPipelinesPage }
})
const CadUploadPage = React.lazy(async () => {
  const module = await import('./pages/CadUploadPage')
  return { default: module.CadUploadPage }
})
const AgentsGpsCapturePage = React.lazy(
  () => import('./pages/AgentsGpsCapturePage'),
)
const FeasibilityWizard = React.lazy(async () => {
  const module = await import('./modules/feasibility/FeasibilityWizard')
  return { default: module.FeasibilityWizard }
})
const FinanceWorkspace = React.lazy(() => import('./modules/finance'))
const AdvancedIntelligencePage = React.lazy(
  () => import('./pages/visualizations/AdvancedIntelligence'),
)
const AgentAdvisoryPage = React.lazy(() => import('./pages/AgentAdvisoryPage'))
const AgentIntegrationsPage = React.lazy(
  () => import('./pages/AgentIntegrationsPage'),
)
const AgentPerformancePage = React.lazy(
  () => import('./pages/AgentPerformancePage'),
)
const BusinessPerformancePage = React.lazy(async () => {
  const module =
    await import('./app/pages/business-performance/BusinessPerformancePage')
  return { default: module.BusinessPerformancePage }
})
const UnifiedCapturePage = React.lazy(async () => {
  const module = await import('./app/pages/capture/UnifiedCapturePage')
  return { default: module.UnifiedCapturePage }
})
const MarketingPage = React.lazy(async () => {
  const module = await import('./app/pages/marketing/MarketingPage')
  return { default: module.MarketingPage }
})
const AdvisoryPage = React.lazy(async () => {
  const module = await import('./app/pages/advisory/AdvisoryPage')
  return { default: module.AdvisoryPage }
})
const IntegrationsPage = React.lazy(async () => {
  const module = await import('./app/pages/integrations/IntegrationsPage')
  return { default: module.IntegrationsPage }
})
const ChecklistTemplateManager = React.lazy(async () => {
  const module =
    await import('./app/pages/site-acquisition/ChecklistTemplateManager')
  return { default: module.ChecklistTemplateManager }
})
const DeveloperPreviewStandalone = React.lazy(async () => {
  const module =
    await import('./app/pages/site-acquisition/DeveloperPreviewStandalone')
  return { default: module.DeveloperPreviewStandalone }
})
const PhaseManagementPage = React.lazy(async () => {
  const module = await import('./app/pages/phase-management')
  return { default: module.PhaseManagementPage }
})
const TeamManagementPage = React.lazy(async () => {
  const module = await import('./app/pages/team/TeamManagementPage')
  return { default: module.TeamManagementPage }
})
const RegulatoryDashboardPage = React.lazy(async () => {
  const module = await import('./app/pages/regulatory/RegulatoryDashboardPage')
  return { default: module.RegulatoryDashboardPage }
})
const DeveloperControlPanel = React.lazy(async () => {
  const module = await import('./app/pages/developer/DeveloperControlPanel')
  return { default: module.DeveloperControlPanel }
})

const businessPerformanceElement = (
  <AppShell activeItem="performance" hideSidebar hideHeader>
    {suspense(<BusinessPerformancePage />)}
  </AppShell>
)

// Unified capture page - consolidates GPS Capture and Site Acquisition
const unifiedCaptureElement = (
  <AppShell activeItem="capture" hideSidebar hideHeader>
    {suspense(<UnifiedCapturePage />)}
  </AppShell>
)

const marketingElement = (
  <AppShell
    activeItem="marketing"
    title="Marketing packs"
    description="Generate, track, and share professional marketing packs for developers and investors."
    hideSidebar
  >
    {suspense(<MarketingPage />)}
  </AppShell>
)

const advisoryElement = (
  <AppShell
    activeItem="advisory"
    title="Advisory console"
    description="Review asset mix strategy, pricing guidance, absorption forecasts, and market feedback in one workspace."
    hideSidebar
  >
    {suspense(<AdvisoryPage />)}
  </AppShell>
)

const integrationsElement = (
  <AppShell
    activeItem="integrations"
    title="Listing integrations"
    description="Connect PropertyGuru, EdgeProp, Zoho, and future portals to publish and monitor listings."
    hideSidebar
  >
    {suspense(<IntegrationsPage />)}
  </AppShell>
)

const developerPreviewStandaloneElement = (
  <AppShell
    activeItem="siteAcquisition"
    title="Developer preview"
    description="Standalone preview viewer for manual QA of Phase 2B renders."
    hideSidebar
  >
    {suspense(<DeveloperPreviewStandalone />)}
  </AppShell>
)

const checklistTemplateManagerElement = (
  <AppShell
    activeItem="siteAcquisition"
    title="Checklist templates"
    description="Author and import scenario-specific due diligence checklists."
    hideSidebar
  >
    {suspense(<ChecklistTemplateManager />)}
  </AppShell>
)

const developerFeasibilityElement = (
  <AppShell
    activeItem="assetFeasibility"
    title="Feasibility"
    description="Run feasibility checks, document pack generation, and advisory workflows."
    hideSidebar
  >
    {suspense(<FeasibilityWizard withLayout={false} />)}
  </AppShell>
)

const financialControlElement = suspense(<FinanceWorkspace />)

const phaseManagementElement = (
  <AppShell activeItem="phaseManagement" hideSidebar hideHeader>
    {suspense(<PhaseManagementPage />)}
  </AppShell>
)

const teamCoordinationElement = (
  <AppShell activeItem="teamCoordination" hideSidebar hideHeader>
    {suspense(<TeamManagementPage />)}
  </AppShell>
)

const regulatoryNavigationElement = (
  <AppShell activeItem="regulatoryNavigation" hideSidebar hideHeader>
    {suspense(<RegulatoryDashboardPage />)}
  </AppShell>
)

const developerControlPanelElement = (
  <AppShell
    activeItem="performance"
    title="Developer Console"
    description="Internal tools and configuration."
  >
    {suspense(<DeveloperControlPanel />)}
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
  // Unified capture page - all capture routes point to the same unified experience
  {
    path: '/app/capture',
    element: unifiedCaptureElement,
  },
  {
    path: '/app/gps-capture',
    element: unifiedCaptureElement,
  },
  {
    path: '/agents/site-capture',
    element: unifiedCaptureElement,
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
    element: unifiedCaptureElement,
  },
  {
    path: '/developers/site-acquisition',
    element: unifiedCaptureElement,
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
    element: suspense(<CadUploadPage />),
  },
  {
    path: '/legacy/cad/detection',
    element: suspense(<CadDetectionPage />),
  },
  {
    path: '/legacy/cad/pipelines',
    element: suspense(<CadPipelinesPage />),
  },
  {
    path: '/cad/pipelines',
    element: suspense(<CadPipelinesPage />),
  },
  {
    path: '/cad/upload',
    element: suspense(<CadUploadPage />),
  },
  {
    path: '/cad/detection',
    element: suspense(<CadDetectionPage />),
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
    element: suspense(<AgentsGpsCapturePage />),
  },
  {
    path: '/legacy/agents/advisory',
    element: suspense(<AgentAdvisoryPage />),
  },
  {
    path: '/legacy/agents/integrations',
    element: suspense(<AgentIntegrationsPage />),
  },
  {
    path: '/legacy/agents/performance',
    element: suspense(<AgentPerformancePage />),
  },
  {
    path: '/visualizations/intelligence',
    element: suspense(<AdvancedIntelligencePage />),
  },
  {
    path: '/legacy/visualizations/intelligence',
    element: suspense(<AdvancedIntelligencePage />),
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
