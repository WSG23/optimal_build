import { useEffect, useMemo, useState } from 'react'
import {
  Alert,
  Box,
  Chip,
  CircularProgress,
  Grid,
  Stack,
  Typography,
} from '@mui/material'

import { Button } from '../../../components/canonical/Button'
import { Card } from '../../../components/canonical/Card'
import {
  fetchFinanceAuditEvidence,
  type FinanceAuditEvidence,
} from '../../../api/finance'
import { useProject } from '../../../contexts/useProject'
import { useRouterController, useRouterParams } from '../../../router'

function downloadJson(content: unknown, filename: string): void {
  if (typeof window === 'undefined') {
    return
  }
  const blob = new Blob([JSON.stringify(content, null, 2)], {
    type: 'application/json;charset=utf-8',
  })
  const url = URL.createObjectURL(blob)
  const anchor = document.createElement('a')
  anchor.href = url
  anchor.download = filename
  document.body.appendChild(anchor)
  anchor.click()
  document.body.removeChild(anchor)
  URL.revokeObjectURL(url)
}

export function EvidencePage() {
  const { currentProject } = useProject()
  const { projectId: routeProjectId } = useRouterParams()
  const { navigate } = useRouterController()
  const projectRef = routeProjectId ?? currentProject?.id ?? ''
  const projectName = currentProject?.name ?? projectRef
  const [evidence, setEvidence] = useState<FinanceAuditEvidence | null>(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    if (!projectRef) {
      setEvidence(null)
      return
    }
    const controller = new AbortController()
    setLoading(true)
    setError(null)
    fetchFinanceAuditEvidence(projectRef, { signal: controller.signal })
      .then((payload) => {
        setEvidence(payload)
      })
      .catch((err) => {
        if (controller.signal.aborted) {
          return
        }
        setError(
          err instanceof Error ? err.message : 'Unable to load evidence pack.',
        )
      })
      .finally(() => {
        if (!controller.signal.aborted) {
          setLoading(false)
        }
      })
    return () => controller.abort()
  }, [projectRef])

  const latestFinanceEvent = useMemo(
    () => evidence?.financeEvents.at(-1) ?? null,
    [evidence],
  )
  const latestImport = useMemo(
    () => evidence?.imports.at(-1) ?? null,
    [evidence],
  )
  const latestSubmission = useMemo(
    () => evidence?.submissionEvents.at(-1) ?? null,
    [evidence],
  )

  if (!projectRef) {
    return (
      <Card variant="default" sx={{ p: 'var(--ob-space-200)' }}>
        <Stack spacing={1.5}>
          <Typography variant="h6">
            Select a project to review evidence
          </Typography>
          <Typography variant="body2" color="text.secondary">
            Evidence packs are tied to a project audit chain.
          </Typography>
          <Box>
            <Button
              variant="primary"
              size="sm"
              onClick={() => navigate('/projects')}
            >
              Go to projects
            </Button>
          </Box>
        </Stack>
      </Card>
    )
  }

  return (
    <Stack spacing={2.5}>
      <Card variant="default" sx={{ p: 'var(--ob-space-200)' }}>
        <Stack spacing={1.5}>
          <Stack
            direction={{ xs: 'column', md: 'row' }}
            spacing={1.5}
            justifyContent="space-between"
            alignItems={{ xs: 'flex-start', md: 'center' }}
          >
            <Box>
              <Typography variant="h5">Evidence pack</Typography>
              <Typography variant="body2" color="text.secondary">
                Liability-ready package for finance origin, workbook lineage,
                recipients, and regulatory submission history.
              </Typography>
              <Typography
                variant="body2"
                color="text.secondary"
                sx={{ mt: 0.5 }}
              >
                Project: {projectName}
              </Typography>
            </Box>
            <Stack direction="row" spacing={1}>
              <Button
                variant="secondary"
                size="sm"
                disabled={!evidence}
                onClick={() =>
                  evidence
                    ? downloadJson(
                        evidence,
                        `evidence-pack-${String(projectName).replace(/\s+/g, '-').toLowerCase()}.json`,
                      )
                    : undefined
                }
              >
                Export evidence pack
              </Button>
              <Button
                variant="ghost"
                size="sm"
                onClick={() => navigate(`/projects/${projectRef}/finance`)}
              >
                Back to finance
              </Button>
            </Stack>
          </Stack>
        </Stack>
      </Card>

      {loading ? (
        <Card
          variant="default"
          sx={{ p: 'var(--ob-space-200)', textAlign: 'center' }}
        >
          <CircularProgress />
        </Card>
      ) : null}

      {error ? <Alert severity="error">{error}</Alert> : null}

      {evidence ? (
        <>
          <Grid container spacing={2}>
            <Grid item xs={12} md={4}>
              <Card
                variant="default"
                sx={{ p: 'var(--ob-space-200)', height: '100%' }}
              >
                <Stack spacing={1}>
                  <Typography variant="h6">Chain health</Typography>
                  <Chip
                    size="small"
                    color={evidence.valid ? 'success' : 'warning'}
                    label={evidence.valid ? 'Chain valid' : 'Needs review'}
                    sx={{ width: 'fit-content' }}
                  />
                  <Typography variant="body2" color="text.secondary">
                    {evidence.chain.signedEntries}/{evidence.chain.entryCount}{' '}
                    signed entries
                  </Typography>
                  <Typography variant="body2" color="text.secondary">
                    Latest hash: {evidence.chain.latestHash ?? 'Not available'}
                  </Typography>
                </Stack>
              </Card>
            </Grid>
            <Grid item xs={12} md={4}>
              <Card
                variant="default"
                sx={{ p: 'var(--ob-space-200)', height: '100%' }}
              >
                <Stack spacing={1}>
                  <Typography variant="h6">Finance origin</Typography>
                  <Typography variant="body2" color="text.secondary">
                    {latestFinanceEvent
                      ? `${latestFinanceEvent.scenarioName ?? 'Scenario'} via ${latestFinanceEvent.origin ?? 'manual'}`
                      : 'No finance scenario recorded yet.'}
                  </Typography>
                  <Typography variant="body2" color="text.secondary">
                    {latestFinanceEvent?.recordedAt
                      ? `Recorded ${new Date(latestFinanceEvent.recordedAt).toLocaleString()}`
                      : 'Scenario lineage appears once a finance run or import is recorded.'}
                  </Typography>
                </Stack>
              </Card>
            </Grid>
            <Grid item xs={12} md={4}>
              <Card
                variant="default"
                sx={{ p: 'var(--ob-space-200)', height: '100%' }}
              >
                <Stack spacing={1}>
                  <Typography variant="h6">Recipients</Typography>
                  {evidence.recipients.length > 0 ? (
                    <Typography variant="body2" color="text.secondary">
                      {evidence.recipients.join(', ')}
                    </Typography>
                  ) : (
                    <Typography variant="body2" color="text.secondary">
                      No recipient trail recorded yet.
                    </Typography>
                  )}
                </Stack>
              </Card>
            </Grid>
          </Grid>

          <Grid container spacing={2}>
            <Grid item xs={12} md={6}>
              <Card
                variant="default"
                sx={{ p: 'var(--ob-space-200)', height: '100%' }}
              >
                <Stack spacing={1}>
                  <Typography variant="h6">Workbook lineage</Typography>
                  {latestImport ? (
                    <>
                      <Typography variant="body2" color="text.secondary">
                        Latest import:{' '}
                        {latestImport.scenarioName ?? 'Workbook scenario'}
                      </Typography>
                      <Typography variant="body2" color="text.secondary">
                        Format:{' '}
                        {latestImport.workbookFormat ??
                          latestImport.format ??
                          'unknown'}
                      </Typography>
                      <Typography variant="body2" color="text.secondary">
                        Assets mapped: {latestImport.assetCount ?? 0}
                      </Typography>
                    </>
                  ) : (
                    <Typography variant="body2" color="text.secondary">
                      No workbook import events recorded yet.
                    </Typography>
                  )}
                </Stack>
              </Card>
            </Grid>
            <Grid item xs={12} md={6}>
              <Card
                variant="default"
                sx={{ p: 'var(--ob-space-200)', height: '100%' }}
              >
                <Stack spacing={1}>
                  <Typography variant="h6">Submission history</Typography>
                  {latestSubmission ? (
                    <>
                      <Typography variant="body2" color="text.secondary">
                        {latestSubmission.agencyName ??
                          latestSubmission.agency ??
                          'Agency'}
                      </Typography>
                      <Typography variant="body2" color="text.secondary">
                        Mode: {latestSubmission.submissionMode ?? 'n/a'}
                      </Typography>
                      <Typography variant="body2" color="text.secondary">
                        Package:{' '}
                        {latestSubmission.packageStatus ??
                          latestSubmission.status ??
                          'n/a'}
                      </Typography>
                    </>
                  ) : (
                    <Typography variant="body2" color="text.secondary">
                      No regulatory package events recorded yet.
                    </Typography>
                  )}
                </Stack>
              </Card>
            </Grid>
          </Grid>
        </>
      ) : null}
    </Stack>
  )
}
