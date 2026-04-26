import { useState } from 'react'

import {
  Alert,
  Box,
  Collapse,
  IconButton,
  Stack,
  Typography,
} from '@mui/material'
import ExpandMoreIcon from '@mui/icons-material/ExpandMore'
import ExpandLessIcon from '@mui/icons-material/ExpandLess'

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
  const [expanded, setExpanded] = useState(false)
  const latestFinanceAuditEvent = auditEvidence?.financeEvents.at(-1) ?? null
  const latestWorkbookImport = auditEvidence?.imports.at(-1) ?? null
  const latestSubmissionEvent = auditEvidence?.submissionEvents.at(-1) ?? null

  return (
    <Card
      variant="default"
      sx={{
        mb: 'var(--ob-space-150)',
        p: 'var(--ob-space-150)',
      }}
    >
      <Stack spacing="var(--ob-space-075)">
        {/* Collapsed header — always visible */}
        <Stack
          direction="row"
          justifyContent="space-between"
          alignItems="center"
          sx={{ cursor: 'pointer' }}
          onClick={() => setExpanded((prev) => !prev)}
          role="button"
          tabIndex={0}
          aria-expanded={expanded}
          onKeyDown={(e) => {
            if (e.key === 'Enter' || e.key === ' ') {
              e.preventDefault()
              setExpanded((prev) => !prev)
            }
          }}
        >
          <Stack
            direction="row"
            spacing="var(--ob-space-100)"
            alignItems="center"
          >
            <Typography
              variant="body2"
              sx={{
                fontWeight: 'var(--ob-font-weight-bold)',
                fontSize: 'var(--ob-font-size-sm)',
              }}
            >
              Audit evidence
            </Typography>
            {auditEvidence && (
              <Box
                sx={{
                  px: 'var(--ob-space-075)',
                  py: 'var(--ob-space-025)',
                  borderRadius: 'var(--ob-radius-xs)',
                  bgcolor: auditEvidence.valid
                    ? 'var(--ob-color-success-soft)'
                    : 'var(--ob-color-error-soft)',
                  color: auditEvidence.valid
                    ? 'var(--ob-success-700)'
                    : 'var(--ob-error-700)',
                  fontSize: 'var(--ob-font-size-xs)',
                  fontWeight: 'var(--ob-font-weight-bold)',
                }}
              >
                {auditEvidence.valid ? 'Valid' : 'Needs review'}
              </Box>
            )}
            {auditEvidence && (
              <Typography variant="caption" color="text.secondary">
                {auditEvidence.chain.signedEntries}/
                {auditEvidence.chain.entryCount} signed
              </Typography>
            )}
          </Stack>
          <IconButton
            size="small"
            aria-label={expanded ? 'Collapse' : 'Expand'}
          >
            {expanded ? (
              <ExpandLessIcon fontSize="small" />
            ) : (
              <ExpandMoreIcon fontSize="small" />
            )}
          </IconButton>
        </Stack>

        {/* Expanded detail */}
        <Collapse in={expanded}>
          <Stack
            spacing="var(--ob-space-075)"
            sx={{ pt: 'var(--ob-space-075)' }}
          >
            {auditEvidenceError ? (
              <Alert severity="warning">{auditEvidenceError}</Alert>
            ) : auditEvidence ? (
              <>
                {auditEvidence.recipients.length > 0 && (
                  <Typography variant="body2" color="text.secondary">
                    Recipients: {auditEvidence.recipients.join(', ')}
                  </Typography>
                )}
                {latestFinanceAuditEvent && (
                  <Typography variant="body2" color="text.secondary">
                    Latest finance scenario:{' '}
                    {latestFinanceAuditEvent.scenarioName ?? 'Scenario'} via{' '}
                    <strong>
                      {latestFinanceAuditEvent.origin ?? 'manual'}
                    </strong>
                    {latestFinanceAuditEvent.recordedAt
                      ? ` on ${new Date(latestFinanceAuditEvent.recordedAt).toLocaleString()}`
                      : ''}
                  </Typography>
                )}
                {latestWorkbookImport && (
                  <Typography variant="body2" color="text.secondary">
                    Latest workbook import:{' '}
                    {latestWorkbookImport.scenarioName ?? 'Workbook scenario'}
                    {latestWorkbookImport.workbookFormat
                      ? ` (${latestWorkbookImport.workbookFormat})`
                      : ''}
                  </Typography>
                )}
                {latestSubmissionEvent && (
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
                )}
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
        </Collapse>
      </Stack>
    </Card>
  )
}
