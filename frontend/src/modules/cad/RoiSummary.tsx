import { useTranslation } from '../../i18n'
import { RoiMetrics } from './types'
import { Box, Chip, Skeleton } from '@mui/material'
import { keyframes } from '@emotion/react'

const pulse = keyframes`
  0% { opacity: 1; }
  50% { opacity: 0.5; }
  100% { opacity: 1; }
`

interface RoiSummaryProps {
  metrics: RoiMetrics
  loading?: boolean
  isLive?: boolean
}

export function RoiSummary({ metrics, loading, isLive }: RoiSummaryProps) {
  const { t } = useTranslation()

  return (
    <section className="cad-panel">
      <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', mb: 2 }}>
        <Box>
          <h3>{t('panels.roiTitle')}</h3>
          <p>{t('panels.roiSubtitle')}</p>
        </Box>
        {isLive && (
          <Chip
            label="LIVE"
            size="small"
            color="success"
            variant="outlined"
            sx={{
              height: 20,
              fontSize: '0.65rem',
              fontWeight: 'bold',
              '& .MuiChip-label': { px: 1 },
              animation: `${pulse} 2s infinite ease-in-out`
            }}
          />
        )}
      </Box>
      <dl className="cad-roi">
        <div>
          <dt>{t('pipelines.automationScore')}</dt>
          <dd>
            {loading ? <Skeleton width={40} /> : `${Math.round(metrics.automationScore * 100)}%`}
          </dd>
        </div>
        <div>
          <dt>{t('pipelines.savings')}</dt>
          <dd>
            {loading ? <Skeleton width={40} /> : `${metrics.savingsPercent}%`}
          </dd>
        </div>
        <div>
          <dt>{t('pipelines.reviewHours')}</dt>
          <dd>
            {loading ? <Skeleton width={40} /> : `${metrics.reviewHoursSaved}h`}
          </dd>
        </div>
        <div>
          <dt>{t('pipelines.payback')}</dt>
          <dd>
            {loading ? <Skeleton width={60} /> : t('pipelines.weeks', { count: metrics.paybackWeeks })}
          </dd>
        </div>
      </dl>
    </section>
  )
}

export default RoiSummary
