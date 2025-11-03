import React from 'react'
import ReactDOM from 'react-dom/client'
import { createBrowserRouter, RouterProvider } from './router'
import { HomeOverview } from './App'
import { TranslationProvider } from './i18n'
import { CadDetectionPage } from './pages/CadDetectionPage'
import { CadPipelinesPage } from './pages/CadPipelinesPage'
import { CadUploadPage } from './pages/CadUploadPage'
import AgentsGpsCapturePage from './pages/AgentsGpsCapturePage'
import { FeasibilityWizard } from './modules/feasibility/FeasibilityWizard'
import { FinanceWorkspace } from './modules/finance'
import AdvancedIntelligencePage from './pages/visualizations/AdvancedIntelligence'
import '@ob/tokens.css'
import './index.css'
import AgentAdvisoryPage from './pages/AgentAdvisoryPage'
import AgentIntegrationsPage from './pages/AgentIntegrationsPage'
import AgentPerformancePage from './pages/AgentPerformancePage'
import { AppShell } from './app/layout/AppShell'
import { BusinessPerformancePage } from './app/pages/business-performance/BusinessPerformancePage'
import { GpsCapturePage } from './app/pages/gps-capture/GpsCapturePage'
import { MarketingPage } from './app/pages/marketing/MarketingPage'
import { AdvisoryPage } from './app/pages/advisory/AdvisoryPage'
import { IntegrationsPage } from './app/pages/integrations/IntegrationsPage'
import { SiteAcquisitionPage } from './app/pages/site-acquisition/SiteAcquisitionPage'
import { ChecklistTemplateManager } from './app/pages/site-acquisition/ChecklistTemplateManager'
import { DeveloperPreviewStandalone } from './app/pages/site-acquisition/DeveloperPreviewStandalone'

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
  >
    <BusinessPerformancePage />
  </AppShell>
)

const gpsCaptureElement = (
  <AppShell
    activeItem="gpsCapture"
    title="GPS capture & quick analysis"
    description="Capture sites in the field, run instant scenario analysis, review market intelligence, and generate marketing packs."
  >
    <GpsCapturePage />
  </AppShell>
)

const marketingElement = (
  <AppShell
    activeItem="marketing"
    title="Marketing packs"
    description="Generate, track, and share professional marketing packs for developers and investors."
  >
    <MarketingPage />
  </AppShell>
)

const advisoryElement = (
  <AppShell
    activeItem="advisory"
    title="Advisory console"
    description="Review asset mix strategy, pricing guidance, absorption forecasts, and market feedback in one workspace."
  >
    <AdvisoryPage />
  </AppShell>
)

const integrationsElement = (
  <AppShell
    activeItem="integrations"
    title="Listing integrations"
    description="Connect PropertyGuru, EdgeProp, Zoho, and future portals to publish and monitor listings."
  >
    <IntegrationsPage />
  </AppShell>
)

const siteAcquisitionElement = (
  <AppShell
    activeItem="siteAcquisition"
    title="Site acquisition"
    description="Comprehensive property capture and development feasibility analysis for developers."
  >
    <SiteAcquisitionPage />
  </AppShell>
)

const developerPreviewStandaloneElement = (
  <AppShell
    activeItem="siteAcquisition"
    title="Developer preview"
    description="Standalone preview viewer for manual QA of Phase 2B renders."
  >
    <DeveloperPreviewStandalone />
  </AppShell>
)

const checklistTemplateManagerElement = (
  <AppShell
    activeItem="siteAcquisition"
    title="Checklist templates"
    description="Author and import scenario-specific due diligence checklists."
  >
    <ChecklistTemplateManager />
  </AppShell>
)

const developerFeasibilityElement = (
  <AppShell
    activeItem="assetFeasibility"
    title="Feasibility workspace"
    description="Run feasibility checks, document pack generation, and advisory workflows."
  >
    <FeasibilityWizard withLayout={false} />
  </AppShell>
)

const financialControlElement = (
  <AppShell
    activeItem="financialControl"
    title="Financial control"
    description="Development economics and financing architecture."
  >
    <FinanceWorkspace />
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
    path: '/legacy/feasibility',
    element: developerFeasibilityElement,
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
      <RouterProvider router={router} />
    </TranslationProvider>
  </React.StrictMode>,
)
