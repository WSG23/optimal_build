import React from 'react'
import ReactDOM from 'react-dom/client'
import { createBrowserRouter, RouterProvider } from './router'
import HomeOverview from './App'
import { TranslationProvider } from './i18n'
import CadDetectionPage from './pages/CadDetectionPage'
import CadPipelinesPage from './pages/CadPipelinesPage'
import CadUploadPage from './pages/CadUploadPage'
import FeasibilityWizard from './modules/feasibility/FeasibilityWizard'
import './index.css'

const router = createBrowserRouter([
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
])

ReactDOM.createRoot(document.getElementById('root')!).render(
  <React.StrictMode>
    <TranslationProvider>
      <RouterProvider router={router} />
    </TranslationProvider>
  </React.StrictMode>,
)
