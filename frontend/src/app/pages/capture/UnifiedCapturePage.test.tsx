import { describe, expect, it, vi } from 'vitest'
import React from 'react'
import { render, screen } from '@testing-library/react'

import { UnifiedCapturePage } from './UnifiedCapturePage'

vi.mock('mapbox-gl/dist/mapbox-gl.css', () => ({}))

const mockToggleDeveloperMode = vi.fn()
const mockUseDeveloperMode = vi.fn()
vi.mock('../../../contexts/useDeveloperMode', () => ({
  useDeveloperMode: () => mockUseDeveloperMode(),
}))

const mockUseUnifiedCapture = vi.fn()
vi.mock('./hooks/useUnifiedCapture', () => ({
  useUnifiedCapture: (args: unknown) => mockUseUnifiedCapture(args),
}))

vi.mock('./components/AgentResultsPanel', () => ({
  AgentResultsPanel: () => <div data-testid="agent-results">AGENT RESULTS</div>,
}))

vi.mock('./components/MissionLog', () => ({
  MissionLog: () => <div data-testid="mission-log">MISSION LOG</div>,
}))

vi.mock('./components/DeveloperResults', () => ({
  DeveloperResults: () => (
    <div data-testid="developer-results">DEV RESULTS</div>
  ),
}))

describe('UnifiedCapturePage', () => {
  function buildCaptureHookValue(overrides: Record<string, unknown> = {}) {
    return {
      latitude: '1.3',
      longitude: '103.85',
      address: '',
      selectedScenarios: [],
      setLatitude: vi.fn(),
      setLongitude: vi.fn(),
      setAddress: vi.fn(),
      handleScenarioToggle: vi.fn(),
      isCapturing: false,
      isScanning: false,
      captureError: null,
      hasResults: false,
      captureSummary: null,
      developerFeatures: null,
      marketSummary: null,
      marketLoading: false,
      capturedSites: [],
      siteAcquisitionResult: null,
      geocodeError: null,
      isGeocoding: false,
      mapContainerRef: { current: null },
      addressInputRef: { current: null },
      mapError: null,
      isMapLoading: false,
      targetAcquired: null,
      handleCapture: vi.fn((e: React.FormEvent<HTMLFormElement>) =>
        e.preventDefault(),
      ),
      handleNewCapture: vi.fn(),
      handleCancelCapture: vi.fn(),
      ...overrides,
    }
  }

  it('renders agent-mode results by default', () => {
    mockUseDeveloperMode.mockReturnValue({
      isDeveloperMode: false,
      toggleDeveloperMode: mockToggleDeveloperMode,
    })

    mockUseUnifiedCapture.mockReturnValue(buildCaptureHookValue())

    render(<UnifiedCapturePage />)

    expect(screen.getByTestId('agent-results')).toBeInTheDocument()
    expect(screen.getByTestId('mission-log')).toBeInTheDocument()
    expect(screen.queryByText('Scenario')).not.toBeInTheDocument()
    expect(
      screen.queryByRole('button', { name: /raw land/i }),
    ).not.toBeInTheDocument()
    expect(
      screen.getByRole('button', { name: /scan & analyze/i }),
    ).toBeEnabled()
  })

  it('keeps the location form focused on address and coordinates', () => {
    mockUseDeveloperMode.mockReturnValue({
      isDeveloperMode: false,
      toggleDeveloperMode: mockToggleDeveloperMode,
    })

    mockUseUnifiedCapture.mockReturnValue(
      buildCaptureHookValue({
        address: '45 Burghley Dr, Singapore 559022',
      }),
    )

    render(<UnifiedCapturePage />)

    expect(
      screen.getByText(
        'Address updates the map and coordinates automatically.',
      ),
    ).toBeInTheDocument()
    expect(screen.queryByText('Region')).not.toBeInTheDocument()
    expect(
      screen.queryByRole('button', { name: /geocode address/i }),
    ).not.toBeInTheDocument()
    expect(
      screen.queryByRole('button', { name: /reverse geocode/i }),
    ).not.toBeInTheDocument()
    expect(screen.queryByText('Scenario')).not.toBeInTheDocument()
    expect(
      screen.getByRole('button', { name: /scan & analyze/i }),
    ).toBeEnabled()
    expect(document.querySelector('form')).toHaveAttribute('novalidate')
    expect(screen.getByLabelText('Lat')).not.toHaveAttribute('pattern')
    expect(screen.getByLabelText('Lng')).not.toHaveAttribute('pattern')
  })

  it('renders the developer workspace when developer mode has results', async () => {
    mockUseDeveloperMode.mockReturnValue({
      isDeveloperMode: true,
      toggleDeveloperMode: mockToggleDeveloperMode,
    })

    mockUseUnifiedCapture.mockReturnValue(
      buildCaptureHookValue({
        siteAcquisitionResult: { propertyId: 'prop-1' },
      }),
    )

    render(<UnifiedCapturePage />)

    expect(await screen.findByTestId('developer-results')).toBeInTheDocument()
    expect(screen.getByTestId('mission-log')).toBeInTheDocument()
  })
})
