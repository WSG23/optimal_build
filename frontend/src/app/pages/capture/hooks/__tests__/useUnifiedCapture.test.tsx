import { afterEach, describe, expect, it, vi } from 'vitest'
import React from 'react'
import { act, cleanup, render } from '@testing-library/react'

import {
  useUnifiedCapture,
  type UseUnifiedCaptureReturn,
} from '../useUnifiedCapture'

const mockMapConstructor = vi.fn()
const mockMapAddListener = vi.fn()
const mockMapSetCenter = vi.fn()
const mockMarkerConstructor = vi.fn()
const mockMarkerAddListener = vi.fn()
const mockMarkerSetPosition = vi.fn()
const mockMarkerSetMap = vi.fn()
const mockAutocompleteConstructor = vi.fn()
const mockAutocompleteAddListener = vi.fn()
let mockAutocompletePlace: Record<string, unknown> | null = null
let mockAutocompletePlaceChanged: (() => void) | null = null

const installGoogleMapsMocks = () => {
  Object.defineProperty(window, 'google', {
    configurable: true,
    value: {
      maps: {
        SymbolPath: { CIRCLE: 'CIRCLE' },
        Map: class {
          constructor(...args: unknown[]) {
            mockMapConstructor(...args)
          }
          addListener(...args: unknown[]) {
            mockMapAddListener(...args)
          }
          setCenter(...args: unknown[]) {
            mockMapSetCenter(...args)
          }
        },
        Marker: class {
          constructor(...args: unknown[]) {
            mockMarkerConstructor(...args)
          }
          addListener(...args: unknown[]) {
            mockMarkerAddListener(...args)
          }
          setPosition(...args: unknown[]) {
            mockMarkerSetPosition(...args)
          }
          setMap(...args: unknown[]) {
            mockMarkerSetMap(...args)
          }
          getPosition() {
            return { lat: () => 1.3, lng: () => 103.85 }
          }
        },
        places: {
          Autocomplete: class {
            constructor(...args: unknown[]) {
              mockAutocompleteConstructor(...args)
            }
            addListener(eventName: string, callback: () => void) {
              mockAutocompleteAddListener(eventName, callback)
              if (eventName === 'place_changed') {
                mockAutocompletePlaceChanged = callback
              }
            }
            getPlace() {
              return mockAutocompletePlace ?? {}
            }
          },
        },
      },
    },
  })
}

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

function renderHookHarness(
  isDeveloperMode: boolean,
  options: { googleMapsApiKey?: string } = {},
) {
  const ref: { current: UseUnifiedCaptureReturn | null } = { current: null }

  function Harness() {
    ref.current = useUnifiedCapture({ isDeveloperMode, ...options })
    return (
      <>
        <input ref={ref.current.addressInputRef} aria-label="Address" />
        <div ref={ref.current.mapContainerRef} />
      </>
    )
  }

  render(<Harness />)
  if (!ref.current) {
    throw new Error('Hook harness did not produce a value')
  }
  return ref
}

describe('useUnifiedCapture', () => {
  afterEach(() => {
    cleanup()
    vi.useRealTimers()
    vi.resetAllMocks()
    mockAutocompletePlace = null
    mockAutocompletePlaceChanged = null
    sessionStorage.clear()
    document.body.classList.remove('capture-results-active')
    delete (window as { google?: unknown }).google
  })

  it('sets a map error when the Google Maps API key is missing', async () => {
    const hookRef = renderHookHarness(true, { googleMapsApiKey: '' })

    await act(async () => {
      // allow effects to run
    })

    expect(hookRef.current!.mapError).toBe(
      'Google Maps API key not configured. Set VITE_GOOGLE_MAPS_API_KEY in your .env file.',
    )
  })

  it('initializes a map when a Google Maps API key is provided', async () => {
    installGoogleMapsMocks()
    renderHookHarness(true, { googleMapsApiKey: 'test-key' })

    await act(async () => {
      // allow effects to run
    })

    expect(mockMapConstructor).toHaveBeenCalled()
    expect(mockMarkerConstructor).toHaveBeenCalled()
  })

  it('auto-geocodes address changes and updates coordinates', async () => {
    vi.useFakeTimers()
    mockForwardGeocodeAddress.mockResolvedValue({
      latitude: 1.2345,
      longitude: 103.9876,
      formattedAddress: '123 Main St, Singapore',
      source: {
        provider: 'onemap_address_search',
        state: 'live',
        configured: true,
        synthetic: false,
      },
    })

    const hookRef = renderHookHarness(true, { googleMapsApiKey: '' })

    await act(async () => {
      hookRef.current!.setAddress('123 Main St')
    })

    await act(async () => {
      vi.advanceTimersByTime(800)
    })

    expect(mockForwardGeocodeAddress).toHaveBeenCalledWith('123 Main St', {
      jurisdictionCode: 'SG',
    })
    expect(hookRef.current!.latitude).toBe('1.234500')
    expect(hookRef.current!.longitude).toBe('103.987600')
    expect(hookRef.current!.analysisLatitude).toBe('1.234500')
    expect(hookRef.current!.analysisLongitude).toBe('103.987600')
    expect(hookRef.current!.coordinateSourceLabel).toBe(
      'OneMap address search (Singapore)',
    )
  })

  it('labels interpolated Singapore coordinates separately from exact OneMap hits', async () => {
    vi.useFakeTimers()
    mockForwardGeocodeAddress.mockResolvedValue({
      latitude: 1.3291483,
      longitude: 103.6982319,
      formattedAddress: '25 SOON LEE ROAD SINGAPORE',
      source: {
        provider: 'onemap_street_interpolation',
        state: 'live',
        configured: true,
        synthetic: true,
        reason: 'Exact address was not returned by OneMap',
      },
    })

    const hookRef = renderHookHarness(true, { googleMapsApiKey: '' })

    await act(async () => {
      hookRef.current!.setAddress('25 Soon Lee Rd')
    })
    await act(async () => {
      vi.advanceTimersByTime(800)
    })

    expect(hookRef.current!.analysisLatitude).toBe('1.329148')
    expect(hookRef.current!.analysisLongitude).toBe('103.698232')
    expect(hookRef.current!.coordinateSourceLabel).toBe(
      'Approximate OneMap street interpolation (Singapore)',
    )
  })

  it('surfaces an error when address auto-geocoding fails', async () => {
    vi.useFakeTimers()
    mockForwardGeocodeAddress.mockRejectedValue(new Error('Geocode down'))
    const hookRef = renderHookHarness(true, { googleMapsApiKey: '' })

    await act(async () => {
      hookRef.current!.setAddress('123 Main St')
    })

    await act(async () => {
      vi.advanceTimersByTime(800)
    })

    expect(hookRef.current!.geocodeError).toBe('Geocode down')
  })

  it('clears stale analysis coordinates when Singapore geocoding fails', async () => {
    vi.useFakeTimers()
    mockForwardGeocodeAddress
      .mockResolvedValueOnce({
        latitude: 1.2345,
        longitude: 103.9876,
        formattedAddress: '123 MAIN ST SINGAPORE 123456',
        source: {
          provider: 'onemap_address_search',
          state: 'live',
          configured: true,
          synthetic: false,
        },
      })
      .mockRejectedValueOnce(
        new Error(
          'OneMap token request failed (400): Invalid OneMap credentials',
        ),
      )

    const hookRef = renderHookHarness(true, { googleMapsApiKey: '' })

    await act(async () => {
      hookRef.current!.setAddress('123 Main St Singapore')
    })
    await act(async () => {
      vi.advanceTimersByTime(800)
      await Promise.resolve()
    })

    expect(hookRef.current!.analysisLatitude).toBe('1.234500')
    expect(hookRef.current!.analysisLongitude).toBe('103.987600')

    await act(async () => {
      hookRef.current!.setAddress('10 Marina Boulevard singapore')
    })
    await act(async () => {
      vi.advanceTimersByTime(800)
      await Promise.resolve()
    })

    expect(hookRef.current!.geocodeError).toBe(
      'OneMap token request failed (400): Invalid OneMap credentials',
    )
    expect(hookRef.current!.latitude).toBe('')
    expect(hookRef.current!.longitude).toBe('')
    expect(hookRef.current!.analysisLatitude).toBe('')
    expect(hookRef.current!.analysisLongitude).toBe('')
    expect(hookRef.current!.coordinateSourceLabel).toBeNull()
    expect(hookRef.current!.mapCoordinateSourceLabel).toBeNull()
  })

  it('uses the backend geocoding failure as the scan error', async () => {
    vi.useFakeTimers()
    mockForwardGeocodeAddress.mockRejectedValue(
      new Error('ONEMAP_ACCESS_TOKEN not configured'),
    )
    const hookRef = renderHookHarness(true, { googleMapsApiKey: '' })

    await act(async () => {
      hookRef.current!.setAddress('1 Nassim Rd')
    })

    await act(async () => {
      const event = {
        preventDefault: vi.fn(),
      } as unknown as React.FormEvent<HTMLFormElement>
      const promise = hookRef.current!.handleCapture(event)
      await Promise.resolve()
      await vi.runAllTimersAsync()
      await promise
    })

    expect(hookRef.current!.captureError).toBe(
      'ONEMAP_ACCESS_TOKEN not configured',
    )
    expect(mockCapturePropertyForDevelopment).not.toHaveBeenCalled()
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

    const hookRef = renderHookHarness(true, { googleMapsApiKey: '' })

    await act(async () => {
      hookRef.current!.setLatitude('1.2345')
      hookRef.current!.setLongitude('103.9876')
      hookRef.current!.setCurrentGfaSqm('16,500')
      hookRef.current!.setCurrentGfaSource('approved plans')
    })

    await act(async () => {
      const event = {
        preventDefault: vi.fn(),
      } as unknown as React.FormEvent<HTMLFormElement>
      const promise = hookRef.current!.handleCapture(event)
      await Promise.resolve()
      await vi.runAllTimersAsync()
      await promise
    })

    expect(mockCapturePropertyForDevelopment).toHaveBeenCalledWith(
      expect.objectContaining({
        latitude: 1.2345,
        longitude: 103.9876,
        jurisdictionCode: undefined,
        previewDetailLevel: 'medium',
        currentGfaSqm: 16500,
        currentGfaSource: 'approved plans',
      }),
      expect.any(AbortSignal),
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
    expect(document.body).toHaveClass('capture-results-active')
  })

  it('uses the submitted address for target-acquired confirmation', async () => {
    vi.useFakeTimers()
    vi.setSystemTime(new Date('2026-01-06T10:00:00.000Z'))

    mockForwardGeocodeAddress.mockResolvedValue({
      latitude: 1.331096,
      longitude: 103.6977849,
      formattedAddress: '25 Soon Lee Rd, Singapore 628083',
    })
    mockCapturePropertyForDevelopment.mockResolvedValue({
      propertyId: 'prop-soon-lee',
      currencySymbol: 'S$',
      address: { fullAddress: '20 Soon Lee Rd, Singapore', district: 'Jurong' },
      quickAnalysis: { generatedAt: '2026-01-06T09:58:00Z', scenarios: [] },
      previewJob: null,
    })

    const hookRef = renderHookHarness(true, { googleMapsApiKey: '' })

    await act(async () => {
      hookRef.current!.setAddress('25 Soon Lee Rd, Singapore 628083')
    })

    await act(async () => {
      const event = {
        preventDefault: vi.fn(),
      } as unknown as React.FormEvent<HTMLFormElement>
      const promise = hookRef.current!.handleCapture(event)
      await Promise.resolve()
      await vi.runAllTimersAsync()
      await promise
    })

    expect(hookRef.current!.targetAcquired).toBe(
      '25 Soon Lee Rd, Singapore 628083',
    )
    expect(hookRef.current!.capturedSites[0]?.address).toBe(
      '25 Soon Lee Rd, Singapore 628083',
    )
    expect(hookRef.current!.siteAcquisitionResult?.address.fullAddress).toBe(
      '20 Soon Lee Rd, Singapore',
    )
    expect(mockCapturePropertyForDevelopment).toHaveBeenCalledWith(
      expect.objectContaining({
        submittedAddress: '25 Soon Lee Rd, Singapore 628083',
      }),
      expect.any(AbortSignal),
    )
  })

  it('blocks developer capture when geocoding changes the street number', async () => {
    vi.useFakeTimers()
    mockForwardGeocodeAddress.mockResolvedValue({
      latitude: 1.3286413,
      longitude: 103.698443,
      formattedAddress: '20 Soon Lee Rd, Singapore 628086',
    })

    const hookRef = renderHookHarness(true, { googleMapsApiKey: '' })

    await act(async () => {
      hookRef.current!.setAddress('25 Soon Lee Rd, Singapore 628083')
    })

    await act(async () => {
      const event = {
        preventDefault: vi.fn(),
      } as unknown as React.FormEvent<HTMLFormElement>
      const promise = hookRef.current!.handleCapture(event)
      await Promise.resolve()
      await vi.runAllTimersAsync()
      await promise
    })

    expect(mockCapturePropertyForDevelopment).not.toHaveBeenCalled()
    expect(hookRef.current!.captureError).toContain(
      'Geocoding resolved "25 Soon Lee Rd, Singapore 628083" to "20 Soon Lee Rd, Singapore 628086"',
    )
  })

  it('blocks developer capture when a prior auto-geocode changed the street number', async () => {
    vi.useFakeTimers()
    mockForwardGeocodeAddress.mockResolvedValue({
      latitude: 1.3286413,
      longitude: 103.698443,
      formattedAddress: '20 Soon Lee Rd, Singapore 628086',
    })

    const hookRef = renderHookHarness(true, { googleMapsApiKey: '' })

    await act(async () => {
      hookRef.current!.setAddress('25 Soon Lee Rd, Singapore 628083')
    })

    await act(async () => {
      vi.advanceTimersByTime(800)
      await Promise.resolve()
    })

    expect(hookRef.current!.latitude).toBe('1.328641')
    expect(hookRef.current!.longitude).toBe('103.698443')
    expect(hookRef.current!.analysisLatitude).toBe('1.328641')
    expect(hookRef.current!.analysisLongitude).toBe('103.698443')

    await act(async () => {
      const event = {
        preventDefault: vi.fn(),
      } as unknown as React.FormEvent<HTMLFormElement>
      const promise = hookRef.current!.handleCapture(event)
      await Promise.resolve()
      await vi.runAllTimersAsync()
      await promise
    })

    expect(mockCapturePropertyForDevelopment).not.toHaveBeenCalled()
    expect(hookRef.current!.captureError).toContain(
      'Geocoding resolved "25 Soon Lee Rd, Singapore 628083" to "20 Soon Lee Rd, Singapore 628086"',
    )
  })

  it('re-resolves partial Singapore addresses before capture even after auto-geocode', async () => {
    vi.useFakeTimers()
    mockForwardGeocodeAddress.mockResolvedValue({
      latitude: 1.3282813,
      longitude: 103.6984406,
      formattedAddress: '20 Soon Lee Rd, Singapore 628086',
      source: {
        provider: 'onemap_address_search',
        state: 'live',
        configured: true,
        synthetic: false,
      },
    })

    const hookRef = renderHookHarness(true, { googleMapsApiKey: '' })

    await act(async () => {
      hookRef.current!.setAddress('25 Soon Lee Rd')
    })

    await act(async () => {
      vi.advanceTimersByTime(800)
      await Promise.resolve()
    })

    await act(async () => {
      const event = {
        preventDefault: vi.fn(),
      } as unknown as React.FormEvent<HTMLFormElement>
      const promise = hookRef.current!.handleCapture(event)
      await Promise.resolve()
      await vi.runAllTimersAsync()
      await promise
    })

    expect(mockForwardGeocodeAddress).toHaveBeenCalledTimes(2)
    expect(mockForwardGeocodeAddress).toHaveBeenLastCalledWith(
      '25 Soon Lee Rd',
      { jurisdictionCode: 'SG' },
    )
    expect(mockCapturePropertyForDevelopment).not.toHaveBeenCalled()
    expect(hookRef.current!.captureError).toContain(
      'Geocoding resolved "25 Soon Lee Rd" to "20 Soon Lee Rd, Singapore 628086"',
    )
  })

  it('re-resolves Singapore Google Places selections through backend geocoding before capture', async () => {
    vi.useFakeTimers()
    vi.setSystemTime(new Date('2026-01-06T10:00:00.000Z'))
    installGoogleMapsMocks()

    mockForwardGeocodeAddress.mockResolvedValue({
      latitude: 1.3071,
      longitude: 103.8259,
      formattedAddress: '1 NASSIM ROAD SINGAPORE 258458',
      source: {
        provider: 'onemap_address_search',
        state: 'live',
        configured: true,
        synthetic: false,
      },
    })
    mockCapturePropertyForDevelopment.mockResolvedValue({
      propertyId: 'prop-nassim',
      currencySymbol: 'S$',
      address: { fullAddress: '1 NASSIM ROAD SINGAPORE 258458' },
      quickAnalysis: { generatedAt: '2026-01-06T09:58:00Z', scenarios: [] },
      previewJob: null,
    })

    const hookRef = renderHookHarness(true, { googleMapsApiKey: 'test-key' })

    await act(async () => {
      await Promise.resolve()
      await Promise.resolve()
    })
    expect(mockAutocompleteConstructor).toHaveBeenCalled()

    mockAutocompletePlace = {
      formatted_address: '1 Nassim Rd, Singapore 258458',
      place_id: 'google-place-1',
      name: '1 Nassim Road',
      types: ['street_address'],
      geometry: {
        location: {
          lat: () => 1.3065566,
          lng: () => 103.8262787,
        },
      },
    }

    await act(async () => {
      mockAutocompletePlaceChanged?.()
    })

    expect(hookRef.current!.latitude).toBe('1.306557')
    expect(hookRef.current!.longitude).toBe('103.826279')
    expect(hookRef.current!.analysisLatitude).toBe('')
    expect(hookRef.current!.analysisLongitude).toBe('')
    expect(hookRef.current!.coordinateSourceLabel).toBe(null)
    expect(hookRef.current!.mapCoordinateSourceLabel).toBe(
      'Google Places autocomplete',
    )

    await act(async () => {
      const event = {
        preventDefault: vi.fn(),
      } as unknown as React.FormEvent<HTMLFormElement>
      const promise = hookRef.current!.handleCapture(event)
      await Promise.resolve()
      await vi.runAllTimersAsync()
      await promise
    })

    expect(mockForwardGeocodeAddress).toHaveBeenCalledWith(
      '1 Nassim Rd, Singapore 258458',
      { jurisdictionCode: 'SG' },
    )
    expect(mockCapturePropertyForDevelopment).toHaveBeenCalledWith(
      expect.objectContaining({
        latitude: 1.3071,
        longitude: 103.8259,
        submittedAddress: '1 Nassim Rd, Singapore 258458',
        placeId: 'google-place-1',
        placeName: '1 Nassim Road',
        placeTypes: ['street_address'],
      }),
      expect.any(AbortSignal),
    )
    expect(hookRef.current!.coordinateSourceLabel).toBe(
      'OneMap address search (Singapore)',
    )
    expect(hookRef.current!.analysisLatitude).toBe('1.307100')
    expect(hookRef.current!.analysisLongitude).toBe('103.825900')
  })

  it('omits developmentScenarios when no scenarios are selected (developer flow)', async () => {
    vi.useFakeTimers()
    vi.setSystemTime(new Date('2026-01-06T10:00:00.000Z'))

    mockCapturePropertyForDevelopment.mockResolvedValue({
      propertyId: 'prop-555',
      currencySymbol: 'S$',
      address: { fullAddress: '1 Cyber Ave', district: 'Downtown' },
      quickAnalysis: { generatedAt: '2026-01-06T09:58:00Z', scenarios: [] },
      previewJob: null,
    })

    const hookRef = renderHookHarness(true, { googleMapsApiKey: '' })

    expect(hookRef.current!.selectedScenarios.length).toBe(0)

    await act(async () => {
      const event = {
        preventDefault: vi.fn(),
      } as unknown as React.FormEvent<HTMLFormElement>
      const promise = hookRef.current!.handleCapture(event)
      await Promise.resolve()
      await vi.runAllTimersAsync()
      await promise
    })

    expect(mockCapturePropertyForDevelopment).toHaveBeenCalledWith(
      expect.objectContaining({
        developmentScenarios: [],
      }),
      expect.any(AbortSignal),
    )
  })

  it('resets state and clears persisted capture when starting a new capture', async () => {
    const hookRef = renderHookHarness(true, { googleMapsApiKey: '' })

    sessionStorage.setItem(
      'site-acquisition:captured-property',
      JSON.stringify({ propertyId: 'prop-123' }),
    )

    await act(async () => {
      hookRef.current!.setLatitude('1.1111')
      hookRef.current!.setLongitude('103.2222')
      hookRef.current!.setAddress('Some address')
      hookRef.current!.setCurrentGfaSqm('12000')
      hookRef.current!.setCurrentGfaSource('source memo')
    })

    await act(async () => {
      hookRef.current!.handleNewCapture()
    })

    expect(hookRef.current!.latitude).toBe('')
    expect(hookRef.current!.longitude).toBe('')
    expect(hookRef.current!.analysisLatitude).toBe('')
    expect(hookRef.current!.analysisLongitude).toBe('')
    expect(hookRef.current!.address).toBe('')
    expect(hookRef.current!.currentGfaSqm).toBe('')
    expect(hookRef.current!.currentGfaSource).toBe('')
    expect(
      sessionStorage.getItem('site-acquisition:captured-property'),
    ).toBeNull()
    expect(document.body).not.toHaveClass('capture-results-active')
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
    mockForwardGeocodeAddress.mockResolvedValue({
      latitude: 1.1111,
      longitude: 103.2222,
    })
    mockFetchPropertyMarketIntelligence.mockResolvedValue({ summary: 'ok' })

    const hookRef = renderHookHarness(false, { googleMapsApiKey: '' })

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
      await Promise.resolve()
      await vi.runAllTimersAsync()
      await promise
    })

    expect(mockLogPropertyByGpsWithFeatures).toHaveBeenCalledWith(
      expect.objectContaining({
        latitude: 1.1111,
        longitude: 103.2222,
        jurisdictionCode: undefined,
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
    const hookRef = renderHookHarness(true, { googleMapsApiKey: '' })

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
