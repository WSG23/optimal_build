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

  const overlayCodes = useMemo(
    () => overlaySuggestions.map((item) => item.code),
    [overlaySuggestions],
  )

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
            p: 2,
            mb: 4,
            backgroundColor: 'rgba(30, 30, 30, 0.6)',
            backdropFilter: 'blur(10px)',
            border: '1px solid rgba(255,255,255,0.05)',
            borderRadius: '4px',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'space-between',
            flexWrap: 'wrap',
            gap: 2,
          }}
        >
          <Box sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
            <TextField
              label={t('pipelines.projectLabel')}
              type="number"
              variant="outlined"
              size="small"
              value={projectId}
              onChange={(e) => {
                setProjectId(Number(e.target.value) || DEFAULT_PROJECT_ID)
              }}
              InputProps={{
                startAdornment: (
                  <InputAdornment position="start">
                    <SearchIcon sx={{ color: 'text.secondary' }} />
                  </InputAdornment>
                ),
                sx: {
                  color: 'white',
                  backgroundColor: 'rgba(255,255,255,0.05)',
                  '& .MuiOutlinedInput-notchedOutline': {
                    borderColor: 'rgba(255,255,255,0.1)',
                  },
                  '&:hover .MuiOutlinedInput-notchedOutline': {
                    borderColor: 'rgba(255,255,255,0.3)',
                  },
                },
              }}
              InputLabelProps={{ sx: { color: 'text.secondary' } }}
            />
            <IconButton
              onClick={handleRetry}
              disabled={loading}
              color="primary"
              sx={{ border: '1px solid rgba(255,255,255,0.1)' }}
            >
              {loading ? (
                <CircularProgress size={24} color="inherit" />
              ) : (
                <RefreshIcon />
              )}
            </IconButton>
          </Box>

          {overlayCodes.length > 0 && (
            <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
              <Typography
                variant="caption"
                sx={{
                  color: 'text.secondary',
                  textTransform: 'uppercase',
                  letterSpacing: '0.05em',
                }}
              >
                {t('detection.overlays')}:
              </Typography>
              {overlayCodes.slice(0, 3).map((code) => (
                <Box
                  key={code}
                  sx={{
                    px: 1,
                    py: 0.5,
                    backgroundColor: 'rgba(6, 182, 212, 0.1)',
                    border: '1px solid rgba(6, 182, 212, 0.3)',
                    borderRadius: '4px',
                    color: '#06b6d4',
                    fontSize: '0.75rem',
                  }}
                >
                  {code}
                </Box>
              ))}
              {overlayCodes.length > 3 && (
                <Typography variant="caption" sx={{ color: 'text.secondary' }}>
                  +{overlayCodes.length - 3}
                </Typography>
              )}
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
              backgroundColor: 'rgba(211, 47, 47, 0.05)',
              color: '#ef5350',
              border: '1px solid rgba(239, 83, 80, 0.3)',
              alignItems: 'center',
              '& .MuiAlert-icon': { color: '#ef5350' },
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
        <RoiSummary
          metrics={roiMetrics}
          loading={loading}
          isLive={!loading && !error}
        />

        {/* Pipeline Suggestions - Visualization for Empty State */}
        <Box sx={{ mb: 6 }}>
          <Typography
            variant="h5"
            sx={{ fontWeight: 700, color: 'white', mb: 2 }}
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
                borderRadius: '4px',
                backgroundColor: 'rgba(30, 30, 30, 0.3)',
                border: '1px dashed rgba(255,255,255,0.1)',
                display: 'flex',
                flexDirection: 'column',
                alignItems: 'center',
                backgroundImage:
                  'radial-gradient(circle at center, rgba(6, 182, 212, 0.05) 0%, transparent 70%)',
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
                  stroke: 'white',
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
                  color: '#06b6d4',
                  borderColor: 'rgba(6, 182, 212, 0.5)',
                  zIndex: 1,
                  '&:hover': {
                    borderColor: '#06b6d4',
                    backgroundColor: 'rgba(6,182,212,0.05)',
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
                    borderRadius: '4px',
                    backgroundColor: '#1E1E1E',
                    border: '1px solid rgba(255,255,255,0.08)',
                    transition: 'all 0.2s',
                    '&:hover': {
                      borderColor: '#06b6d4',
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
                        color: 'white',
                        fontSize: '1.1rem',
                        fontWeight: 600,
                      }}
                    >
                      {suggestion.title}
                    </Typography>
                    <Box
                      sx={{
                        px: 1,
                        py: 0.5,
                        borderRadius: '4px',
                        backgroundColor: `rgba(${suggestion.automationScore > 0.8 ? '16, 185, 129' : '245, 158, 11'}, 0.1)`,
                        color:
                          suggestion.automationScore > 0.8
                            ? '#34D399'
                            : '#FBBF24',
                        fontWeight: 'bold',
                        fontSize: '0.75rem',
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
                      borderTop: '1px solid rgba(255,255,255,0.05)',
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
                      <Typography variant="subtitle2" sx={{ color: '#06b6d4' }}>
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
