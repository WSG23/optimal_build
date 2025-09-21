import { useTranslation } from '../../i18n'
import { RoiMetrics } from './types'

interface RoiSummaryProps {
  metrics: RoiMetrics
}

export function RoiSummary({ metrics }: RoiSummaryProps) {
  const { t } = useTranslation()

  return (
    <section className="cad-panel">
      <h3>{t('panels.roiTitle')}</h3>
      <p>{t('panels.roiSubtitle')}</p>
      <dl className="cad-roi">
        <div>
          <dt>{t('pipelines.automationScore')}</dt>
          <dd>{Math.round(metrics.automationScore * 100)}%</dd>
        </div>
        <div>
          <dt>{t('pipelines.savings')}</dt>
          <dd>{metrics.savingsPercent}%</dd>
        </div>
        <div>
          <dt>{t('pipelines.reviewHours')}</dt>
          <dd>{metrics.reviewHoursSaved}h</dd>
        </div>
        <div>
          <dt>{t('pipelines.payback')}</dt>
          <dd>{t('pipelines.weeks', { count: metrics.paybackWeeks })}</dd>
        </div>
      </dl>
    </section>
  )
}

export default RoiSummary
