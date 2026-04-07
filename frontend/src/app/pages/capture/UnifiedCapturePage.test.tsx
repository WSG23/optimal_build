import { describe, expect, it, vi } from 'vitest'
import React from 'react'
import { render, screen, fireEvent } from '@testing-library/react'

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
  it('renders agent-mode results by default', () => {
    mockUseDeveloperMode.mockReturnValue({
      isDeveloperMode: false,
      toggleDeveloperMode: mockToggleDeveloperMode,
    })

    const handleScenarioToggle = vi.fn()
    mockUseUnifiedCapture.mockReturnValue({
      latitude: '1.3',
      longitude: '103.85',
      address: '',
      selectedScenarios: ['raw_land'],
      setLatitude: vi.fn(),
      setLongitude: vi.fn(),
      setAddress: vi.fn(),
      handleScenarioToggle,
      isCapturing: false,
      isScanning: false,
      captureError: null,
      captureSummary: null,
      marketSummary: null,
      marketLoading: false,
      capturedSites: [],
      siteAcquisitionResult: null,
      geocodeError: null,
      mapContainerRef: { current: null },
      mapError: null,
      handleCapture: vi.fn((e: React.FormEvent<HTMLFormElement>) =>
        e.preventDefault(),
      ),
    })

    render(<UnifiedCapturePage />)

    expect(screen.getByTestId('agent-results')).toBeInTheDocument()
    expect(screen.getByTestId('mission-log')).toBeInTheDocument()

    const rawLandTile = screen.getByRole('button', { name: /Raw Land/i })
    fireEvent.click(rawLandTile)
    expect(handleScenarioToggle).toHaveBeenCalledWith('raw_land')
  })

  it('keeps the location form focused on address and coordinates', () => {
    mockUseDeveloperMode.mockReturnValue({
      isDeveloperMode: false,
      toggleDeveloperMode: mockToggleDeveloperMode,
    })

    mockUseUnifiedCapture.mockReturnValue({
      latitude: '1.3',
      longitude: '103.85',
      address: '45 Burghley Dr, Singapore 559022',
      selectedScenarios: ['raw_land'],
      setLatitude: vi.fn(),
      setLongitude: vi.fn(),
      setAddress: vi.fn(),
      handleScenarioToggle: vi.fn(),
      isCapturing: false,
      isScanning: false,
      captureError: null,
      captureSummary: null,
      marketSummary: null,
      marketLoading: false,
      capturedSites: [],
      siteAcquisitionResult: null,
      geocodeError: null,
      mapContainerRef: { current: null },
      mapError: null,
      handleCapture: vi.fn((e: React.FormEvent<HTMLFormElement>) =>
        e.preventDefault(),
      ),
    })

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
  })

  it('renders the developer workspace when developer mode has results', async () => {
    mockUseDeveloperMode.mockReturnValue({
      isDeveloperMode: true,
      toggleDeveloperMode: mockToggleDeveloperMode,
    })

    mockUseUnifiedCapture.mockReturnValue({
      latitude: '1.3',
      longitude: '103.85',
      address: '',
      selectedScenarios: ['raw_land'],
      setLatitude: vi.fn(),
      setLongitude: vi.fn(),
      setAddress: vi.fn(),
      handleScenarioToggle: vi.fn(),
      isCapturing: false,
      isScanning: false,
      captureError: null,
      captureSummary: null,
      marketSummary: null,
      marketLoading: false,
      capturedSites: [],
      siteAcquisitionResult: { propertyId: 'prop-1' },
      geocodeError: null,
      mapContainerRef: { current: null },
      mapError: null,
      handleCapture: vi.fn((e: React.FormEvent<HTMLFormElement>) =>
        e.preventDefault(),
      ),
    })

    render(<UnifiedCapturePage />)

    expect(await screen.findByTestId('developer-results')).toBeInTheDocument()
    expect(screen.getByTestId('mission-log')).toBeInTheDocument()
  })
})
