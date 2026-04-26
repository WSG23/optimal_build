import React from 'react'
import ReactDOM from 'react-dom/client'
import { createBrowserRouter, RouterProvider } from './router'
import { HomeOverview } from './App'
import { TranslationProvider } from './i18n'
import { DeveloperProvider } from './contexts/DeveloperContext'
import { ProjectProvider } from './contexts/ProjectContext'
import { AppThemeProvider } from './theme/ThemeProvider'
import '@ob/tokens.css'
import './styles/index.css'
import './styles/premium-effects.css'
import { AppShell } from './app/layout/AppShell'
import { BaseLayout } from './app/layout/BaseLayout'
import { NotFoundPage } from './app/pages/NotFoundPage'
import { RouteProgress } from './components/layout/RouteProgress'
import {
  AGENT_CAPTURE_ROUTE_PATHS,
  DEVELOPER_CAPTURE_ROUTE_PATHS,
  PROJECT_CAPTURE_ROUTE_PATH,
} from './app/pages/capture/routeAliases'

const hash = window.location.hash
if (hash.startsWith('#/')) {
  const targetPath = hash.slice(1)
  window.history.replaceState(null, '', targetPath)
}

function suspense(element: React.ReactNode) {
  return <React.Suspense fallback={<RouteProgress />}>{element}</React.Suspense>
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
const DueDiligencePage = React.lazy(async () => {
  const module = await import('./app/pages/due-diligence/DueDiligencePage')
  return { default: module.DueDiligencePage }
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
const ProjectListPage = React.lazy(async () => {
  const module = await import('./app/pages/projects/ProjectListPage')
  return { default: module.ProjectListPage }
})
const ProjectHubPage = React.lazy(async () => {
  const module = await import('./app/pages/projects/ProjectHubPage')
  return { default: module.ProjectHubPage }
})
const DeveloperControlPanel = React.lazy(async () => {
  const module = await import('./app/pages/developer/DeveloperControlPanel')
  return { default: module.DeveloperControlPanel }
})
const DealCalculatorPage = React.lazy(async () => {
  const module = await import('./app/pages/deal-calculator/DealCalculatorPage')
  return { default: module.DealCalculatorPage }
})
const EvidencePage = React.lazy(async () => {
  const module = await import('./app/pages/evidence/EvidencePage')
  return { default: module.EvidencePage }
})
const WhyNotExcelPage = React.lazy(async () => {
  const module = await import('./app/pages/why-not-excel/WhyNotExcelPage')
  return { default: module.WhyNotExcelPage }
})

const businessPerformanceElement = (
  <AppShell activeItem="performance" hideSidebar hideHeader workspace="agent">
    {suspense(<BusinessPerformancePage />)}
  </AppShell>
)

const agentDashboardElement = (
  <AppShell
    activeItem="performance"
    title="Agent Workspace"
    description="Pipeline performance, capture, marketing, and advisory workflows."
    workspace="agent"
  >
    {suspense(<BusinessPerformancePage />)}
  </AppShell>
)

// Unified capture page - same feature surface, workspace-specific shell wrappers
const agentCaptureElement = (
  <AppShell activeItem="gpsCapture" hideSidebar hideHeader workspace="agent">
    {suspense(<UnifiedCapturePage />)}
  </AppShell>
)

const developerCaptureElement = (
  <AppShell
    activeItem="siteAcquisition"
    hideSidebar
    hideHeader
    workspace="developer"
  >
    {suspense(<UnifiedCapturePage />)}
  </AppShell>
)

const marketingElement = (
  <AppShell
    activeItem="marketing"
    title="Marketing packs"
    description="Generate, track, and share professional marketing packs for developers and investors."
    hideSidebar
    workspace="agent"
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
    workspace="agent"
  >
    {suspense(<AdvisoryPage />)}
  </AppShell>
)

const integrationsElement = (
  <AppShell
    activeItem="integrations"
    title="Data partnerships"
    description="Truthful partner status for Singapore portals, market data, and CRM workflows."
    hideSidebar
    workspace="agent"
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
    workspace="developer"
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
    workspace="developer"
  >
    {suspense(<ChecklistTemplateManager />)}
  </AppShell>
)

const dueDiligenceElement = (
  <AppShell
    activeItem="dueDiligence"
    title="Property due diligence"
    description="Review condition assessments, inspection history, checklist progress, and scenario overrides."
    hideSidebar
    workspace="developer"
  >
    {suspense(<DueDiligencePage />)}
  </AppShell>
)

const developerFeasibilityElement = (
  <AppShell
    activeItem="assetFeasibility"
    title="Feasibility"
    description="Run feasibility checks, document pack generation, and advisory workflows."
    hideSidebar
    workspace="developer"
  >
    {suspense(<FeasibilityWizard withLayout={false} />)}
  </AppShell>
)

const financialControlElement = suspense(
  <FinanceWorkspace workspace="developer" />,
)

const phaseManagementElement = (
  <AppShell
    activeItem="phaseManagement"
    hideSidebar
    hideHeader
    workspace="developer"
  >
    {suspense(<PhaseManagementPage />)}
  </AppShell>
)

const teamCoordinationElement = (
  <AppShell
    activeItem="teamCoordination"
    hideSidebar
    hideHeader
    workspace="developer"
  >
    {suspense(<TeamManagementPage />)}
  </AppShell>
)

const regulatoryNavigationElement = (
  <AppShell
    activeItem="regulatoryNavigation"
    hideSidebar
    hideHeader
    workspace="developer"
  >
    {suspense(<RegulatoryDashboardPage />)}
  </AppShell>
)

const developerControlPanelElement = (
  <AppShell
    activeItem="performance"
    title="Developer Console"
    description="Internal tools and configuration."
    workspace="developer"
  >
    {suspense(<DeveloperControlPanel />)}
  </AppShell>
)

const dealCalculatorElement = (
  <AppShell
    activeItem="dealCalculator"
    title="Deal Calculator"
    description="Standalone Singapore deal screen for feasibility, finance, and trust-signaled underwriting."
    hideSidebar
    workspace="developer"
  >
    {suspense(<DealCalculatorPage />)}
  </AppShell>
)

const evidenceElement = (
  <AppShell
    activeItem="evidence"
    title="Evidence Packs"
    description="Exportable audit packs for finance lineage, workbook imports, recipients, and submissions."
    hideSidebar
    workspace="developer"
  >
    {suspense(<EvidencePage />)}
  </AppShell>
)

const whyNotExcelElement = (
  <AppShell
    title="Why Not Excel?"
    description="Why Singapore developers move from spreadsheet-only underwriting into a shared evidence workflow."
    hideSidebar
    workspace="developer"
  >
    {suspense(<WhyNotExcelPage />)}
  </AppShell>
)

const projectListElement = (
  <AppShell
    title="Projects"
    description="Singapore-first onboarding for deal modeling, workbook intake, and project execution."
    workspace="developer"
  >
    {suspense(<ProjectListPage />)}
  </AppShell>
)

const developerDashboardElement = (
  <AppShell
    activeItem="projects"
    title="Developer Workspace"
    description="Singapore developer workflow for deal screening, finance, consultant coordination, and regulatory prep."
    workspace="developer"
  >
    {suspense(<ProjectListPage />)}
  </AppShell>
)

const projectHubElement = (
  <AppShell
    title="Project Overview"
    description="Project hub and navigation."
    workspace="developer"
  >
    {suspense(<ProjectHubPage />)}
  </AppShell>
)

const notFoundElement = (
  <AppShell title="Not found" hideSidebar workspace="developer">
    <NotFoundPage />
  </AppShell>
)

const router = createBrowserRouter(
  [
    {
      path: '/',
      element: developerDashboardElement,
    },
    {
      path: '/agents',
      element: agentDashboardElement,
    },
    {
      path: '/developers',
      element: developerDashboardElement,
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
    ...DEVELOPER_CAPTURE_ROUTE_PATHS.map((path) => ({
      path,
      element: developerCaptureElement,
    })),
    ...AGENT_CAPTURE_ROUTE_PATHS.map((path) => ({
      path,
      element: agentCaptureElement,
    })),
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
      path: '/app/deal-calculator',
      element: dealCalculatorElement,
    },
    {
      path: '/developers/deal-calculator',
      element: dealCalculatorElement,
    },
    {
      path: '/app/evidence',
      element: evidenceElement,
    },
    {
      path: '/developers/evidence',
      element: evidenceElement,
    },
    {
      path: '/why-not-excel',
      element: whyNotExcelElement,
    },
    {
      path: '/developers/why-not-excel',
      element: whyNotExcelElement,
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
      path: '/app/due-diligence',
      element: dueDiligenceElement,
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
      path: '/projects',
      element: projectListElement,
    },
    {
      path: '/projects/:projectId',
      element: projectHubElement,
    },
    {
      path: PROJECT_CAPTURE_ROUTE_PATH,
      element: developerCaptureElement,
    },
    {
      path: '/projects/:projectId/due-diligence',
      element: dueDiligenceElement,
    },
    {
      path: '/projects/:projectId/feasibility',
      element: developerFeasibilityElement,
    },
    {
      path: '/projects/:projectId/finance',
      element: financialControlElement,
    },
    {
      path: '/projects/:projectId/phases',
      element: phaseManagementElement,
    },
    {
      path: '/projects/:projectId/team',
      element: teamCoordinationElement,
    },
    {
      path: '/projects/:projectId/evidence',
      element: evidenceElement,
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
  ],
  { notFoundElement },
)

const container = document.getElementById('root')

if (!container) {
  throw new Error('Root element with id "root" not found')
}

ReactDOM.createRoot(container).render(
  <React.StrictMode>
    <TranslationProvider>
      <AppThemeProvider>
        <DeveloperProvider>
          <ProjectProvider>
            <RouterProvider router={router} layout={BaseLayout} />
          </ProjectProvider>
        </DeveloperProvider>
      </AppThemeProvider>
    </TranslationProvider>
  </React.StrictMode>,
)
