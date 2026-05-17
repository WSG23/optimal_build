import {
  Box,
  Chip,
  CircularProgress,
  Stack,
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableRow,
  Typography,
} from '@mui/material'
import type { SxProps, Theme } from '@mui/material/styles'

import type {
  AuthoritySubmission,
  ChangeOfUseApplication,
  HeritageSubmission,
} from '../../../../api/regulatory'
import { Button } from '../../../../components/canonical/Button'
import { Card } from '../../../../components/canonical/Card'
import { EmptyState } from '../../../../components/canonical/EmptyState'

interface SubmissionsTabContentProps {
  submissions: AuthoritySubmission[]
  changeOfUseApps: ChangeOfUseApplication[]
  heritageSubmissions: HeritageSubmission[]
  loading: boolean
  integrationModeLabel: string
  integrationState: string
  tableSx?: SxProps<Theme>
  onRefreshSubmission: (id: string) => void
  onOpenChangeOfUseForm: (application?: ChangeOfUseApplication) => void
  onOpenHeritageForm: (submission?: HeritageSubmission) => void
}

function formatDate(value?: string | null): string {
  if (!value) {
    return 'Not submitted'
  }
  const parsed = new Date(value)
  return Number.isNaN(parsed.getTime()) ? value : parsed.toLocaleDateString()
}

export function SubmissionsTabContent({
  submissions,
  changeOfUseApps,
  heritageSubmissions,
  loading,
  integrationModeLabel,
  integrationState,
  tableSx,
  onRefreshSubmission,
  onOpenChangeOfUseForm,
  onOpenHeritageForm,
}: SubmissionsTabContentProps) {
  if (loading) {
    return (
      <Box
        sx={{
          py: 'var(--ob-space-300)',
          display: 'flex',
          justifyContent: 'center',
        }}
      >
        <CircularProgress size={24} />
      </Box>
    )
  }

  const hasAnySubmission =
    submissions.length > 0 ||
    changeOfUseApps.length > 0 ||
    heritageSubmissions.length > 0

  if (!hasAnySubmission) {
    return (
      <EmptyState
        title="No submissions yet"
        description={`Regulatory tracking is ready in ${integrationModeLabel.toLowerCase()} mode. Start with a change-of-use or heritage workflow.`}
        actionLabel="Start change of use"
        onAction={() => onOpenChangeOfUseForm()}
        secondaryActionLabel="New heritage submission"
        onSecondaryAction={() => onOpenHeritageForm()}
        size="md"
        sx={{ alignItems: 'flex-start', textAlign: 'left' }}
      />
    )
  }

  return (
    <Stack spacing="var(--ob-space-200)">
      <Card variant="default" sx={{ p: 'var(--ob-space-200)' }}>
        <Stack
          direction={{ xs: 'column', md: 'row' }}
          justifyContent="space-between"
          spacing="var(--ob-space-100)"
        >
          <Box>
            <Typography variant="h6" component="h2">
              Authority submissions
            </Typography>
            <Typography variant="body2" color="text.secondary">
              Integration state: {integrationState} • Mode:{' '}
              {integrationModeLabel}
            </Typography>
          </Box>
        </Stack>
        <Box sx={tableSx}>
          <Table sx={{ mt: 'var(--ob-space-150)' }}>
            <TableHead>
              <TableRow>
                <TableCell>Title</TableCell>
                <TableCell>Status</TableCell>
                <TableCell>Agency</TableCell>
                <TableCell>Submitted</TableCell>
                <TableCell align="right">Action</TableCell>
              </TableRow>
            </TableHead>
            <TableBody>
              {submissions.map((submission) => (
                <TableRow key={submission.id}>
                  <TableCell>{submission.title}</TableCell>
                  <TableCell>
                    <Chip size="small" label={submission.status} />
                  </TableCell>
                  <TableCell>
                    {submission.agency_name ??
                      submission.agency_code ??
                      'Agency'}
                  </TableCell>
                  <TableCell>{formatDate(submission.submitted_at)}</TableCell>
                  <TableCell align="right">
                    <Button
                      variant="ghost"
                      size="sm"
                      onClick={() => onRefreshSubmission(submission.id)}
                    >
                      Refresh
                    </Button>
                  </TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </Box>
      </Card>

      <Card variant="default" sx={{ p: 'var(--ob-space-200)' }}>
        <Stack spacing="var(--ob-space-100)">
          <Typography variant="h6" component="h3">
            Change of use
          </Typography>
          {changeOfUseApps.length === 0 ? (
            <Typography variant="body2" color="text.secondary">
              No change-of-use applications yet.
            </Typography>
          ) : (
            changeOfUseApps.map((application) => (
              <Stack
                key={application.id}
                direction={{ xs: 'column', md: 'row' }}
                justifyContent="space-between"
                spacing="var(--ob-space-100)"
              >
                <Typography variant="body2" color="text.secondary">
                  {application.current_use} to {application.proposed_use} •{' '}
                  {application.status}
                </Typography>
                <Button
                  variant="ghost"
                  size="sm"
                  onClick={() => onOpenChangeOfUseForm(application)}
                >
                  Edit
                </Button>
              </Stack>
            ))
          )}
        </Stack>
      </Card>

      <Card variant="default" sx={{ p: 'var(--ob-space-200)' }}>
        <Stack spacing="var(--ob-space-100)">
          <Typography variant="h6" component="h3">
            Heritage submissions
          </Typography>
          {heritageSubmissions.length === 0 ? (
            <Typography variant="body2" color="text.secondary">
              No heritage submissions yet.
            </Typography>
          ) : (
            heritageSubmissions.map((submission) => (
              <Stack
                key={submission.id}
                direction={{ xs: 'column', md: 'row' }}
                justifyContent="space-between"
                spacing="var(--ob-space-100)"
              >
                <Typography variant="body2" color="text.secondary">
                  {submission.conservation_status} • {submission.status}
                </Typography>
                <Button
                  variant="ghost"
                  size="sm"
                  onClick={() => onOpenHeritageForm(submission)}
                >
                  Edit
                </Button>
              </Stack>
            ))
          )}
        </Stack>
      </Card>
    </Stack>
  )
}
