import { describe, expect, it } from 'vitest'

import {
  getOpenPipelineMetricDisplay,
  OPEN_PIPELINE_PENDING_COPY,
} from './metricDisplay'

describe('getOpenPipelineMetricDisplay', () => {
  it('returns loading state while the pipeline is still fetching', () => {
    expect(getOpenPipelineMetricDisplay(true, null)).toEqual({
      kind: 'loading',
      text: '-',
    })
  })

  it('returns the pending placeholder only when data is absent after loading', () => {
    expect(getOpenPipelineMetricDisplay(false, null)).toEqual({
      kind: 'pending',
      text: OPEN_PIPELINE_PENDING_COPY,
    })
  })

  it('keeps an explicit zero value instead of collapsing it into pending copy', () => {
    const display = getOpenPipelineMetricDisplay(false, 0)

    expect(display.kind).toBe('value')
    expect(display.text).not.toBe(OPEN_PIPELINE_PENDING_COPY)
    expect(display.text).toMatch(/0/)
  })
})
