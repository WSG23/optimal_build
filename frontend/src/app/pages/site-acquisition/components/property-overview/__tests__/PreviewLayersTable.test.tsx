import { render, screen } from '@testing-library/react'
import { describe, expect, it, vi } from 'vitest'

import { PreviewLayersTable } from '../PreviewLayersTable'

describe('PreviewLayersTable', () => {
  it('uses capture-safe labels and hides floors when metadata is absent', () => {
    render(
      <PreviewLayersTable
        layers={[
          {
            id: 'office',
            name: 'office',
            color: '#2196f3',
            metrics: {
              allocationPct: 54,
              gfaSqm: 7616,
              niaSqm: 6245,
              heightM: 6.4,
              floors: null,
            },
            geometry: null,
          },
        ]}
        visibility={{ office: true }}
        focusLayerId={null}
        hiddenLayerCount={0}
        isLoading={false}
        error={null}
        onLayerAction={vi.fn()}
        onShowAll={vi.fn()}
        onResetFocus={vi.fn()}
        formatNumber={(value, options) =>
          new Intl.NumberFormat('en-SG', options).format(value)
        }
      />,
    )

    expect(screen.getByText('Preview Layers')).toBeInTheDocument()
    expect(screen.getByText('Layer Share')).toBeInTheDocument()
    expect(screen.getByText('Flag')).toBeInTheDocument()
    expect(screen.queryByText('Mix %')).not.toBeInTheDocument()
    expect(screen.queryByText('Risk')).not.toBeInTheDocument()
    expect(screen.queryByText('Floors')).not.toBeInTheDocument()
  })
})
