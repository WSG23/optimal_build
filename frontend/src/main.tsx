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
    path: '/app/gps-capture',
    element: gpsCaptureElement,
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
    element: <FeasibilityWizard />,
  },
  {
    path: '/legacy/finance',
    element: <FinanceWorkspace />,
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
