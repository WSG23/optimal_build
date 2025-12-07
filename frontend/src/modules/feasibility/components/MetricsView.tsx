import { useMemo } from 'react'

import type { BuildableSummary } from '../types'

interface MetricsViewProps {
  result: BuildableSummary
  numberFormatter: Intl.NumberFormat
  t: (key: string) => string
}

export function MetricsView({ result, numberFormatter, t }: MetricsViewProps) {
  const accuracy = result.metrics.accuracyRange ?? 0.25
  const accuracyPercent = Math.round(accuracy * 100)

  // Color coding: <10% = Good (Green), 10-20% = Medium (Blue), >20% = Low (Orange)
  const accuracyColor =
    accuracy <= 0.1
      ? 'var(--ob-color-success-text)'
      : accuracy <= 0.2
        ? 'var(--ob-color-accent)'
        : 'var(--ob-color-warning-text)'

  const accuracyBg =
    accuracy <= 0.1
      ? 'var(--ob-color-success-bg)'
      : accuracy <= 0.2
        ? 'var(--ob-color-accent-light)'
        : 'var(--ob-color-warning-bg)'

  const metrics = useMemo(
    () => [
      {
        key: 'gfaCapM2',
        label: t('wizard.results.metrics.gfaCap'),
        value: numberFormatter.format(result.metrics.gfaCapM2),
        testId: 'gfa-cap',
        showAccuracy: true,
      },
      {
        key: 'floorsMax',
        label: t('wizard.results.metrics.floorsMax'),
        value: numberFormatter.format(result.metrics.floorsMax),
        testId: 'floors-max',
      },
      {
        key: 'footprintM2',
        label: t('wizard.results.metrics.footprint'),
        value: numberFormatter.format(result.metrics.footprintM2),
        testId: 'footprint',
      },
      {
        key: 'nsaEstM2',
        label: t('wizard.results.metrics.nsa'),
        value: numberFormatter.format(result.metrics.nsaEstM2),
        testId: 'nsa-est',
        showAccuracy: true,
      },
    ],
    [numberFormatter, result, t],
  )

  return (
    <dl className="feasibility-metrics">
      {metrics.map((metric) => (
        <div key={metric.key} className="feasibility-metrics__item">
          <dt>
            {metric.label}
            {metric.showAccuracy && (
              <span
                style={{
                  display: 'inline-block',
                  marginLeft: '8px',
                  fontSize: '0.6875rem',
                  fontWeight: 600,
                  color: accuracyColor,
                  background: accuracyBg,
                  padding: '1px 6px',
                  borderRadius: '999px',
                  verticalAlign: 'middle',
                }}
              >
                ±{accuracyPercent}%
              </span>
            )}
          </dt>
          <dd data-testid={metric.testId}>{metric.value}</dd>
        </div>
      ))}
    </dl>
  )
}
