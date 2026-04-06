import { formatCurrency } from './utils'

export const OPEN_PIPELINE_PENDING_COPY = 'Waiting for data...'

export function getOpenPipelineMetricDisplay(
  pipelineLoading: boolean,
  totalPipelineValue: number | null,
) {
  if (pipelineLoading) {
    return { kind: 'loading' as const, text: '-' }
  }
  if (totalPipelineValue === null) {
    return { kind: 'pending' as const, text: OPEN_PIPELINE_PENDING_COPY }
  }
  return {
    kind: 'value' as const,
    text: formatCurrency(totalPipelineValue),
  }
}
