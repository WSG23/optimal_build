import { describe, expect, it } from 'vitest'
import { render, screen } from '@testing-library/react'

import { Preview3DViewer } from './Preview3DViewer'

describe('Preview3DViewer', () => {
  it('shows a queued starter-model state when no preview asset is available yet', () => {
    render(<Preview3DViewer previewUrl={null} status="queued" />)

    expect(screen.getByText('Starter model queued')).toBeInTheDocument()
    expect(
      screen.getByText(/scenario-specific starter model/i),
    ).toBeInTheDocument()
  })

  it('shows a processing state while a starter model is being generated', () => {
    render(<Preview3DViewer previewUrl={null} status="processing" />)

    expect(screen.getByText('Generating starter model')).toBeInTheDocument()
    expect(
      screen.getByText(/switch to the 3d model when processing completes/i),
    ).toBeInTheDocument()
  })

  it('shows a retry-oriented failure state when generation fails', () => {
    render(<Preview3DViewer previewUrl={null} status="failed" />)

    expect(screen.getByText('Starter model unavailable')).toBeInTheDocument()
    expect(screen.getByText(/retry the generation action/i)).toBeInTheDocument()
  })

  it('shows a fallback preview state for placeholder geometry', () => {
    render(<Preview3DViewer previewUrl={null} status="placeholder" />)

    expect(screen.getByText('Fallback preview only')).toBeInTheDocument()
    expect(
      screen.getByText(/parcel-level scalar controls/i),
    ).toBeInTheDocument()
  })

  it('shows thumbnail context when available without a preview asset', () => {
    render(
      <Preview3DViewer
        previewUrl={null}
        status="ready"
        thumbnailUrl="/static/preview-thumb.png"
      />,
    )

    expect(screen.getByText('Starter model syncing')).toBeInTheDocument()
    expect(screen.getByText('Latest thumbnail')).toBeInTheDocument()
    expect(screen.getByAltText('Starter model thumbnail')).toHaveAttribute(
      'src',
      '/static/preview-thumb.png',
    )
  })
})
