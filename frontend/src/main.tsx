import React from 'react'
import ReactDOM from 'react-dom/client'
import { createBrowserRouter, RouterProvider } from './router'
import { HomeOverview } from './App'
import { TranslationProvider } from './i18n'
import { CadDetectionPage } from './pages/CadDetectionPage'
import { CadPipelinesPage } from './pages/CadPipelinesPage'
import { CadUploadPage } from './pages/CadUploadPage'
import { FeasibilityWizard } from './modules/feasibility/FeasibilityWizard'
import { FinanceWorkspace } from './modules/finance'
import '@ob/tokens.css'
import './index.css'

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
