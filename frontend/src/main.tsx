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

const hash = window.location.hash
if (hash.startsWith('#/')) {
  const targetPath = hash.slice(1)
  window.history.replaceState(null, '', targetPath)
}

const router = createBrowserRouter([
  {
    path: '/home',
    element: <HomeOverview />,
  },
  {
    path: '/',
    element: <HomeOverview />,
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
    path: '/cad/pipelines',
    element: <CadPipelinesPage />,
  },
  {
    path: '/feasibility',
    element: <FeasibilityWizard />,
  },
  {
    path: '/finance',
    element: <FinanceWorkspace />,
  },
  {
    path: '/agents/site-capture',
    element: <AgentsGpsCapturePage />,
  },
  {
    path: '/agents/advisory',
    element: <AgentAdvisoryPage />,
  },
  {
    path: '/agents/integrations',
    element: <AgentIntegrationsPage />,
  },
  {
    path: '/agents/performance',
    element: <AgentPerformancePage />,
  },
  {
    path: '/visualizations/intelligence',
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
