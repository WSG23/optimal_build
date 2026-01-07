import { afterEach, describe, expect, it, vi } from 'vitest'
import React from 'react'
import { act, render } from '@testing-library/react'

import {
  useUnifiedCapture,
  type UseUnifiedCaptureReturn,
} from '../useUnifiedCapture'

vi.mock('mapbox-gl', () => ({ default: {} }))

const mockCapturePropertyForDevelopment = vi.fn()
vi.mock('../../../../../api/siteAcquisition', () => ({
  capturePropertyForDevelopment: (...args: unknown[]) =>
    mockCapturePropertyForDevelopment(...args),
}))

const mockLogPropertyByGpsWithFeatures = vi.fn()
const mockFetchPropertyMarketIntelligence = vi.fn()
vi.mock('../../../../../api/agents', () => ({
  DEFAULT_SCENARIO_ORDER: ['raw_land', 'en_bloc'],
  logPropertyByGpsWithFeatures: (...args: unknown[]) =>
    mockLogPropertyByGpsWithFeatures(...args),
  fetchPropertyMarketIntelligence: (...args: unknown[]) =>
    mockFetchPropertyMarketIntelligence(...args),
}))

const mockForwardGeocodeAddress = vi.fn()
const mockReverseGeocodeCoords = vi.fn()
vi.mock('../../../../../api/geocoding', () => ({
  forwardGeocodeAddress: (...args: unknown[]) =>
    mockForwardGeocodeAddress(...args),
  reverseGeocodeCoords: (...args: unknown[]) =>
    mockReverseGeocodeCoords(...args),
}))

function renderHookHarness(isDeveloperMode: boolean) {
  const ref: { current: UseUnifiedCaptureReturn | null } = { current: null }

  function Harness() {
    ref.current = useUnifiedCapture({ isDeveloperMode })
    return null
  }

  render(<Harness />)
  if (!ref.current) {
    throw new Error('Hook harness did not produce a value')
  }
  return ref
}

describe('useUnifiedCapture', () => {
  afterEach(() => {
    vi.useRealTimers()
    vi.clearAllMocks()
    sessionStorage.clear()
  })

  it('runs the developer capture flow and persists the capture', async () => {
    vi.useFakeTimers()
    vi.setSystemTime(new Date('2026-01-06T10:00:00.000Z'))

    mockCapturePropertyForDevelopment.mockResolvedValue({
      propertyId: 'prop-123',
      currencySymbol: 'S$',
      address: { fullAddress: '1 Cyber Ave', district: 'Downtown' },
      quickAnalysis: { generatedAt: '2026-01-06T09:58:00Z', scenarios: [] },
      previewJob: null,
    })

    const hookRef = renderHookHarness(true)

    await act(async () => {
      hookRef.current!.setLatitude('1.2345')
      hookRef.current!.setLongitude('103.9876')
    })

    await act(async () => {
      const event = {
        preventDefault: vi.fn(),
      } as unknown as React.FormEvent<HTMLFormElement>
      const promise = hookRef.current!.handleCapture(event)
      vi.advanceTimersByTime(1500)
      await promise
    })

    expect(mockCapturePropertyForDevelopment).toHaveBeenCalledWith(
      expect.objectContaining({
        latitude: 1.2345,
        longitude: 103.9876,
        jurisdictionCode: 'SG',
        previewDetailLevel: 'medium',
      }),
    )

    const persisted = sessionStorage.getItem(
      'site-acquisition:captured-property',
    )
    expect(persisted).toContain('"propertyId":"prop-123"')

    expect(hookRef.current!.siteAcquisitionResult?.propertyId).toBe('prop-123')
    expect(hookRef.current!.capturedSites[0]?.propertyId).toBe('prop-123')
    expect(hookRef.current!.capturedSites[0]?.address).toBe('1 Cyber Ave')
    expect(hookRef.current!.capturedSites[0]?.capturedAt).toBe(
      '2026-01-06T10:00:01.500Z',
    )
  })

  it('runs the agent capture flow and fetches market intelligence', async () => {
    vi.useFakeTimers()
    vi.setSystemTime(new Date('2026-01-06T10:00:00.000Z'))

    mockLogPropertyByGpsWithFeatures.mockResolvedValue({
      propertyId: 'gps-777',
      address: { fullAddress: 'Mocked Address 777', district: 'Central' },
      quickAnalysis: { scenarios: [{ scenario: 'raw_land' }] },
      developerFeatures: { preview3D: false },
      timestamp: '2026-01-06T10:00:00.000Z',
    })
    mockFetchPropertyMarketIntelligence.mockResolvedValue({ summary: 'ok' })

    const hookRef = renderHookHarness(false)

    await act(async () => {
      hookRef.current!.setAddress('Manual Address Override')
      hookRef.current!.setLatitude('1.1111')
      hookRef.current!.setLongitude('103.2222')
    })

    await act(async () => {
      const event = {
        preventDefault: vi.fn(),
      } as unknown as React.FormEvent<HTMLFormElement>
      const promise = hookRef.current!.handleCapture(event)
      vi.advanceTimersByTime(1500)
      await promise
    })

    expect(mockLogPropertyByGpsWithFeatures).toHaveBeenCalledWith(
      expect.objectContaining({
        latitude: 1.1111,
        longitude: 103.2222,
        jurisdictionCode: 'SG',
        enabledFeatures: expect.any(Object),
      }),
    )
    expect(mockFetchPropertyMarketIntelligence).toHaveBeenCalledWith('gps-777')
    expect(hookRef.current!.captureSummary?.propertyId).toBe('gps-777')
    expect(hookRef.current!.marketSummary).toEqual({ summary: 'ok' })
    expect(hookRef.current!.capturedSites[0]?.address).toBe(
      'Manual Address Override',
    )
  })

  it('sets a validation error when coordinates are invalid', async () => {
    const hookRef = renderHookHarness(true)

    await act(async () => {
      hookRef.current!.setLatitude('not-a-number')
      hookRef.current!.setLongitude('103.8500')
    })

    await act(async () => {
      const event = {
        preventDefault: vi.fn(),
      } as unknown as React.FormEvent<HTMLFormElement>
      await hookRef.current!.handleCapture(event)
    })

    expect(hookRef.current!.captureError).toBe(
      'Please provide valid coordinates.',
    )
    expect(mockCapturePropertyForDevelopment).not.toHaveBeenCalled()
    expect(mockLogPropertyByGpsWithFeatures).not.toHaveBeenCalled()
  })
})
