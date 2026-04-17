import { Box, Stack, Typography } from '@mui/material'

import { Button } from '../../components/canonical/Button'
import { Card } from '../../components/canonical/Card'

interface FinanceOverviewCardProps {
  navigate: (path: string) => void
  handleExportWorkbook: () => void
  handleExportCsv: () => void
  hasPrimaryScenario: boolean
  exportingWorkbook: boolean
  exportingScenario: boolean
}

export function FinanceOverviewCard({
  navigate,
  handleExportWorkbook,
  handleExportCsv,
  hasPrimaryScenario,
  exportingWorkbook,
  exportingScenario,
}: FinanceOverviewCardProps) {
  return (
    <Card
      variant="default"
      sx={{
        mb: 'var(--ob-space-150)',
        p: 'var(--ob-space-200)',
      }}
    >
      <Stack
        direction={{ xs: 'column', md: 'row' }}
        spacing={1.5}
        justifyContent="space-between"
      >
        <Box>
          <Typography variant="h6">
            Finance mode for Singapore developers
          </Typography>
          <Typography variant="body2" color="text.secondary">
            Build a scenario from a deal screen, import a workbook, or start
            from an SG template. Then package outputs for lenders, investors,
            and internal approvals.
          </Typography>
        </Box>
        <Stack direction="row" spacing={1} flexWrap="wrap" useFlexGap>
          <Button
            variant="secondary"
            size="sm"
            onClick={() => navigate('/developers/why-not-excel')}
          >
            Why not Excel?
          </Button>
          <Button
            variant="ghost"
            size="sm"
            onClick={handleExportWorkbook}
            disabled={!hasPrimaryScenario || exportingWorkbook}
          >
            {exportingWorkbook ? 'Preparing workbook...' : 'Lender workbook'}
          </Button>
          <Button
            variant="ghost"
            size="sm"
            onClick={handleExportCsv}
            disabled={!hasPrimaryScenario || exportingScenario}
          >
            {exportingScenario ? 'Preparing export...' : 'Investor export'}
          </Button>
        </Stack>
      </Stack>
    </Card>
  )
}
