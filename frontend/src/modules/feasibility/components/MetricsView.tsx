import { useMemo } from 'react'

import type { BuildableSummary } from '../types'

interface MetricsViewProps {
  result: BuildableSummary
  numberFormatter: Intl.NumberFormat
  t: (key: string) => string
}

export function MetricsView({ result, numberFormatter, t }: MetricsViewProps) {
  const metrics = useMemo(
    () => [
      {
        key: 'gfaCapM2',
        label: t('wizard.results.metrics.gfaCap'),
        value: numberFormatter.format(result.metrics.gfaCapM2),
        testId: 'gfa-cap',
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
      },
    ],
    [numberFormatter, result, t],
  )

  return (
    <dl className="feasibility-metrics">
      {metrics.map((metric) => (
        <div key={metric.key} className="feasibility-metrics__item">
          <dt>{metric.label}</dt>
          <dd data-testid={metric.testId}>{metric.value}</dd>
        </div>
      ))}
    </dl>
  )
}
