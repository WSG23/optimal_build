import { useCallback, useEffect, useMemo, useRef, useState } from 'react'

import type {
  OverlaySuggestion,
  PipelineSuggestion,
  ProjectRoiMetrics,
} from '../api/client'
import { AppLayout } from '../App'
import { useApiClient } from '../api/client'
import { useTranslation } from '../i18n'
import useRules from '../hooks/useRules'
import RulePackExplanationPanel from '../modules/cad/RulePackExplanationPanel'
import RoiSummary from '../modules/cad/RoiSummary'
import type { RoiMetrics } from '../modules/cad/types'
import {
  Box,
  Button,
  TextField,
  Typography,
  CircularProgress,
  Alert,
  Paper,
  InputAdornment,
  IconButton,
} from '@mui/material'
import RefreshIcon from '@mui/icons-material/Refresh'
import SearchIcon from '@mui/icons-material/Search'
// Use MUI icons or fallbacks
import AutoFixHighIcon from '@mui/icons-material/AutoFixHigh'
import CloudOffIcon from '@mui/icons-material/CloudOff'

const DEFAULT_PROJECT_ID = 1
const OVERLAY_RUN_POLL_INTERVAL_MS = 2500
const OVERLAY_RUN_POLL_TIMEOUT_MS = 60000

export function CadPipelinesPage() {
  const apiClient = useApiClient()
  const { t } = useTranslation()
  const [projectId, setProjectId] = useState<number>(DEFAULT_PROJECT_ID)
  const [overlaySuggestions, setOverlaySuggestions] = useState<
    OverlaySuggestion[]
  >([])
  const [suggestions, setSuggestions] = useState<PipelineSuggestion[]>([])
  const [roi, setRoi] = useState<ProjectRoiMetrics | null>(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const { rules, loading: rulesLoading } = useRules(apiClient)
  const processedProjectRef = useRef<{ id: number | null; processed: boolean }>(
    { id: null, processed: false },
  )

  // Fetch logic is largely the same, but we will wrap it to handle re-tries nicely
  const fetchData = useCallback(async () => {
    // Logic copied from original 'load' function
    setLoading(true)
    setError(null)
    try {
      const eventsBeforeRun = await apiClient.listAuditTrail(projectId, {
        eventType: 'overlay_run',
      })
      const lastEventIdBeforeRun = eventsBeforeRun.reduce<number>(
        (max, event) => {
          return event.id > max ? event.id : max
        },
        0,
      )
      const runRequestedAt = Date.now()
      const runResult = await apiClient.runOverlay(projectId)

      // Polling logic
      const checkStatus = async () => {
        const deadline = runRequestedAt + OVERLAY_RUN_POLL_TIMEOUT_MS
        while (Date.now() < deadline) {
          const events = await apiClient.listAuditTrail(projectId, {
            eventType: 'overlay_run',
          })
          if (events.some((e) => e.id > lastEventIdBeforeRun)) return
          await new Promise((r) => setTimeout(r, OVERLAY_RUN_POLL_INTERVAL_MS))
        }
        throw new Error(t('common.errors.pipelineLoad'))
      }

      if (runResult.status.toLowerCase() !== 'completed') {
        await checkStatus()
      }

      const overlays = await apiClient.listOverlaySuggestions(projectId)
      const pipeline = await apiClient.getDefaultPipelineSuggestions({
        overlays: overlays.map((item) => item.code),
        hints: overlays
          .map((item) => item.rationale)
          .filter((value): value is string => Boolean(value)),
      })
      const roiMetrics = await apiClient.getProjectRoi(projectId)

      setOverlaySuggestions(overlays)
      setSuggestions(pipeline)
      setRoi(roiMetrics)
    } catch (err) {
      setError(
        err instanceof Error ? err.message : t('common.errors.pipelineLoad'),
      )
      setSuggestions([])
    } finally {
      setLoading(false)
    }
  }, [apiClient, projectId, t])

  useEffect(() => {
    if (processedProjectRef.current.id !== projectId) {
      processedProjectRef.current = { id: projectId, processed: false }
    }
    if (processedProjectRef.current.processed) return

    processedProjectRef.current.processed = true
    fetchData()
  }, [projectId, fetchData])

  const overlayCodes = useMemo(() => {
    const normalized = overlaySuggestions
      .map((item) => item.code.trim().toUpperCase())
      .filter(Boolean)
    return Array.from(new Set(normalized))
  }, [overlaySuggestions])

  const roiMetrics = useMemo<RoiMetrics>(() => {
    if (!roi) {
      return {
        automationScore: 0,
        savingsPercent: 0,
        reviewHoursSaved: 0,
        paybackWeeks: 0,
      }
    }
    return {
      automationScore: roi.automationScore,
      savingsPercent: roi.savingsPercent,
      reviewHoursSaved: Number(roi.reviewHoursSaved.toFixed(1)),
      paybackWeeks: roi.paybackWeeks,
    }
  }, [roi])

  const handleRetry = () => {
    processedProjectRef.current.processed = false // Force re-run
    // re-trigger effect by a slight update or just call fetchData direct?
    // Since effect guards on processed, we just reset processed and let effect run if id changed,
    // or if id is same, we need to manually call fetchData.
    fetchData()
  }

  return (
    <AppLayout title={t('pipelines.title')} subtitle={t('pipelines.subtitle')}>
      <Box
        className="cad-pipelines-page"
        sx={{ maxWidth: '1200px', margin: '0 auto', p: 2 }}
      >
        {/* Header Toolbar */}
        <Paper
          elevation={0}
          sx={{
            p: 'var(--ob-space-150)',
            mb: 4,
            background: 'var(--ob-color-surface-toolbar)',
            border: '1px solid rgba(255,255,255,0.10)',
            borderRadius: 'calc(var(--ob-radius-lg) + var(--ob-space-050))', // ~12px
            boxShadow: 'var(--ob-shadow-xl)',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'space-between',
            flexWrap: { xs: 'wrap', md: 'nowrap' },
            gap: 'var(--ob-space-150)',
          }}
        >
          <Box
            sx={{
              display: 'flex',
              alignItems: 'center',
              gap: 'var(--ob-space-150)',
              minWidth: 0,
            }}
          >
            <TextField
              hiddenLabel
              type="number"
              variant="outlined"
              size="small"
              value={projectId}
              onChange={(e) => {
                setProjectId(Number(e.target.value) || DEFAULT_PROJECT_ID)
              }}
              placeholder={t('pipelines.projectLabel')}
              InputProps={{
                startAdornment: (
                  <InputAdornment position="start">
                    <SearchIcon sx={{ color: 'var(--ob-neutral-500)' }} />
                  </InputAdornment>
                ),
                sx: {
                  color: 'var(--ob-neutral-100)',
                  backgroundColor: 'rgba(51, 65, 85, 0.5)', // slate-700/50
                  borderRadius: 'var(--ob-radius-md)',
                  width: '12rem', // matches Gemini (w-48)
                  '& .MuiOutlinedInput-notchedOutline': {
                    borderColor: 'rgba(71, 85, 105, 1)', // slate-600
                  },
                  '&:hover .MuiOutlinedInput-notchedOutline': {
                    borderColor: 'rgba(148, 163, 184, 0.5)',
                  },
                },
              }}
            />
            <IconButton
              onClick={handleRetry}
              disabled={loading}
              sx={{
                borderRadius: 'var(--ob-radius-pill)',
                width: 'var(--ob-size-icon-md)',
                height: 'var(--ob-size-icon-md)',
                color: 'var(--ob-neutral-500)',
                '&:hover': {
                  color: 'var(--ob-neutral-100)',
                  backgroundColor: 'rgba(255,255,255,0.05)',
                },
              }}
            >
              {loading ? (
                <CircularProgress size={18} color="inherit" />
              ) : (
                <RefreshIcon />
              )}
            </IconButton>
          </Box>

          {overlayCodes.length > 0 && (
            <Box
              sx={{
                display: 'flex',
                alignItems: 'center',
                gap: 'var(--ob-space-100)',
                minWidth: 0,
                flex: '1 1 auto',
                justifyContent: { xs: 'flex-start', md: 'flex-end' },
                flexWrap: 'nowrap',
              }}
            >
              <Typography
                variant="caption"
                sx={{
                  color: 'var(--ob-neutral-500)',
                  textTransform: 'uppercase',
                  letterSpacing: '0.16em',
                  fontWeight: 900,
                  fontSize: 'var(--ob-font-size-2xs)',
                  whiteSpace: 'nowrap',
                }}
              >
                {t('detection.overlays')}:
              </Typography>
              <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                {overlayCodes.slice(0, 3).map((code) => (
                  <Box
                    key={code}
                    sx={{
                      px: 'var(--ob-space-125)',
                      py: 'var(--ob-space-050)',
                      backgroundColor: 'rgba(51, 65, 85, 0.8)', // slate-700/80
                      border: '1px solid rgba(71, 85, 105, 1)', // slate-600
                      borderRadius: 'var(--ob-radius-md)',
                      color: 'var(--ob-brand-200)',
                      fontSize: 'var(--ob-font-size-2xs)',
                      fontWeight: 900,
                      letterSpacing: '0.08em',
                      textTransform: 'uppercase',
                      whiteSpace: 'nowrap',
                    }}
                  >
                    {code}
                  </Box>
                ))}
                {overlayCodes.length > 3 && (
                  <Typography
                    variant="caption"
                    sx={{
                      color: 'var(--ob-brand-300)',
                      fontWeight: 900,
                      fontSize: 'var(--ob-font-size-2xs)',
                      letterSpacing: '0.08em',
                      ml: 1,
                    }}
                  >
                    +{overlayCodes.length - 3}
                  </Typography>
                )}
              </Box>
            </Box>
          )}
        </Paper>

        {/* Error Handling - Status Indicator */}
        {error && (
          <Alert
            severity="error"
            variant="outlined"
            sx={{
              mb: 4,
              backgroundColor: 'rgba(var(--ob-color-error-muted-rgb) / 0.06)',
              color: 'var(--ob-color-error-muted)',
              border: '1px solid rgba(var(--ob-color-error-muted-rgb) / 0.3)',
              alignItems: 'center',
              '& .MuiAlert-icon': { color: 'var(--ob-color-error-muted)' },
            }}
            action={
              <Button color="inherit" size="small" onClick={handleRetry}>
                RETRY
              </Button>
            }
            icon={<CloudOffIcon />}
          >
            {error}
          </Alert>
        )}

        {/* ROI Snapshot - The "Wow" Deck */}
        <RoiSummary metrics={roiMetrics} loading={loading} isLive={false} />

        {/* Pipeline Suggestions - Visualization for Empty State */}
        <Box sx={{ mb: 6 }}>
          <Typography
            variant="h5"
            sx={{ fontWeight: 700, color: 'text.primary', mb: 2 }}
          >
            {t('pipelines.suggestionHeading')}
          </Typography>

          {/* Loading State just handled by loading overlay or specific skeleons, done inside RoiSummary for that part.
               For suggestions list, we can show a special loader or the empty state.
            */}

          {!loading && suggestions.length === 0 && !error && (
            <Paper
              elevation={0}
              sx={{
                p: 6,
                borderRadius: 'var(--ob-radius-sm)',
                backgroundColor: 'var(--ob-surface-glass-1)',
                border: '1px dashed var(--ob-color-border-faint)',
                display: 'flex',
                flexDirection: 'column',
                alignItems: 'center',
                backgroundImage:
                  'radial-gradient(circle at center, rgba(var(--ob-color-brand-primary-emphasis-rgb) / 0.08) 0%, transparent 70%)',
                position: 'relative',
                overflow: 'hidden',
              }}
            >
              {/* Background Watermark */}
              <Box
                component="svg"
                viewBox="0 0 200 200"
                sx={{
                  position: 'absolute',
                  width: '400px',
                  height: '400px',
                  opacity: 0.03,
                  fill: 'none',
                  stroke: 'var(--ob-color-text-primary)',
                  strokeWidth: 1,
                  top: '50%',
                  left: '50%',
                  transform: 'translate(-50%, -50%)',
                }}
              >
                <path d="M20,100 L180,100 M100,20 L100,180 M50,50 L150,150 M150,50 L50,150" />
                <circle cx="100" cy="100" r="80" />
                <rect x="40" y="40" width="120" height="120" />
              </Box>

              <AutoFixHighIcon
                sx={{
                  fontSize: 60,
                  color: 'text.secondary',
                  mb: 2,
                  opacity: 0.5,
                }}
              />

              <Typography
                variant="h6"
                sx={{
                  color: 'text.primary',
                  fontWeight: 600,
                  mb: 1,
                  zIndex: 1,
                }}
              >
                Waiting for overlays...
              </Typography>
              <Typography
                variant="body2"
                sx={{
                  color: 'text.secondary',
                  maxWidth: '400px',
                  textAlign: 'center',
                  mb: 3,
                  zIndex: 1,
                }}
              >
                Once the parsing pipeline completes, your custom automation
                rules and savings estimates will appear here.
              </Typography>

              <Button
                variant="outlined"
                onClick={handleRetry}
                disabled={loading}
                startIcon={<RefreshIcon />}
                sx={{
                  color: 'var(--ob-color-brand-primary-emphasis)',
                  borderColor:
                    'rgba(var(--ob-color-brand-primary-emphasis-rgb) / 0.5)',
                  zIndex: 1,
                  '&:hover': {
                    borderColor: 'var(--ob-color-border-brand)',
                    backgroundColor:
                      'rgba(var(--ob-color-brand-primary-emphasis-rgb) / 0.05)',
                  },
                }}
              >
                Check for Updates
              </Button>
            </Paper>
          )}

          {!loading && suggestions.length > 0 && (
            <Box
              sx={{
                display: 'grid',
                gridTemplateColumns: 'repeat(auto-fill, minmax(300px, 1fr))',
                gap: 3,
              }}
            >
              {suggestions.map((suggestion) => (
                <Paper
                  key={suggestion.id}
                  sx={{
                    p: 3,
                    borderRadius: 'var(--ob-radius-sm)',
                    backgroundColor: 'background.paper',
                    border: '1px solid var(--ob-color-border-faint)',
                    transition: 'all 0.2s',
                    '&:hover': {
                      borderColor: 'var(--ob-color-border-brand)',
                      transform: 'translateY(-2px)',
                    },
                  }}
                >
                  <Box
                    sx={{
                      display: 'flex',
                      alignItems: 'flex-start',
                      justifyContent: 'space-between',
                      mb: 2,
                    }}
                  >
                    <Typography
                      variant="h6"
                      sx={{
                        color: 'text.primary',
                        fontSize: 'var(--ob-font-size-lg)',
                        fontWeight: 'var(--ob-font-weight-semibold)',
                      }}
                    >
                      {suggestion.title}
                    </Typography>
                    <Box
                      sx={{
                        px: 1,
                        py: 0.5,
                        borderRadius: 'var(--ob-radius-sm)',
                        backgroundColor:
                          suggestion.automationScore > 0.8
                            ? 'rgba(var(--ob-color-success-strong-rgb) / 0.12)'
                            : 'rgba(var(--ob-color-warning-strong-rgb) / 0.12)',
                        color:
                          suggestion.automationScore > 0.8
                            ? 'var(--ob-color-status-success-text)'
                            : 'var(--ob-color-status-warning-text)',
                        fontWeight: 'var(--ob-font-weight-bold)',
                        fontSize: 'var(--ob-font-size-xs)',
                      }}
                    >
                      {Math.round(suggestion.automationScore * 100)}% AUTO
                    </Box>
                  </Box>

                  <Typography
                    variant="body2"
                    sx={{
                      color: 'text.secondary',
                      mb: 3,
                      height: '40px',
                      overflow: 'hidden',
                      textOverflow: 'ellipsis',
                    }}
                  >
                    {suggestion.description}
                  </Typography>

                  <Box
                    sx={{
                      borderTop: '1px solid var(--ob-color-border-faint)',
                      pt: 2,
                      display: 'flex',
                      justifyContent: 'space-between',
                    }}
                  >
                    <Box>
                      <Typography
                        variant="caption"
                        sx={{ color: 'text.secondary', display: 'block' }}
                      >
                        {t('pipelines.savings')}
                      </Typography>
                      <Typography
                        variant="subtitle2"
                        sx={{ color: 'var(--ob-color-brand-primary-emphasis)' }}
                      >
                        {suggestion.estimatedSavingsPercent}%
                      </Typography>
                    </Box>
                    <Box sx={{ textAlign: 'right' }}>
                      <Typography
                        variant="caption"
                        sx={{ color: 'text.secondary', display: 'block' }}
                      >
                        {t('pipelines.reviewHours')}
                      </Typography>
                      <Typography variant="subtitle2" sx={{ color: 'white' }}>
                        {suggestion.reviewHoursSaved}h
                      </Typography>
                    </Box>
                  </Box>
                </Paper>
              ))}
            </Box>
          )}
        </Box>

        <RulePackExplanationPanel rules={rules} loading={rulesLoading} />
      </Box>
    </AppLayout>
  )
}

export default CadPipelinesPage
