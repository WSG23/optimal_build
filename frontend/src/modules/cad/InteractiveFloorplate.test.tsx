import { describe, expect, it } from 'vitest'
import { render, screen } from '@testing-library/react'

import { InteractiveFloorplate } from './InteractiveFloorplate'

const sampleUnit = {
  id: 'unit-1',
  floor: 1,
  unitLabel: 'A-101',
  areaSqm: 42,
  status: 'approved' as const,
  severity: 'low' as const,
}

describe('InteractiveFloorplate', () => {
  it('renders a dedicated loading placeholder while overlays are being prepared', () => {
    render(<InteractiveFloorplate units={[]} loading={true} />)

    expect(screen.getByText('Preparing detection overlays')).toBeInTheDocument()
    expect(screen.getByText('Scanning sectors')).toBeInTheDocument()
  })

  it('renders the CAD upload empty state when no units are available', () => {
    render(<InteractiveFloorplate units={[]} loading={false} />)

    expect(
      screen.getByText('Upload a CAD file to see detection results'),
    ).toBeInTheDocument()
    expect(screen.getByText('CAD detection ready')).toBeInTheDocument()
  })

  it('renders unit labels when floorplate data is available', () => {
    render(<InteractiveFloorplate units={[sampleUnit]} loading={false} />)

    expect(screen.getByText('A-101')).toBeInTheDocument()
    expect(
      screen.queryByText('Upload a CAD file to see detection results'),
    ).not.toBeInTheDocument()
  })
})
