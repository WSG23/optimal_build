import { Alert, Box, Stack, Typography } from '@mui/material'

import { Button } from '../../components/canonical/Button'
import { Card } from '../../components/canonical/Card'
import type { FinanceAuditEvidence } from '../../api/finance'

interface FinanceAuditCardProps {
  effectiveProjectId: string
  auditEvidence: FinanceAuditEvidence | null
  auditEvidenceError: string | null
  navigate: (path: string) => void
}

export function FinanceAuditCard({
  effectiveProjectId,
  auditEvidence,
  auditEvidenceError,
  navigate,
}: FinanceAuditCardProps) {
  const latestFinanceAuditEvent = auditEvidence?.financeEvents.at(-1) ?? null
  const latestWorkbookImport = auditEvidence?.imports.at(-1) ?? null
  const latestSubmissionEvent = auditEvidence?.submissionEvents.at(-1) ?? null

  return (
    <Card
      variant="default"
      sx={{
        mb: 'var(--ob-space-150)',
        p: 'var(--ob-space-200)',
      }}
    >
      <Stack spacing={1.25}>
        <Box>
          <Typography variant="h6">Audit evidence snapshot</Typography>
          <Typography variant="body2" color="text.secondary">
            Evidence chain health for finance modeling, workbook imports, and
            regulatory submission prep.
          </Typography>
        </Box>
        {auditEvidenceError ? (
          <Alert severity="warning">{auditEvidenceError}</Alert>
        ) : auditEvidence ? (
          <>
            <Stack
              direction={{ xs: 'column', md: 'row' }}
              spacing={1}
              useFlexGap
              flexWrap="wrap"
            >
              <Box
                sx={{
                  px: 1.25,
                  py: 0.75,
                  borderRadius: 2,
                  bgcolor: auditEvidence.valid
                    ? 'rgba(15,118,110,0.10)'
                    : 'rgba(185,28,28,0.10)',
                  color: auditEvidence.valid
                    ? 'var(--ob-success-700)'
                    : 'var(--ob-error-700)',
                  fontSize: '0.8rem',
                  fontWeight: 700,
                }}
              >
                {auditEvidence.valid ? 'Chain valid' : 'Chain needs review'}
              </Box>
              <Typography variant="body2" color="text.secondary">
                {auditEvidence.chain.signedEntries}/
                {auditEvidence.chain.entryCount} signed entries
              </Typography>
              {auditEvidence.recipients.length > 0 ? (
                <Typography variant="body2" color="text.secondary">
                  Recipients: {auditEvidence.recipients.join(', ')}
                </Typography>
              ) : null}
            </Stack>
            <Stack spacing={0.75}>
              {latestFinanceAuditEvent ? (
                <Typography variant="body2" color="text.secondary">
                  Latest finance scenario:{' '}
                  {latestFinanceAuditEvent.scenarioName ?? 'Scenario'} via{' '}
                  <strong>{latestFinanceAuditEvent.origin ?? 'manual'}</strong>
                  {latestFinanceAuditEvent.recordedAt
                    ? ` on ${new Date(latestFinanceAuditEvent.recordedAt).toLocaleString()}`
                    : ''}
                </Typography>
              ) : null}
              {latestWorkbookImport ? (
                <Typography variant="body2" color="text.secondary">
                  Latest workbook import:{' '}
                  {latestWorkbookImport.scenarioName ?? 'Workbook scenario'}
                  {latestWorkbookImport.workbookFormat
                    ? ` (${latestWorkbookImport.workbookFormat})`
                    : ''}
                </Typography>
              ) : null}
              {latestSubmissionEvent ? (
                <Typography variant="body2" color="text.secondary">
                  Latest submission event:{' '}
                  {latestSubmissionEvent.agencyName ??
                    latestSubmissionEvent.agency ??
                    'Agency'}{' '}
                  {latestSubmissionEvent.submissionMode
                    ? `• ${latestSubmissionEvent.submissionMode.replace('_', ' ')}`
                    : ''}
                  {latestSubmissionEvent.packageStatus
                    ? ` • ${latestSubmissionEvent.packageStatus}`
                    : ''}
                </Typography>
              ) : null}
            </Stack>
            <Box>
              <Button
                variant="secondary"
                size="sm"
                onClick={() =>
                  navigate(`/projects/${effectiveProjectId}/evidence`)
                }
              >
                Open evidence pack
              </Button>
            </Box>
          </>
        ) : (
          <Typography variant="body2" color="text.secondary">
            No audit evidence recorded for this project yet.
          </Typography>
        )}
      </Stack>
    </Card>
  )
}
