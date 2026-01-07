import { describe, expect, it, vi } from 'vitest'
import React from 'react'
import { render, screen } from '@testing-library/react'

import { colors } from '@ob/tokens'
import type { PreviewLayerMetadata } from '../previewMetadata'
import { PreviewLayersTable } from '../components/property-overview/PreviewLayersTable'

vi.mock('../../../../components/canonical/Button', () => ({
  Button: ({ children }: { children: React.ReactNode }) => (
    <button type="button">{children}</button>
  ),
}))

describe('PreviewLayersTable', () => {
  it('renders risk badge class based on allocation', () => {
    const layers: PreviewLayerMetadata[] = [
      {
        id: 'layer-1',
        name: 'Residential',
        color: colors.brand[600],
        metrics: {
          allocationPct: 45,
          gfaSqm: 1000,
          niaSqm: 800,
          heightM: 50,
          floors: 12,
        },
        geometry: null,
      },
    ]

    render(
      <PreviewLayersTable
        layers={layers}
        visibility={{ 'layer-1': true }}
        focusLayerId={null}
        hiddenLayerCount={0}
        isLoading={false}
        error={null}
        onLayerAction={vi.fn()}
        onShowAll={vi.fn()}
        onResetFocus={vi.fn()}
        formatNumber={(value) => value.toString()}
      />,
    )

    const riskBadge = screen.getByText('high')
    expect(riskBadge).toHaveClass(
      'preview-layers-master-table__risk-badge',
      'preview-layers-master-table__risk-badge--high',
    )
  })
})
