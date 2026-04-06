import { Assessment, AttachMoney, Map, ShowChart } from '@mui/icons-material'
import { Box, Grid, Stack, Typography } from '@mui/material'

import type { DealCalculatorResult } from '../../../../api/dealCalculator'
import { Button } from '../../../../components/canonical/Button'
import { Card } from '../../../../components/canonical/Card'
import { EmptyState } from '../../../../components/canonical/EmptyState'
import { MetricTile } from '../../../../components/canonical/MetricTile'

interface DealResultsPanelProps {
  result: DealCalculatorResult | null
  sourceNotes: string[]
  handoffMessage: string | null
  onFinanceHandoff: () => void
}

function formatCurrency(value: number | null | undefined): string {
  if (value == null) {
    return '-'
  }
  return new Intl.NumberFormat('en-SG', {
    style: 'currency',
    currency: 'SGD',
    maximumFractionDigits: 0,
  }).format(value)
}

function formatPercent(value: number | null | undefined): string {
  if (value == null) {
    return '-'
  }
  return `${(value * 100).toFixed(2)}%`
}

export function DealResultsPanel({
  result,
  sourceNotes,
  handoffMessage,
  onFinanceHandoff,
}: DealResultsPanelProps) {
  if (!result) {
    return (
      <EmptyState
        title="Results will appear here"
        description="Run a deal screen to review the build envelope, finance summary, and handoff notes."
        size="md"
      />
    )
  }

  return (
    <Stack spacing="var(--ob-space-200)">
      <Grid container spacing="var(--ob-space-150)">
        <Grid item xs={12} sm={6}>
          <MetricTile
            label="Estimated GFA"
            value={result.feasibilitySummary.estimatedAchievableGfaSqm.toLocaleString()}
            trend={`${result.feasibilitySummary.estimatedUnitCount} units`}
            icon={<Assessment fontSize="small" />}
            variant="compact"
            sx={{ height: '100%' }}
          />
        </Grid>
        <Grid item xs={12} sm={6}>
          <MetricTile
            label="Total Capex"
            value={formatCurrency(result.financeSummary.totalCapexSgd)}
            icon={<AttachMoney fontSize="small" />}
            variant="compact"
            sx={{ height: '100%' }}
          />
        </Grid>
        <Grid item xs={12} sm={6}>
          <MetricTile
            label="IRR"
            value={formatPercent(result.financeSummary.irr)}
            icon={<ShowChart fontSize="small" />}
            variant="compact"
            sx={{ height: '100%' }}
          />
        </Grid>
        <Grid item xs={12} sm={6}>
          <MetricTile
            label="MOIC"
            value={
              result.financeSummary.moic == null
                ? '-'
                : `${result.financeSummary.moic.toFixed(2)}x`
            }
            icon={<Map fontSize="small" />}
            variant="compact"
            sx={{ height: '100%' }}
          />
        </Grid>
      </Grid>

      <Card variant="default" sx={{ p: 'var(--ob-space-200)' }}>
        <Stack spacing="var(--ob-space-150)">
          <Box>
            <Typography variant="h6">Deal screen summary</Typography>
            <Typography variant="body2" color="text.secondary">
              {result.site.formattedAddress}
            </Typography>
          </Box>

          <Stack
            direction={{ xs: 'column', sm: 'row' }}
            spacing="var(--ob-space-150)"
          >
            <Box sx={{ minWidth: 0 }}>
              <Typography variant="overline">Planning</Typography>
              <Typography variant="body2" color="text.secondary">
                Zone {result.buildEnvelope.zoneCode ?? 'Unknown'} • Plot ratio{' '}
                {result.buildEnvelope.allowablePlotRatio ?? '-'}
              </Typography>
            </Box>
            <Box sx={{ minWidth: 0 }}>
              <Typography variant="overline">Finance</Typography>
              <Typography variant="body2" color="text.secondary">
                NOI {formatCurrency(result.financeSummary.totalAnnualNoiSgd)} •
                Exit{' '}
                {formatCurrency(result.financeSummary.estimatedExitValueSgd)}
              </Typography>
            </Box>
          </Stack>

          {result.recommendations.length > 0 && (
            <Box>
              <Typography variant="overline">Recommendations</Typography>
              <Stack
                component="ul"
                spacing="var(--ob-space-050)"
                sx={{ pl: 2, m: 0 }}
              >
                {result.recommendations.slice(0, 4).map((recommendation) => (
                  <Typography
                    key={recommendation}
                    component="li"
                    variant="body2"
                    color="text.secondary"
                  >
                    {recommendation}
                  </Typography>
                ))}
              </Stack>
            </Box>
          )}

          {sourceNotes.length > 0 && (
            <Box>
              <Typography variant="overline">Data provenance</Typography>
              <Stack spacing="var(--ob-space-025)">
                {sourceNotes.map((note) => (
                  <Typography key={note} variant="body2" color="text.secondary">
                    {note}
                  </Typography>
                ))}
              </Stack>
            </Box>
          )}

          <Stack
            direction={{ xs: 'column', sm: 'row' }}
            spacing="var(--ob-space-100)"
            alignItems={{ xs: 'stretch', sm: 'center' }}
          >
            <Button variant="primary" onClick={onFinanceHandoff}>
              Save finance handoff
            </Button>
            {handoffMessage && (
              <Typography variant="body2" color="text.secondary">
                {handoffMessage}
              </Typography>
            )}
          </Stack>
        </Stack>
      </Card>
    </Stack>
  )
}
