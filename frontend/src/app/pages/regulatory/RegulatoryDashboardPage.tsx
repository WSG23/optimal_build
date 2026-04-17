import React, {
  Suspense,
  lazy,
  useState,
  useEffect,
  useCallback,
  useMemo,
  useRef,
} from 'react'
import { Box, Alert, Snackbar, Tab, Tabs, useTheme } from '@mui/material'
import AddIcon from '@mui/icons-material/Add'
import RefreshIcon from '@mui/icons-material/Refresh'
import TimelineIcon from '@mui/icons-material/Timeline'
import SubmissionIcon from '@mui/icons-material/Assignment'
import {
  regulatoryApi,
  AuthoritySubmission,
  ChangeOfUseApplication,
  HeritageSubmission,
  AssetType,
  type CorenetCapability,
} from '../../../api/regulatory'
import { QuickActionsSection } from './components/QuickActionsSection'
import { getTableSx } from '../../../utils/themeStyles'
import { useProjectScope } from '../../../contexts/useProjectScope'
import { Button } from '../../../components/canonical/Button'
import { EmptyState, SkeletonCard } from '../../../components/canonical'
import { useRouterController } from '../../../router'

const SubmissionWizard = lazy(async () => {
  const module = await import('./components/SubmissionWizard')
  return { default: module.SubmissionWizard }
})

const CompliancePathTimeline = lazy(async () => {
  const module = await import('./components/CompliancePathTimeline')
  return { default: module.CompliancePathTimeline }
})

const ChangeOfUseWizard = lazy(async () => {
  const module = await import('./components/ChangeOfUseWizard')
  return { default: module.ChangeOfUseWizard }
})

const HeritageSubmissionForm = lazy(async () => {
  const module = await import('./components/HeritageSubmissionForm')
  return { default: module.HeritageSubmissionForm }
})

const SubmissionsTabContent = lazy(async () => {
  const module = await import('./components/SubmissionsTabContent')
  return { default: module.SubmissionsTabContent }
})

const STORAGE_PREFIX = 'ob_regulatory'

const buildStorageKey = (projectId: string, suffix: string) =>
  `${STORAGE_PREFIX}:${projectId}:${suffix}`

const loadStoredList = <T,>(projectId: string, suffix: string): T[] => {
  if (typeof window === 'undefined' || !projectId) {
    return []
  }
  const raw = window.localStorage.getItem(buildStorageKey(projectId, suffix))
  if (!raw) {
    return []
  }
  try {
    const parsed = JSON.parse(raw) as T[]
    return Array.isArray(parsed) ? parsed : []
  } catch {
    return []
  }
}

const persistList = <T,>(projectId: string, suffix: string, items: T[]) => {
  if (typeof window === 'undefined' || !projectId) {
    return
  }
  window.localStorage.setItem(
    buildStorageKey(projectId, suffix),
    JSON.stringify(items),
  )
}

interface TabPanelProps {
  children?: React.ReactNode
  index: number
  value: number
}

function TabPanel({ children, value, index }: TabPanelProps) {
  return (
    <Box
      role="tabpanel"
      hidden={value !== index}
      id={`regulatory-tabpanel-${index}`}
      aria-labelledby={`regulatory-tab-${index}`}
      sx={{ pt: 'var(--ob-space-300)' }}
    >
      {value === index && children}
    </Box>
  )
}

function RegulatoryPanelFallback({ label }: { label: string }) {
  return (
    <Box
      className="ob-seamless-panel ob-seamless-panel--glass"
      sx={{
        p: 'var(--ob-space-150)',
        minHeight: 220,
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
      }}
    >
      <Alert severity="info" sx={{ mb: 0 }}>
        {label}
      </Alert>
    </Box>
  )
}

export const RegulatoryDashboardPage: React.FC = () => {
  const theme = useTheme()
  const isDarkMode = theme.palette.mode === 'dark'
  const { navigate } = useRouterController()
  const { currentProject, isProjectLoading, projectError, projectId } =
    useProjectScope()

  const [tabValue, setTabValue] = useState(0)
  const [submissions, setSubmissions] = useState<AuthoritySubmission[]>([])
  const [changeOfUseApps, setChangeOfUseApps] = useState<
    ChangeOfUseApplication[]
  >([])
  const [heritageSubmissions, setHeritageSubmissions] = useState<
    HeritageSubmission[]
  >([])
  const [loading, setLoading] = useState(false)
  const [refreshing, setRefreshing] = useState(false)
  const [wizardOpen, setWizardOpen] = useState(false)
  const [changeOfUseOpen, setChangeOfUseOpen] = useState(false)
  const [selectedChangeOfUse, setSelectedChangeOfUse] = useState<
    ChangeOfUseApplication | undefined
  >(undefined)
  const [heritageFormOpen, setHeritageFormOpen] = useState(false)
  const [selectedHeritageSubmission, setSelectedHeritageSubmission] = useState<
    HeritageSubmission | undefined
  >(undefined)
  const [error, setError] = useState<string | null>(null)
  const [successMessage, setSuccessMessage] = useState<string | null>(null)
  const [capability, setCapability] = useState<CorenetCapability | null>(null)
  const previousProjectId = useRef<string | null>(null)
  const fetchRequestId = useRef(0)
  const latestHeritageSubmission = useMemo(() => {
    if (heritageSubmissions.length === 0) {
      return null
    }
    return [...heritageSubmissions].sort((a, b) => {
      return new Date(b.created_at).getTime() - new Date(a.created_at).getTime()
    })[0]
  }, [heritageSubmissions])
  const preferredAssetType = useMemo<AssetType | undefined>(() => {
    if (heritageSubmissions.length > 0) {
      return 'heritage'
    }
    if (changeOfUseApps.length > 0) {
      const latest = changeOfUseApps[0]
      return (latest.proposed_use || latest.current_use) as AssetType
    }
    return undefined
  }, [changeOfUseApps, heritageSubmissions])

  const tableSx = getTableSx(isDarkMode)

  const fetchSubmissions = useCallback(
    async (isRefresh = false) => {
      if (!projectId) {
        return
      }
      const requestId = ++fetchRequestId.current
      if (isRefresh) setRefreshing(true)
      else setLoading(true)
      setError(null)

      const storedSubmissions = loadStoredList<AuthoritySubmission>(
        projectId,
        'submissions',
      )
      const storedChangeOfUse = loadStoredList<ChangeOfUseApplication>(
        projectId,
        'change-of-use',
      )
      const storedHeritage = loadStoredList<HeritageSubmission>(
        projectId,
        'heritage',
      )

      try {
        try {
          const capabilityData = await regulatoryApi.getCorenetCapability()
          if (requestId !== fetchRequestId.current) {
            return
          }
          setCapability(capabilityData)
        } catch (capabilityError) {
          console.warn(
            '[regulatory] failed to load CORENET capability',
            capabilityError,
          )
        }

        const data = await regulatoryApi.listSubmissions(projectId)
        if (requestId !== fetchRequestId.current) {
          return
        }
        setSubmissions(data)
        persistList(projectId, 'submissions', data)

        const couApps =
          await regulatoryApi.listChangeOfUseApplications(projectId)
        if (requestId !== fetchRequestId.current) {
          return
        }
        setChangeOfUseApps(couApps)
        persistList(projectId, 'change-of-use', couApps)

        const heritageData =
          await regulatoryApi.listHeritageSubmissions(projectId)
        if (requestId !== fetchRequestId.current) {
          return
        }
        setHeritageSubmissions(heritageData)
        persistList(projectId, 'heritage', heritageData)

        const pendingItems = data.filter((s) =>
          ['SUBMITTED', 'IN_REVIEW'].includes(s.status),
        )
        if (pendingItems.length > 0 && isRefresh) {
          for (const item of pendingItems) {
            await regulatoryApi.getSubmissionStatus(item.id)
          }
          const updatedData = await regulatoryApi.listSubmissions(projectId)
          if (requestId !== fetchRequestId.current) {
            return
          }
          setSubmissions(updatedData)
        }
      } catch (err) {
        if (requestId !== fetchRequestId.current) {
          return
        }
        console.error(err)
        setSubmissions(storedSubmissions)
        setChangeOfUseApps(storedChangeOfUse)
        setHeritageSubmissions(storedHeritage)
        if (
          storedSubmissions.length === 0 &&
          storedChangeOfUse.length === 0 &&
          storedHeritage.length === 0
        ) {
          setError('Failed to load submissions')
        }
      } finally {
        if (requestId === fetchRequestId.current) {
          if (isRefresh) setRefreshing(false)
          else setLoading(false)
        }
      }
    },
    [projectId],
  )

  useEffect(() => {
    fetchSubmissions()
  }, [fetchSubmissions])

  useEffect(() => {
    if (previousProjectId.current === projectId) {
      return
    }
    previousProjectId.current = projectId
    setSubmissions([])
    setChangeOfUseApps([])
    setHeritageSubmissions([])
    setSelectedChangeOfUse(undefined)
    setSelectedHeritageSubmission(undefined)
    setWizardOpen(false)
    setChangeOfUseOpen(false)
    setHeritageFormOpen(false)
    setError(null)
  }, [projectId])

  if (!projectId) {
    return (
      <Box sx={{ width: '100%' }}>
        {isProjectLoading ? (
          <SkeletonCard contentLines={3} />
        ) : (
          <EmptyState
            title="Select a project to manage regulatory submissions"
            description={
              projectError?.message ??
              'Submission tracking, compliance paths, and heritage workflows are tied to a project.'
            }
            actionLabel="Go to projects"
            onAction={() => navigate('/projects')}
            size="md"
            sx={{ alignItems: 'flex-start', textAlign: 'left' }}
          />
        )}
      </Box>
    )
  }

  const handleCreateSuccess = (newSubmission: AuthoritySubmission) => {
    setSubmissions((prev) => {
      const next = [
        newSubmission,
        ...prev.filter((s) => s.id !== newSubmission.id),
      ]
      persistList(projectId, 'submissions', next)
      return next
    })
    setWizardOpen(false)
    setSuccessMessage('Submission created successfully')
  }

  const handleHeritageSuccess = (submission: HeritageSubmission) => {
    setHeritageSubmissions((prev) => {
      const existingIndex = prev.findIndex((s) => s.id === submission.id)
      if (existingIndex >= 0) {
        const updated = [...prev]
        updated[existingIndex] = submission
        persistList(projectId, 'heritage', updated)
        setSuccessMessage('Heritage submission updated')
        return updated
      }
      const next = [submission, ...prev]
      persistList(projectId, 'heritage', next)
      setSuccessMessage('Heritage submission created')
      return next
    })
  }

  const openHeritageForm = (submission?: HeritageSubmission) => {
    setSelectedHeritageSubmission(submission)
    setHeritageFormOpen(true)
  }

  const openChangeOfUseForm = (application?: ChangeOfUseApplication) => {
    setSelectedChangeOfUse(application)
    setChangeOfUseOpen(true)
  }

  const closeHeritageForm = () => {
    setHeritageFormOpen(false)
    setSelectedHeritageSubmission(undefined)
  }

  const closeChangeOfUseForm = () => {
    setChangeOfUseOpen(false)
    setSelectedChangeOfUse(undefined)
  }

  const handleTabChange = (_: React.SyntheticEvent, newValue: number) => {
    setTabValue(newValue)
  }

  const handleRefreshSubmission = (id: string) => {
    regulatoryApi.getSubmissionStatus(id).then(() => fetchSubmissions(false))
  }

  const integrationState = capability?.integration_status.state ?? 'unavailable'
  const integrationModeLabel = capability?.live_submission_available
    ? 'Live submission'
    : capability?.package_status === 'submission_ready'
      ? 'Submission prep'
      : 'Unavailable'

  return (
    <Box sx={{ width: '100%' }}>
      {/* Page Header */}
      <Box
        component="header"
        sx={{
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'flex-start',
          flexWrap: 'wrap',
          gap: 'var(--ob-space-100)',
          mb: 'var(--ob-space-200)',
          animation:
            'ob-slide-down-fade var(--ob-motion-header-duration) var(--ob-motion-header-ease) both',
        }}
      >
        <Box>
          <Box
            component="h1"
            sx={{
              fontSize: 'var(--ob-font-size-2xl)',
              fontWeight: 700,
              lineHeight: 1.2,
              color: 'var(--ob-color-text-primary)',
              m: 0,
            }}
          >
            Regulatory Dashboard
          </Box>
          <Box
            component="p"
            sx={{
              fontSize: 'var(--ob-font-size-sm)',
              color: 'var(--ob-color-text-secondary)',
              m: 0,
              mt: 'var(--ob-space-025)',
            }}
          >
            Manage authority submissions and compliance tracking
          </Box>
          <Box
            component="span"
            sx={{
              fontSize: 'var(--ob-font-size-xs)',
              color: 'var(--ob-color-text-tertiary)',
              mt: 'var(--ob-space-050)',
              display: 'block',
            }}
          >
            Project: {currentProject?.name ?? projectId}
          </Box>
        </Box>
        <Box sx={{ display: 'flex', gap: 'var(--ob-space-100)' }}>
          <Button
            variant="secondary"
            size="sm"
            onClick={() => fetchSubmissions(true)}
            disabled={refreshing || loading}
          >
            <RefreshIcon sx={{ fontSize: '1rem', mr: 'var(--ob-space-050)' }} />
            {refreshing ? 'Updating...' : 'Check Status'}
          </Button>
          <Button
            variant="primary"
            size="sm"
            onClick={() => setWizardOpen(true)}
          >
            <AddIcon sx={{ fontSize: '1rem', mr: 'var(--ob-space-050)' }} />
            New Submission
          </Button>
        </Box>
      </Box>

      {error && (
        <Alert severity="error" sx={{ mb: 'var(--ob-space-200)' }}>
          {error}
        </Alert>
      )}

      {capability ? (
        <Alert
          severity={
            capability.live_submission_available
              ? 'success'
              : capability.integration_status.state === 'mock'
                ? 'warning'
                : 'info'
          }
          sx={{ mb: 'var(--ob-space-200)' }}
        >
          CORENET mode: <strong>{integrationModeLabel}</strong>
          {capability.delivery_blockers.length > 0
            ? ` \u2014 ${capability.delivery_blockers[0]}`
            : ''}
        </Alert>
      ) : null}

      {/* Quick Actions */}
      <QuickActionsSection
        latestHeritageSubmission={latestHeritageSubmission}
        onOpenChangeOfUse={() => openChangeOfUseForm()}
        onOpenHeritageForm={openHeritageForm}
        onNavigateToCompliance={() => setTabValue(1)}
      />

      {/* Tabs */}
      <Box sx={{ borderBottom: 1, borderColor: 'divider' }}>
        <Tabs value={tabValue} onChange={handleTabChange}>
          <Tab
            label="Submissions"
            icon={<SubmissionIcon />}
            iconPosition="start"
          />
          <Tab
            label="Compliance Path"
            icon={<TimelineIcon />}
            iconPosition="start"
          />
        </Tabs>
      </Box>

      {/* Tab 0: Submissions */}
      <TabPanel value={tabValue} index={0}>
        <Suspense
          fallback={
            <RegulatoryPanelFallback label="Loading submissions workspace..." />
          }
        >
          <SubmissionsTabContent
            submissions={submissions}
            changeOfUseApps={changeOfUseApps}
            heritageSubmissions={heritageSubmissions}
            loading={loading}
            integrationModeLabel={integrationModeLabel}
            integrationState={integrationState}
            tableSx={tableSx}
            onRefreshSubmission={handleRefreshSubmission}
            onOpenChangeOfUseForm={openChangeOfUseForm}
            onOpenHeritageForm={openHeritageForm}
          />
        </Suspense>
      </TabPanel>

      {/* Tab 1: Compliance Path */}
      <TabPanel value={tabValue} index={1}>
        <Suspense
          fallback={
            <RegulatoryPanelFallback label="Loading compliance path..." />
          }
        >
          <CompliancePathTimeline
            projectId={projectId}
            projectName={currentProject?.name}
            preferredAssetType={preferredAssetType}
          />
        </Suspense>
      </TabPanel>

      {/* Dialogs */}
      {wizardOpen ? (
        <Suspense fallback={null}>
          <SubmissionWizard
            open={wizardOpen}
            onClose={() => setWizardOpen(false)}
            projectId={projectId}
            onSuccess={handleCreateSuccess}
          />
        </Suspense>
      ) : null}

      {changeOfUseOpen ? (
        <Suspense fallback={null}>
          <ChangeOfUseWizard
            open={changeOfUseOpen}
            onClose={closeChangeOfUseForm}
            projectId={projectId}
            initialApplication={selectedChangeOfUse}
            onSuccess={(application) => {
              closeChangeOfUseForm()
              setChangeOfUseApps((prev) => {
                const existingIndex = prev.findIndex(
                  (s) => s.id === application.id,
                )
                if (existingIndex >= 0) {
                  const updated = [...prev]
                  updated[existingIndex] = application
                  persistList(projectId, 'change-of-use', updated)
                  setSuccessMessage('Change of use application updated')
                  return updated
                }
                const next = [application, ...prev]
                persistList(projectId, 'change-of-use', next)
                setSuccessMessage('Change of use application submitted')
                return next
              })
            }}
          />
        </Suspense>
      ) : null}

      {heritageFormOpen ? (
        <Suspense fallback={null}>
          <HeritageSubmissionForm
            open={heritageFormOpen}
            onClose={closeHeritageForm}
            projectId={projectId}
            existingSubmission={selectedHeritageSubmission}
            onSuccess={handleHeritageSuccess}
          />
        </Suspense>
      ) : null}

      <Snackbar
        open={Boolean(successMessage)}
        autoHideDuration={3000}
        onClose={() => setSuccessMessage(null)}
        message={successMessage}
        anchorOrigin={{ vertical: 'bottom', horizontal: 'center' }}
        ContentProps={{
          role: 'status',
          'aria-live': 'polite' as const,
          sx: {
            bgcolor: 'var(--ob-gold-bg)',
            color: 'var(--ob-gold-text)',
            border: '1px solid var(--ob-gold-400)',
            borderRadius: 'var(--ob-radius-sm)',
            fontWeight: 600,
          },
        }}
      />
    </Box>
  )
}
