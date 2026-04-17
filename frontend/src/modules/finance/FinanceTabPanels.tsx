import { Suspense, lazy, type ReactNode } from 'react'

import { Alert, Box, CircularProgress, Stack, Typography } from '@mui/material'
import Warning from '@mui/icons-material/Warning'

import { Button } from '../../components/canonical/Button'
import { Card } from '../../components/canonical/Card'
import { FinancePrivacyNotice } from './components/FinancePrivacyNotice'
import type {
  ConstructionLoanInput,
  FinanceAnalyticsMetadata,
  FinanceScenarioSummary,
  FinanceSensitivityOutcome,
  SensitivityBandInput,
} from '../../api/finance'
import type { SensitivitySummaryItem } from './components/sensitivitySummary'
import type { TranslationOptions } from '../../i18n/i18n'

type TranslateFn = (key: string, options?: TranslationOptions) => string

const FinanceAssetBreakdown = lazy(
  () => import('./components/FinanceAssetBreakdown'),
)
const FinanceCapitalStack = lazy(
  () => import('./components/FinanceCapitalStack'),
)
const FinanceDrawdownSchedule = lazy(
  () => import('./components/FinanceDrawdownSchedule'),
)
const FinanceLoanInterest = lazy(
  () => import('./components/FinanceLoanInterest'),
)
const FinanceSensitivityTable = lazy(
  () => import('./components/FinanceSensitivityTable'),
)
const FinanceScenarioCreator = lazy(() =>
  import('./components/FinanceScenarioCreator').then((module) => ({
    default: module.FinanceScenarioCreator,
  })),
)
const FinanceFacilityEditor = lazy(() =>
  import('./components/FinanceFacilityEditor').then((module) => ({
    default: module.FinanceFacilityEditor,
  })),
)
const FinanceJobTimeline = lazy(() =>
  import('./components/FinanceJobTimeline').then((module) => ({
    default: module.FinanceJobTimeline,
  })),
)
const FinanceAnalyticsPanel = lazy(() =>
  import('./components/FinanceAnalyticsPanel').then((module) => ({
    default: module.FinanceAnalyticsPanel,
  })),
)
const FinanceSensitivityControls = lazy(() =>
  import('./components/FinanceSensitivityControls').then((module) => ({
    default: module.FinanceSensitivityControls,
  })),
)
const FinanceSensitivitySummary = lazy(() =>
  import('./components/FinanceSensitivitySummary').then((module) => ({
    default: module.FinanceSensitivitySummary,
  })),
)

interface TimelineJob {
  scenarioId: number
  taskId: string | null
  status: string
  backend: string | null
  queuedAt: string | null
}

interface FinanceTabPanelsProps {
  activeTab: number
  setActiveTab: (tab: number) => void
  scenarios: FinanceScenarioSummary[]
  primaryScenario: FinanceScenarioSummary | null
  analyticsMetadata: FinanceAnalyticsMetadata | null
  showEmptyState: boolean
  effectiveProjectId: string
  projectDisplayName: string
  financeTemplateId: string | null
  capturePropertyId: string | null
  seeding: boolean
  savingLoan: boolean
  promotingScenarioId: number | null
  deletingScenarioId: number | null
  runningSensitivity: boolean
  sensitivityError: string | null
  pendingCount: number
  timelineJobs: TimelineJob[]
  parameters: string[]
  selectedParameters: string[]
  filteredSensitivity: FinanceSensitivityOutcome[]
  sensitivitySummaries: SensitivitySummaryItem[]
  t: TranslateFn
  addScenario: (summary: FinanceScenarioSummary) => void
  refresh: () => void
  setScenarioMessage: (msg: string | null) => void
  setScenarioError: (msg: string | null) => void
  handleSeedFromCapture: () => void
  handleImportWorkbookClick: () => void
  handleSaveLoan: (input: ConstructionLoanInput) => Promise<void>
  handleMarkPrimary: (scenarioId: number) => void
  handleRequestDeleteScenario: (
    scenarioId: number,
    scenarioName: string,
  ) => void
  handleRunSensitivity: (bands: SensitivityBandInput[]) => void
  handleSelectAll: () => void
  handleToggleParameter: (parameter: string) => void
  handleDownloadCsv: () => void
  handleDownloadJson: () => void
}

export function FinanceTabPanels({
  activeTab,
  setActiveTab,
  scenarios,
  primaryScenario,
  analyticsMetadata,
  showEmptyState,
  effectiveProjectId,
  projectDisplayName,
  financeTemplateId,
  capturePropertyId,
  seeding,
  savingLoan,
  promotingScenarioId,
  deletingScenarioId,
  runningSensitivity,
  sensitivityError,
  pendingCount,
  timelineJobs,
  parameters,
  selectedParameters,
  filteredSensitivity,
  sensitivitySummaries,
  t,
  addScenario,
  refresh,
  setScenarioMessage,
  setScenarioError,
  handleSeedFromCapture,
  handleImportWorkbookClick,
  handleSaveLoan,
  handleMarkPrimary,
  handleRequestDeleteScenario,
  handleRunSensitivity,
  handleSelectAll,
  handleToggleParameter,
  handleDownloadCsv,
  handleDownloadJson,
}: FinanceTabPanelsProps) {
  const panelFallback: ReactNode = (
    <Card
      variant="default"
      sx={{
        p: 'var(--ob-space-200)',
        display: 'flex',
        justifyContent: 'center',
      }}
    >
      <CircularProgress />
    </Card>
  )

  const renderEmptyPanel = (title: string) => (
    <Card variant="default" sx={{ p: 'var(--ob-space-300)' }}>
      <Stack spacing={1} alignItems="flex-start">
        <Typography variant="h6">{title}</Typography>
        <Typography variant="body2" color="text.secondary">
          Create or import a finance scenario to populate this view.
        </Typography>
        <Button variant="secondary" size="sm" onClick={() => setActiveTab(0)}>
          Go to scenario builder
        </Button>
      </Stack>
    </Card>
  )

  return (
    <>
      {/* Tab Panels - Depth 1 (Glass Cards with ob-card-module) */}
      <div role="tabpanel" hidden={activeTab !== 0}>
        {activeTab === 0 && (
          <Stack spacing="var(--ob-space-200)">
            <Box className="ob-card-module">
              <Suspense fallback={panelFallback}>
                <FinanceScenarioCreator
                  projectId={effectiveProjectId}
                  projectName={projectDisplayName}
                  initialTemplateId={financeTemplateId}
                  onCreated={(summary) => {
                    setScenarioMessage(
                      t('finance.scenarioCreator.success', {
                        name: summary.scenarioName,
                      }),
                    )
                    setScenarioError(null)
                    addScenario(summary)
                  }}
                  onError={(message) => {
                    setScenarioError(message)
                    setScenarioMessage(null)
                  }}
                  onRefresh={() => {
                    refresh()
                  }}
                />
              </Suspense>
            </Box>

            {primaryScenario?.isPrivate ? (
              <FinancePrivacyNotice projectName={projectDisplayName} />
            ) : null}

            {showEmptyState && (
              <Card
                variant="default"
                sx={{
                  p: 'var(--ob-space-300)',
                  textAlign: 'center',
                }}
              >
                <Stack spacing={2} alignItems="center">
                  <Typography variant="h5">Start a finance model</Typography>
                  <Typography variant="body2" color="text.secondary">
                    Enter assumptions in the scenario builder above or seed a
                    starting point from your capture.
                  </Typography>
                  <Stack
                    direction={{ xs: 'column', sm: 'row' }}
                    spacing={1}
                    justifyContent="center"
                    alignItems="center"
                  >
                    {capturePropertyId && (
                      <Button
                        variant="primary"
                        size="sm"
                        onClick={handleSeedFromCapture}
                        disabled={seeding}
                      >
                        {seeding ? 'Seeding...' : 'Seed from Capture'}
                      </Button>
                    )}
                    <Button
                      variant="secondary"
                      size="sm"
                      onClick={() => setActiveTab(0)}
                    >
                      Build from assumptions
                    </Button>
                    <Button
                      variant="ghost"
                      size="sm"
                      onClick={handleImportWorkbookClick}
                    >
                      Import from workbook
                    </Button>
                  </Stack>
                </Stack>
              </Card>
            )}

            {primaryScenario?.scenarioId === 0 && (
              <Alert
                severity="warning"
                icon={<Warning />}
                sx={{ mb: 'var(--ob-space-050)' }}
              >
                <strong>{t('finance.warnings.offlineMode')}</strong>
                <Typography variant="body2">
                  {t('finance.warnings.offlineModeDetail') ||
                    'You are viewing offline demonstration data. Changes cannot be saved correctly until the backend service is available.'}
                </Typography>
              </Alert>
            )}

            {scenarios.length > 0 && (
              <Box className="ob-card-module">
                <Suspense fallback={panelFallback}>
                  <FinanceCapitalStack
                    scenarios={scenarios}
                    onMarkPrimary={handleMarkPrimary}
                    updatingScenarioId={promotingScenarioId}
                    onRequestDelete={handleRequestDeleteScenario}
                    deletingScenarioId={deletingScenarioId}
                  />
                </Suspense>
              </Box>
            )}
          </Stack>
        )}
      </div>

      <div role="tabpanel" hidden={activeTab !== 1}>
        {activeTab === 1 &&
          (showEmptyState ? (
            renderEmptyPanel('Drawdown schedule')
          ) : (
            <Box className="ob-card-module">
              <Suspense fallback={panelFallback}>
                <FinanceDrawdownSchedule scenarios={scenarios} />
              </Suspense>
            </Box>
          ))}
      </div>
      <div role="tabpanel" hidden={activeTab !== 2}>
        {activeTab === 2 &&
          (showEmptyState
            ? renderEmptyPanel('Asset breakdown')
            : primaryScenario && (
                <Box className="ob-card-module">
                  <Suspense fallback={panelFallback}>
                    <FinanceAssetBreakdown
                      summary={primaryScenario.assetMixSummary ?? null}
                      breakdowns={primaryScenario.assetBreakdowns ?? []}
                    />
                  </Suspense>
                </Box>
              ))}
      </div>
      <div role="tabpanel" hidden={activeTab !== 3}>
        {activeTab === 3 &&
          (showEmptyState ? (
            renderEmptyPanel('Facility editor')
          ) : (
            <Box className="ob-card-module">
              <Suspense fallback={panelFallback}>
                <FinanceFacilityEditor
                  scenario={primaryScenario ?? null}
                  onSave={handleSaveLoan}
                  saving={savingLoan}
                />
              </Suspense>
            </Box>
          ))}
      </div>
      <div role="tabpanel" hidden={activeTab !== 4}>
        {activeTab === 4 &&
          (showEmptyState ? (
            renderEmptyPanel('Job timeline')
          ) : (
            <Box className="ob-card-module">
              <Suspense fallback={panelFallback}>
                <FinanceJobTimeline
                  jobs={timelineJobs}
                  pendingCount={pendingCount}
                />
              </Suspense>
            </Box>
          ))}
      </div>
      <div role="tabpanel" hidden={activeTab !== 5}>
        {activeTab === 5 &&
          (showEmptyState ? (
            renderEmptyPanel('Loan interest')
          ) : (
            <Box className="ob-card-module">
              <Suspense fallback={panelFallback}>
                <FinanceLoanInterest
                  schedule={primaryScenario?.constructionLoanInterest ?? null}
                />
              </Suspense>
            </Box>
          ))}
      </div>
      <div role="tabpanel" hidden={activeTab !== 6}>
        {activeTab === 6 &&
          (showEmptyState
            ? renderEmptyPanel('Analytics')
            : analyticsMetadata && (
                <Stack spacing="var(--ob-space-200)">
                  <Box className="ob-card-module">
                    <Suspense fallback={panelFallback}>
                      <FinanceAnalyticsPanel
                        analytics={analyticsMetadata}
                        currency={primaryScenario?.currency ?? 'SGD'}
                      />
                    </Suspense>
                  </Box>
                  {primaryScenario && (
                    <Box className="ob-card-module">
                      <FinanceSensitivityControls
                        scenario={primaryScenario}
                        pendingJobs={pendingCount}
                        disabled={runningSensitivity}
                        error={sensitivityError}
                        onRun={handleRunSensitivity}
                      />
                    </Box>
                  )}
                </Stack>
              ))}
      </div>
      <div role="tabpanel" hidden={activeTab !== 7}>
        {activeTab === 7 &&
          (showEmptyState ? (
            renderEmptyPanel('Sensitivity analysis')
          ) : (
            <Stack spacing="var(--ob-space-200)">
              <Box className="ob-card-module">
                <Suspense fallback={panelFallback}>
                  <FinanceSensitivitySummary
                    summaries={sensitivitySummaries}
                    currency={primaryScenario?.currency ?? 'SGD'}
                  />
                </Suspense>
              </Box>
              {primaryScenario && (
                <Box className="ob-card-module">
                  <FinanceSensitivityControls
                    scenario={primaryScenario}
                    pendingJobs={pendingCount}
                    disabled={runningSensitivity}
                    error={sensitivityError}
                    onRun={handleRunSensitivity}
                  />
                </Box>
              )}
              <Box className="ob-card-module">
                <FinanceSensitivityTable
                  outcomes={filteredSensitivity}
                  currency={primaryScenario?.currency ?? 'SGD'}
                  parameters={parameters}
                  selectedParameters={selectedParameters}
                  onSelectAll={handleSelectAll}
                  onToggleParameter={handleToggleParameter}
                  onDownloadCsv={handleDownloadCsv}
                  onDownloadJson={handleDownloadJson}
                />
              </Box>
            </Stack>
          ))}
      </div>
    </>
  )
}
