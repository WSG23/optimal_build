import { Box, Typography } from '@mui/material'
import ArrowForward from '@mui/icons-material/ArrowForward'
import { Button } from '../../../components/canonical/Button'
import { Card } from '../../../components/canonical/Card'
import { useTranslation } from '../../../i18n'
import { AllocationRing } from './AllocationRing'

interface ChartDataEntry {
  name: string
  value: number
  color: string
}

interface AllocationSummaryPanelProps {
  chartData: ChartDataEntry[]
  unallocated: number
  totalRevenue: number
  saving: boolean
}

export function AllocationSummaryPanel({
  chartData,
  unallocated,
  totalRevenue,
  saving,
}: AllocationSummaryPanelProps) {
  const { t } = useTranslation()

  return (
    <Box sx={{ minWidth: 0 }}>
      <Card
        sx={{
          p: 'var(--ob-space-150)',
          height: '100%',
          display: 'flex',
          flexDirection: 'column',
        }}
      >
        <Typography
          variant="h6"
          component="h3"
          sx={{
            fontWeight: 'var(--ob-font-weight-semibold)',
            mb: 'var(--ob-space-150)',
            textTransform: 'uppercase',
            letterSpacing: 'var(--ob-letter-spacing-wider)',
            fontSize: 'var(--ob-font-size-xs)',
          }}
        >
          {t('finance.allocation.title', {
            defaultValue: 'ALLOCATION MIX',
          })}
        </Typography>

        <Box
          sx={{
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            flex: 1,
            gap: 'var(--ob-space-200)',
          }}
        >
          <AllocationRing
            data={chartData}
            totalAllocation={100 - unallocated}
            size={160}
          />

          <Box
            sx={{
              display: 'flex',
              flexDirection: 'column',
              gap: 'var(--ob-space-050)',
            }}
          >
            {chartData
              .filter((d) => d.name !== 'Pending')
              .map((entry) => (
                <Box
                  key={entry.name}
                  sx={{
                    display: 'flex',
                    alignItems: 'center',
                    gap: 'var(--ob-space-050)',
                  }}
                >
                  <Box
                    sx={{
                      width: 'var(--ob-space-050)',
                      height: 'var(--ob-space-050)',
                      borderRadius: 'var(--ob-radius-pill)',
                      bgcolor: entry.color,
                    }}
                  />
                  <Typography
                    variant="body2"
                    sx={{ color: 'text.secondary', minWidth: 60 }}
                  >
                    {entry.name}
                  </Typography>
                  <Typography
                    variant="body2"
                    sx={{ fontWeight: 'var(--ob-font-weight-semibold)' }}
                  >
                    {entry.value}%
                  </Typography>
                </Box>
              ))}
          </Box>
        </Box>

        <Card
          sx={{
            mt: 'var(--ob-space-200)',
            p: 'var(--ob-space-100)',
            bgcolor: 'action.hover',
            border: 'none',
          }}
        >
          <Typography
            variant="caption"
            sx={{
              color: 'text.secondary',
              display: 'block',
              mb: 'var(--ob-space-025)',
            }}
          >
            {t('finance.scenarioCreator.totalAnnualRevenue')}
          </Typography>
          <Typography
            variant="h4"
            sx={{ fontWeight: 'var(--ob-font-weight-bold)' }}
          >
            ${totalRevenue.toLocaleString()}
          </Typography>
        </Card>

        <Button
          type="submit"
          fullWidth
          variant="primary"
          size="lg"
          sx={{ mt: 'var(--ob-space-150)' }}
          endIcon={<ArrowForward fontSize="small" />}
          disabled={saving}
        >
          {saving
            ? t('finance.scenarioCreator.actions.saving')
            : t('finance.scenarioCreator.actions.submit')}
        </Button>
      </Card>
    </Box>
  )
}
