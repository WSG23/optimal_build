import AutoFixHigh from '@mui/icons-material/AutoFixHigh'
import HistoryEdu from '@mui/icons-material/HistoryEdu'
import Timeline from '@mui/icons-material/Timeline'
import { Stack, Typography } from '@mui/material'

import type { HeritageSubmission } from '../../../../api/regulatory'
import { Button } from '../../../../components/canonical/Button'
import { Card } from '../../../../components/canonical/Card'

interface QuickActionsSectionProps {
  latestHeritageSubmission: HeritageSubmission | null
  onOpenChangeOfUse: () => void
  onOpenHeritageForm: (submission?: HeritageSubmission) => void
  onNavigateToCompliance: () => void
}

export function QuickActionsSection({
  latestHeritageSubmission,
  onOpenChangeOfUse,
  onOpenHeritageForm,
  onNavigateToCompliance,
}: QuickActionsSectionProps) {
  return (
    <Card
      variant="default"
      sx={{ mb: 'var(--ob-space-200)', p: 'var(--ob-space-200)' }}
    >
      <Stack spacing="var(--ob-space-150)">
        <Typography variant="h6">Quick actions</Typography>
        <Stack
          direction={{ xs: 'column', md: 'row' }}
          spacing="var(--ob-space-100)"
        >
          <Button variant="secondary" size="sm" onClick={onOpenChangeOfUse}>
            <AutoFixHigh sx={{ fontSize: 16, mr: 'var(--ob-space-050)' }} />
            Start change of use
          </Button>
          <Button
            variant="secondary"
            size="sm"
            onClick={() =>
              onOpenHeritageForm(latestHeritageSubmission ?? undefined)
            }
          >
            <HistoryEdu sx={{ fontSize: 16, mr: 'var(--ob-space-050)' }} />
            {latestHeritageSubmission
              ? 'Update heritage submission'
              : 'New heritage submission'}
          </Button>
          <Button variant="ghost" size="sm" onClick={onNavigateToCompliance}>
            <Timeline sx={{ fontSize: 16, mr: 'var(--ob-space-050)' }} />
            View compliance path
          </Button>
        </Stack>
      </Stack>
    </Card>
  )
}
