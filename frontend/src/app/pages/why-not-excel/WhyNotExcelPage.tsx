import { Box, Grid, Stack, Typography } from '@mui/material'

import { Card } from '../../../components/canonical/Card'
import { Button } from '../../../components/canonical/Button'
import { PRIMARY_MARKET } from '../../config/productFocus'
import { useRouterController } from '../../../router'

const DIFFERENTIATORS = [
  {
    title: 'Provenance, not hidden assumptions',
    body: 'Every Singapore screen can expose whether land, rules, and submissions are live, partner-gated, mocked, or unavailable. Excel usually leaves that trust layer implicit.',
  },
  {
    title: 'Audit evidence, not just outputs',
    body: 'Finance origin, workbook lineage, recipients, and submission-prep history are recorded into an evidence pack that can be handed to approvers and reviewers.',
  },
  {
    title: 'Shared workflow, not file passing',
    body: 'Deal calculator, workbook intake, finance, team coordination, and regulatory prep stay attached to the same project instead of fragmenting into emailed files.',
  },
  {
    title: 'Regulatory linkage, not manual copy-over',
    body: 'The product can tie development assumptions to Singapore compliance and submission-prep surfaces instead of leaving them disconnected from the model.',
  },
]

export function WhyNotExcelPage() {
  const { navigate } = useRouterController()

  return (
    <Stack spacing="var(--ob-space-200)">
      <Card variant="default" sx={{ p: 'var(--ob-space-250)' }}>
        <Stack spacing="var(--ob-space-150)">
          <Typography variant="h3">Why not Excel?</Typography>
          <Typography variant="body1" color="text.secondary">
            Excel is still the incumbent. The case for Optimal Build in{' '}
            {PRIMARY_MARKET}
            is not “spreadsheets are bad.” It is that underwriting becomes more
            defensible when provenance, audit, workbook intake, and regulatory
            linkage live in the same workflow.
          </Typography>
          <Box>
            <Button
              variant="primary"
              size="sm"
              onClick={() => navigate('/developers/deal-calculator')}
            >
              Model a deal in 5 minutes
            </Button>
          </Box>
        </Stack>
      </Card>

      <Grid container spacing="var(--ob-space-200)">
        {DIFFERENTIATORS.map((item) => (
          <Grid item xs={12} md={6} key={item.title}>
            <Card
              variant="default"
              sx={{ p: 'var(--ob-space-200)', height: '100%' }}
            >
              <Stack spacing="var(--ob-space-100)">
                <Typography variant="h6">{item.title}</Typography>
                <Typography variant="body2" color="text.secondary">
                  {item.body}
                </Typography>
              </Stack>
            </Card>
          </Grid>
        ))}
      </Grid>
    </Stack>
  )
}
