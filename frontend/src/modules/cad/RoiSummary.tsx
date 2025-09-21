import { RoiMetrics } from './types'
import { useLocale } from '../../i18n/LocaleContext'

interface RoiSummaryProps {
  metrics: RoiMetrics
}

export function RoiSummary({ metrics }: RoiSummaryProps) {
  const { strings } = useLocale()

  return (
    <section className="cad-panel">
      <h3>{strings.panels.roiTitle}</h3>
      <p>{strings.panels.roiSubtitle}</p>
      <dl className="cad-roi">
        <div>
          <dt>{strings.pipelines.automationScore}</dt>
          <dd>{Math.round(metrics.automationScore * 100)}%</dd>
        </div>
        <div>
          <dt>{strings.pipelines.savings}</dt>
          <dd>{metrics.savingsPercent}%</dd>
        </div>
        <div>
          <dt>{strings.pipelines.reviewHours}</dt>
          <dd>{metrics.reviewHoursSaved}h</dd>
        </div>
        <div>
          <dt>Payback</dt>
          <dd>{metrics.paybackWeeks} weeks</dd>
        </div>
      </dl>
    </section>
  )
}

export default RoiSummary
