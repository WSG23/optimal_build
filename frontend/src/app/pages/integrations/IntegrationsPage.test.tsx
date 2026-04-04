// @vitest-environment jsdom

import { describe, expect, it } from 'vitest'
import { render, screen } from '@testing-library/react'

import { IntegrationsPage } from './IntegrationsPage'

describe('IntegrationsPage', () => {
  it('shows explicit partner-gated states instead of mock connect actions', () => {
    render(<IntegrationsPage />)

    expect(screen.getByText('Singapore data partnerships')).toBeInTheDocument()
    expect(screen.getByText('URA Data Service')).toBeInTheDocument()
    expect(screen.getAllByText('Partner access required').length).toBeGreaterThan(0)
    expect(screen.getByText('Coming soon')).toBeInTheDocument()
    expect(
      screen.queryByRole('button', { name: /connect/i }),
    ).not.toBeInTheDocument()
  })
})
