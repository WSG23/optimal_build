/**
 * useUnifiedCapture - Combined capture logic for unified capture page
 *
 * Handles both Agent and Developer capture flows:
 * - Agent: Uses logPropertyByGpsWithFeatures API
 * - Developer: Uses capturePropertyForDevelopment API
 *
 * Returns unified state and handlers for the capture form.
 */

import { useState, useCallback, useRef, useEffect } from 'react'
import type { FormEvent } from 'react'

import { importLibrary, setOptions } from '@googlemaps/js-api-loader'

import {
  fetchPropertyMarketIntelligence,
  logPropertyByGpsWithFeatures,
  type DevelopmentScenario,
  type GpsCaptureSummaryWithFeatures,
  type DeveloperFeatureData,
  type MarketIntelligenceSummary,
} from '../../../../api/agents'
import { capturePropertyForDevelopment } from '../../../../api/siteAcquisition'
import type { SiteAcquisitionResult } from '../../../../api/siteAcquisition'
import {
  forwardGeocodeAddress,
  reverseGeocodeCoords,
} from '../../../../api/geocoding'
import type { ExternalSourceMetadata } from '../../../../api/externalSources'
import { loadCaptureForProject } from '../utils/captureStorage'

const GOOGLE_MAPS_API_KEY = import.meta.env?.VITE_GOOGLE_MAPS_API_KEY ?? ''
const CAPTURE_RESULTS_ACTIVE_CLASS = 'capture-results-active'

function leadingStreetNumber(value: string): string | null {
  const match = value.trim().match(/^(\d+[a-zA-Z]?)(?=\s)/)
  return match?.[1]?.toLowerCase() ?? null
}

function looksLikeSingaporeAddress(value: string): boolean {
  const trimmed = value.trim()
  return /\bsingapore\b/i.test(trimmed) || /\b\d{6}\b/.test(trimmed)
}

function formatCoordinate(value: number): string {
  return Number.isFinite(value) ? value.toFixed(6) : ''
}

function hasConflictingResolvedStreetNumber(
  submittedAddress: string,
  resolvedAddress: string | null | undefined,
): boolean {
  if (!resolvedAddress) {
    return false
  }
  const submittedNumber = leadingStreetNumber(submittedAddress)
  const resolvedNumber = leadingStreetNumber(resolvedAddress)
  return Boolean(
    submittedNumber && resolvedNumber && submittedNumber !== resolvedNumber,
  )
}

// @googlemaps/js-api-loader v2: functional API. setOptions() is idempotent
// per page; importLibrary() resolves with the requested library and
// transparently deduplicates concurrent calls.
let optionsApplied = false

async function loadGoogleMaps(apiKey: string): Promise<void> {
  if (!optionsApplied) {
    setOptions({ key: apiKey, v: 'weekly' })
    optionsApplied = true
  }
  // Load required libraries in parallel; results are attached to
  // `window.google.maps.*` for downstream code that references the globals.
  await Promise.all([
    importLibrary('maps'),
    importLibrary('marker'),
    importLibrary('places'),
  ])
}

function dismissPlacesAutocompleteDropdown() {
  addressInputBlur()
  document.body.classList.add(CAPTURE_RESULTS_ACTIVE_CLASS)
}

function addressInputBlur() {
  const activeElement = document.activeElement
  if (activeElement instanceof HTMLInputElement) {
    activeElement.blur()
  }
}

/** Attempt browser geolocation with a timeout. Returns null on failure. */
function getUserPosition(
  timeoutMs = 8000,
): Promise<{ latitude: number; longitude: number } | null> {
  return new Promise((resolve) => {
    if (!navigator.geolocation) {
      resolve(null)
      return
    }
    navigator.geolocation.getCurrentPosition(
      (pos) =>
        resolve({
          latitude: pos.coords.latitude,
          longitude: pos.coords.longitude,
        }),
      () => resolve(null),
      { enableHighAccuracy: false, timeout: timeoutMs, maximumAge: 300_000 },
    )
  })
}

export interface CapturedSite {
  propertyId: string
  address: string
  district?: string
  scenario: DevelopmentScenario | null
  capturedAt: string
}

interface SelectedPlaceMetadata {
  formattedAddress: string
  placeId: string | null
  placeName: string | null
  placeTypes: string[]
}

function coordinateSourceLabelFor(
  source: ExternalSourceMetadata | null | undefined,
  fallbackLabel: string | null = null,
): string | null {
  if (!source) {
    return fallbackLabel
  }

  if (source.state === 'mock') {
    return 'Mock geocoder'
  }
  if (source.state === 'unavailable') {
    return fallbackLabel ?? 'Coordinate source unavailable'
  }

  switch (source.provider) {
    case 'onemap_address_search':
      return 'OneMap address search (Singapore)'
    case 'onemap_street_interpolation':
      return 'Approximate OneMap street interpolation (Singapore)'
    case 'google_maps':
      return fallbackLabel ?? 'Google geocoding'
    default:
      return source.provider
        .split('_')
        .filter(Boolean)
        .map((part) => part.charAt(0).toUpperCase() + part.slice(1))
        .join(' ')
  }
}

export interface UseUnifiedCaptureOptions {
  isDeveloperMode: boolean
  projectId?: string | null
  googleMapsApiKey?: string
}

export interface UseUnifiedCaptureReturn {
  // Form state
  latitude: string
  longitude: string
  analysisLatitude: string
  analysisLongitude: string
  address: string
  currentGfaSqm: string
  currentGfaSource: string
  selectedScenarios: DevelopmentScenario[]

  // Setters
  setLatitude: (value: string) => void
  setLongitude: (value: string) => void
  setAddress: (value: string) => void
  setCurrentGfaSqm: (value: string) => void
  setCurrentGfaSource: (value: string) => void
  handleScenarioToggle: (scenario: DevelopmentScenario) => void

  // Capture state
  isCapturing: boolean
  isScanning: boolean
  captureError: string | null
  hasResults: boolean

  // Agent results
  captureSummary: GpsCaptureSummaryWithFeatures | null
  developerFeatures: DeveloperFeatureData | null
  marketSummary: MarketIntelligenceSummary | null
  marketLoading: boolean
  capturedSites: CapturedSite[]

  // Developer results
  siteAcquisitionResult: SiteAcquisitionResult | null

  // Geocoding
  geocodeError: string | null
  isGeocoding: boolean
  coordinateSourceLabel: string | null
  mapCoordinateSourceLabel: string | null

  // Map
  mapContainerRef: React.RefObject<HTMLDivElement>
  /**
   * Legacy address input ref (kept for tests / label associations). The
   * Places API (New) PlaceAutocompleteElement renders its own input into
   * `autocompleteHostRef` instead — that's the visible address field.
   */
  addressInputRef: React.RefObject<HTMLInputElement>
  /** Host element for the <gmp-place-autocomplete> web component. */
  autocompleteHostRef: React.RefObject<HTMLDivElement>
  mapError: string | null
  isMapLoading: boolean

  // Post-capture confirmation
  targetAcquired: string | null

  // Handlers
  handleCapture: (event: FormEvent<HTMLFormElement>) => Promise<void>
  handleNewCapture: () => void
  handleCancelCapture: () => void
}

export function useUnifiedCapture({
  isDeveloperMode,
  projectId,
  googleMapsApiKey,
}: UseUnifiedCaptureOptions): UseUnifiedCaptureReturn {
  // Form state — latitude/longitude is the map preview position; analysis
  // coordinates are backend-resolved and are the only coordinates used for
  // zoning lookup once available.
  const [latitude, setLatitude] = useState<string>('')
  const [longitude, setLongitude] = useState<string>('')
  const [analysisLatitude, setAnalysisLatitude] = useState<string>('')
  const [analysisLongitude, setAnalysisLongitude] = useState<string>('')
  const [address, setAddressState] = useState<string>('')
  const [currentGfaSqm, setCurrentGfaSqm] = useState<string>('')
  const [currentGfaSource, setCurrentGfaSource] = useState<string>('')
  const [jurisdictionCode, setJurisdictionCode] = useState<string>('')
  const [selectedScenarios, setSelectedScenarios] = useState<
    DevelopmentScenario[]
  >([])

  // Capture state
  const [isCapturing, setIsCapturing] = useState(false)
  const [isScanning, setIsScanning] = useState(false)
  const [captureError, setCaptureError] = useState<string | null>(null)
  const [targetAcquired, setTargetAcquired] = useState<string | null>(null)
  const abortControllerRef = useRef<AbortController | null>(null)

  // Agent results
  const [captureSummary, setCaptureSummary] =
    useState<GpsCaptureSummaryWithFeatures | null>(null)
  const [developerFeatures, setDeveloperFeatures] =
    useState<DeveloperFeatureData | null>(null)
  const [marketSummary, setMarketSummary] =
    useState<MarketIntelligenceSummary | null>(null)
  const [marketLoading, setMarketLoading] = useState(false)
  const [capturedSites, setCapturedSites] = useState<CapturedSite[]>(() => {
    try {
      const stored = sessionStorage.getItem('capture:mission-log')
      return stored ? (JSON.parse(stored) as CapturedSite[]) : []
    } catch {
      return []
    }
  })

  // Developer results
  const [siteAcquisitionResult, setSiteAcquisitionResult] =
    useState<SiteAcquisitionResult | null>(null)

  // Geocoding
  const [geocodeError, setGeocodeError] = useState<string | null>(null)
  const [isGeocoding, setIsGeocoding] = useState(false)
  const [coordinateSourceLabel, setCoordinateSourceLabel] = useState<
    string | null
  >(null)
  const [mapCoordinateSourceLabel, setMapCoordinateSourceLabel] = useState<
    string | null
  >(null)
  // Track the address that was last geocoded to avoid redundant calls
  const lastGeocodedAddressRef = useRef<string>('')
  const lastResolvedGeocodeAddressRef = useRef<string>('')
  const lastGeocodeErrorRef = useRef<string | null>(null)
  const selectedPlaceMetadataRef = useRef<SelectedPlaceMetadata | null>(null)

  const clearAnalysisCoordinates = useCallback(() => {
    setAnalysisLatitude('')
    setAnalysisLongitude('')
    setCoordinateSourceLabel(null)
  }, [])

  const clearAddressResolvedCoordinates = useCallback(() => {
    clearAnalysisCoordinates()
    if (mapCoordinateSourceLabel !== 'Browser location') {
      setLatitude('')
      setLongitude('')
      setMapCoordinateSourceLabel(null)
    }
  }, [clearAnalysisCoordinates, mapCoordinateSourceLabel])

  const setAddress = useCallback(
    (value: string) => {
      setAddressState(value)
      setCaptureError(null)
      setGeocodeError(null)
      lastGeocodeErrorRef.current = null
      if (value.trim() !== lastGeocodedAddressRef.current) {
        clearAddressResolvedCoordinates()
      }
    },
    [clearAddressResolvedCoordinates],
  )

  // Map
  const [mapError, setMapError] = useState<string | null>(null)
  const [isMapLoaded, setIsMapLoaded] = useState(false)
  const [isMapLoading, setIsMapLoading] = useState(true)
  const mapContainerRef = useRef<HTMLDivElement | null>(null)
  const mapInstanceRef = useRef<google.maps.Map | null>(null)
  const mapMarkerRef = useRef<google.maps.marker.AdvancedMarkerElement | null>(
    null,
  )
  const hasHydratedRef = useRef(false)
  const geolocatedRef = useRef(false)
  const addressInputRef = useRef<HTMLInputElement | null>(null)
  // PlaceAutocompleteElement renders its own input element; we host it in a
  // wrapper div so consumers can still pass an HTMLInputElement ref for
  // backward-compatible API (used by tests and label-for associations).
  const autocompleteHostRef = useRef<HTMLDivElement | null>(null)
  const autocompleteElementRef =
    useRef<google.maps.places.PlaceAutocompleteElement | null>(null)

  /** Update AdvancedMarkerElement position. */
  const updateMarkerPosition = useCallback((lat: number, lng: number) => {
    const m = mapMarkerRef.current
    if (!m) return
    m.position = { lat, lng }
  }, [])

  useEffect(() => {
    hasHydratedRef.current = false
  }, [projectId])

  // Persist Mission Log to sessionStorage
  useEffect(() => {
    if (capturedSites.length > 0) {
      sessionStorage.setItem(
        'capture:mission-log',
        JSON.stringify(capturedSites),
      )
    }
  }, [capturedSites])

  // Browser geolocation — run once on mount to center map on user's position
  useEffect(() => {
    if (geolocatedRef.current) return
    geolocatedRef.current = true

    getUserPosition().then((pos) => {
      if (!pos) return
      // Only set if user hasn't already typed something
      setLatitude((prev) => (prev === '' ? pos.latitude.toFixed(6) : prev))
      setLongitude((prev) => (prev === '' ? pos.longitude.toFixed(6) : prev))
      setMapCoordinateSourceLabel((prev) => prev ?? 'Browser location')

      // Center map if already initialized
      if (mapInstanceRef.current) {
        mapInstanceRef.current.setCenter({
          lat: pos.latitude,
          lng: pos.longitude,
        })
        updateMarkerPosition(pos.latitude, pos.longitude)
      }
    })
  }, [updateMarkerPosition])

  // Scenario toggle handler
  const handleScenarioToggle = useCallback((scenario: DevelopmentScenario) => {
    setSelectedScenarios((prev) => {
      if (prev.includes(scenario)) {
        return prev.filter((item) => item !== scenario)
      }
      return [...prev, scenario]
    })
  }, [])

  // Forward geocode (address → coordinates)
  // Returns the coordinates if geocoding succeeded, null otherwise
  const handleForwardGeocode = useCallback(
    async (
      addressToGeocode?: string,
    ): Promise<{
      latitude: number
      longitude: number
      formattedAddress: string
    } | null> => {
      const targetAddress = addressToGeocode ?? address
      if (!targetAddress.trim()) {
        const message = 'Please enter an address to geocode.'
        lastGeocodeErrorRef.current = message
        setGeocodeError(message)
        return null
      }
      try {
        lastGeocodeErrorRef.current = null
        setGeocodeError(null)
        setIsGeocoding(true)
        const result = await forwardGeocodeAddress(targetAddress.trim(), {
          jurisdictionCode: jurisdictionCode || 'SG',
        })
        const sourceLabel = coordinateSourceLabelFor(
          result.source,
          'Backend geocoder',
        )
        setLatitude(formatCoordinate(result.latitude))
        setLongitude(formatCoordinate(result.longitude))
        setMapCoordinateSourceLabel(sourceLabel)
        setAnalysisLatitude(formatCoordinate(result.latitude))
        setAnalysisLongitude(formatCoordinate(result.longitude))
        setCoordinateSourceLabel(sourceLabel)
        lastGeocodedAddressRef.current = targetAddress.trim()
        lastResolvedGeocodeAddressRef.current = result.formattedAddress
        selectedPlaceMetadataRef.current = null

        if (mapInstanceRef.current) {
          mapInstanceRef.current.setCenter({
            lat: result.latitude,
            lng: result.longitude,
          })
          updateMarkerPosition(result.latitude, result.longitude)
        }
        return {
          latitude: result.latitude,
          longitude: result.longitude,
          formattedAddress: result.formattedAddress,
        }
      } catch (error) {
        console.error('Forward geocode failed', error)
        const message =
          error instanceof Error ? error.message : 'Unable to geocode address.'
        lastGeocodeErrorRef.current = message
        setGeocodeError(message)
        if (
          jurisdictionCode.toUpperCase() === 'SG' ||
          looksLikeSingaporeAddress(targetAddress)
        ) {
          clearAddressResolvedCoordinates()
        }
        return null
      } finally {
        setIsGeocoding(false)
      }
    },
    [
      address,
      clearAddressResolvedCoordinates,
      jurisdictionCode,
      updateMarkerPosition,
    ],
  )

  // Auto-geocode when address changes (debounced)
  // This provides Google Maps-like behavior where typing an address
  // automatically updates the map location
  useEffect(() => {
    const trimmedAddress = address.trim()

    // Skip if address is empty or hasn't changed from last geocoded address
    if (!trimmedAddress || trimmedAddress === lastGeocodedAddressRef.current) {
      return
    }

    // Debounce: wait 800ms after user stops typing before geocoding
    const timeoutId = setTimeout(() => {
      // Only auto-geocode if the address looks complete (has at least a few characters)
      if (trimmedAddress.length >= 5) {
        handleForwardGeocode(trimmedAddress)
      }
    }, 800)

    return () => clearTimeout(timeoutId)
  }, [address, handleForwardGeocode])

  // Load Google Maps script
  useEffect(() => {
    const apiKey = googleMapsApiKey ?? GOOGLE_MAPS_API_KEY
    if (!apiKey) {
      setMapError(
        'Google Maps API key not configured. Set VITE_GOOGLE_MAPS_API_KEY in your .env file.',
      )
      setIsMapLoading(false)
      return
    }

    setIsMapLoading(true)
    loadGoogleMaps(apiKey)
      .then(() => {
        setIsMapLoaded(true)
        setIsMapLoading(false)
      })
      .catch((err: Error) => {
        setMapError(
          `Map failed to load: ${err.message}. Check your API key and network connection.`,
        )
        setIsMapLoading(false)
      })
  }, [googleMapsApiKey])

  useEffect(() => {
    if (!isDeveloperMode) {
      return
    }
    if (hasHydratedRef.current) {
      return
    }
    let storedResult: SiteAcquisitionResult | null = null
    if (projectId) {
      storedResult = loadCaptureForProject(projectId)
    }
    if (!storedResult) {
      const raw = sessionStorage.getItem('site-acquisition:captured-property')
      if (raw) {
        try {
          storedResult = JSON.parse(raw) as SiteAcquisitionResult
        } catch {
          storedResult = null
        }
      }
    }
    if (storedResult) {
      setSiteAcquisitionResult(storedResult)
      setLatitude(formatCoordinate(storedResult.coordinates.latitude))
      setLongitude(formatCoordinate(storedResult.coordinates.longitude))
      setAnalysisLatitude(formatCoordinate(storedResult.coordinates.latitude))
      setAnalysisLongitude(formatCoordinate(storedResult.coordinates.longitude))
      setCoordinateSourceLabel('Saved capture coordinates')
      setMapCoordinateSourceLabel('Saved capture coordinates')
      setJurisdictionCode(storedResult.jurisdictionCode ?? 'SG')
      if (storedResult.address?.fullAddress) {
        setAddressState(storedResult.address.fullAddress)
      }
    }
    hasHydratedRef.current = true
  }, [isDeveloperMode, projectId])

  // Initialize Google Map
  useEffect(() => {
    if (!isMapLoaded || !mapContainerRef.current || mapInstanceRef.current) {
      return
    }

    // Dark grey map style — monochrome, no colorful markers
    const darkGreyMapStyle: google.maps.MapTypeStyle[] = [
      { elementType: 'geometry', stylers: [{ color: '#212121' }] },
      { elementType: 'labels.icon', stylers: [{ visibility: 'off' }] },
      { elementType: 'labels.text.fill', stylers: [{ color: '#757575' }] },
      { elementType: 'labels.text.stroke', stylers: [{ color: '#212121' }] },
      {
        featureType: 'administrative',
        elementType: 'geometry',
        stylers: [{ color: '#757575' }],
      },
      {
        featureType: 'poi',
        elementType: 'geometry',
        stylers: [{ color: '#2a2a2a' }],
      },
      {
        featureType: 'poi',
        elementType: 'labels.text.fill',
        stylers: [{ color: '#616161' }],
      },
      {
        featureType: 'poi.park',
        elementType: 'geometry',
        stylers: [{ color: '#1c3a1c' }],
      },
      {
        featureType: 'road',
        elementType: 'geometry.fill',
        stylers: [{ color: '#2c2c2c' }],
      },
      {
        featureType: 'road',
        elementType: 'labels.text.fill',
        stylers: [{ color: '#8a8a8a' }],
      },
      {
        featureType: 'road.arterial',
        elementType: 'geometry',
        stylers: [{ color: '#373737' }],
      },
      {
        featureType: 'road.highway',
        elementType: 'geometry',
        stylers: [{ color: '#3c3c3c' }],
      },
      {
        featureType: 'road.highway.controlled_access',
        elementType: 'geometry',
        stylers: [{ color: '#4e4e4e' }],
      },
      {
        featureType: 'road.local',
        elementType: 'labels.text.fill',
        stylers: [{ color: '#616161' }],
      },
      {
        featureType: 'transit',
        elementType: 'labels.text.fill',
        stylers: [{ color: '#616161' }],
      },
      {
        featureType: 'transit.line',
        elementType: 'geometry',
        stylers: [{ color: '#2a2a2a' }],
      },
      {
        featureType: 'transit.station',
        elementType: 'labels.icon',
        stylers: [{ visibility: 'off' }],
      },
      {
        featureType: 'water',
        elementType: 'geometry',
        stylers: [{ color: '#181818' }],
      },
      {
        featureType: 'water',
        elementType: 'labels.text.fill',
        stylers: [{ color: '#3d3d3d' }],
      },
    ]

    const initialLat = Number(latitude) || 1.3
    const initialLng = Number(longitude) || 103.85

    const map = new google.maps.Map(mapContainerRef.current, {
      center: { lat: initialLat, lng: initialLng },
      zoom: 16,
      styles: darkGreyMapStyle,
      mapId: 'capture_map',
      mapTypeControl: false,
      streetViewControl: false,
      fullscreenControl: false,
      zoomControl: true,
      clickableIcons: true,
    })

    // Resolve brand color from CSS custom property
    const brandColor =
      getComputedStyle(document.documentElement)
        .getPropertyValue('--ob-color-brand-primary')
        .trim() || '#00f3ff'

    // Create draggable AdvancedMarkerElement (classic Marker deprecated Feb 2024).
    const pinSvg = document.createElement('div')
    pinSvg.innerHTML = `<svg width="24" height="24" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
      <circle cx="12" cy="12" r="10" fill="#ffffff" stroke="${brandColor}" stroke-width="3"/>
    </svg>`
    pinSvg.style.cursor = 'grab'
    pinSvg.title = 'Drag to reposition or click the map'

    const marker = new google.maps.marker.AdvancedMarkerElement({
      position: { lat: initialLat, lng: initialLng },
      map,
      gmpDraggable: true,
      content: pinSvg,
    })

    // Guard against setState after unmount
    let mounted = true

    const setMarkerPosition = (lat: number, lng: number) => {
      marker.position = { lat, lng }
    }

    const handleDragEnd = () => {
      if (!mounted) return
      const position = marker.position
      if (position) {
        const lat =
          typeof position.lat === 'function' ? position.lat() : position.lat
        const lng =
          typeof position.lng === 'function' ? position.lng() : position.lng
        setLatitude(Number(lat).toFixed(6))
        setLongitude(Number(lng).toFixed(6))
        setMapCoordinateSourceLabel('Google Maps pin')
        clearAnalysisCoordinates()
        reverseGeocodeCoords(Number(lat), Number(lng))
          .then((result) => {
            if (mounted && result?.formattedAddress) {
              setMapCoordinateSourceLabel(
                coordinateSourceLabelFor(
                  result.source,
                  'Google Maps reverse geocoding',
                ),
              )
              setAddressState(result.formattedAddress)
              lastGeocodedAddressRef.current = result.formattedAddress
              lastResolvedGeocodeAddressRef.current = result.formattedAddress
            }
          })
          .catch(() => {})
      }
    }

    marker.addEventListener('gmp-dragend', handleDragEnd)

    // Handle map click — set pin and reverse-geocode for address
    map.addListener('click', (event: google.maps.MapMouseEvent) => {
      if (!mounted) return
      if (event.latLng) {
        const lat = event.latLng.lat()
        const lng = event.latLng.lng()
        setLatitude(lat.toFixed(6))
        setLongitude(lng.toFixed(6))
        setMapCoordinateSourceLabel('Google Maps pin')
        clearAnalysisCoordinates()
        setMarkerPosition(lat, lng)
        reverseGeocodeCoords(lat, lng)
          .then((result) => {
            if (mounted && result?.formattedAddress) {
              setMapCoordinateSourceLabel(
                coordinateSourceLabelFor(
                  result.source,
                  'Google Maps reverse geocoding',
                ),
              )
              setAddressState(result.formattedAddress)
              lastGeocodedAddressRef.current = result.formattedAddress
              lastResolvedGeocodeAddressRef.current = result.formattedAddress
            }
          })
          .catch(() => {})
      }
    })

    mapInstanceRef.current = map
    mapMarkerRef.current = marker

    return () => {
      mounted = false
      if (mapMarkerRef.current) {
        mapMarkerRef.current.map = null
      }
    }
    // mapInstanceRef.current guard prevents re-init; coord deps only affect
    // the initial map center on the first run after isMapLoaded flips true.
  }, [isMapLoaded, latitude, longitude, clearAnalysisCoordinates])

  // Initialize Places API (New) PlaceAutocompleteElement.
  // Renders its own <gmp-place-autocomplete> web component into the host div.
  useEffect(() => {
    if (
      !isMapLoaded ||
      !autocompleteHostRef.current ||
      autocompleteElementRef.current ||
      !google.maps.places?.PlaceAutocompleteElement
    ) {
      return
    }

    const autocomplete = new google.maps.places.PlaceAutocompleteElement({
      types: ['address'],
    })
    // Mirror existing state into the autocomplete input on mount.
    if (address) {
      ;(autocomplete as unknown as { value: string }).value = address
    }
    autocompleteHostRef.current.appendChild(autocomplete)

    // Keep `address` state in sync with the user's typing so the
    // debounced backend geocode (separate effect) continues to fire.
    autocomplete.addEventListener('input', (event: Event) => {
      const value =
        (event.target as unknown as { value?: string } | null)?.value ?? ''
      setAddressState(value)
    })

    autocomplete.addEventListener('gmp-select', async (event: Event) => {
      const detail = (
        event as unknown as {
          placePrediction?: { toPlace: () => google.maps.places.Place }
        }
      ).placePrediction
      if (!detail) return
      const place = detail.toPlace()
      await place.fetchFields({
        fields: ['displayName', 'formattedAddress', 'location', 'types', 'id'],
      })

      const formattedAddress = place.formattedAddress ?? null
      if (formattedAddress) {
        setAddressState(formattedAddress)
        lastGeocodedAddressRef.current = formattedAddress
        lastResolvedGeocodeAddressRef.current = formattedAddress
        selectedPlaceMetadataRef.current = {
          formattedAddress,
          placeId: place.id ?? null,
          placeName: place.displayName ?? null,
          placeTypes: place.types ?? [],
        }
      }

      const location = place.location
      if (location) {
        const lat =
          typeof location.lat === 'function' ? location.lat() : location.lat
        const lng =
          typeof location.lng === 'function' ? location.lng() : location.lng
        setLatitude(Number(lat).toFixed(6))
        setLongitude(Number(lng).toFixed(6))
        setMapCoordinateSourceLabel('Google Places autocomplete')
        clearAnalysisCoordinates()
        if (mapInstanceRef.current) {
          mapInstanceRef.current.setCenter({
            lat: Number(lat),
            lng: Number(lng),
          })
          updateMarkerPosition(Number(lat), Number(lng))
        }
      }
    })

    autocompleteElementRef.current = autocomplete
    return () => {
      autocomplete.remove()
      autocompleteElementRef.current = null
    }
    // `address` is read only to seed the initial value on first mount; the
    // input event listener keeps it in sync afterwards.
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [isMapLoaded, clearAnalysisCoordinates, updateMarkerPosition])

  // Capture handler - routes to appropriate API based on mode
  const handleCapture = useCallback(
    async (event: FormEvent<HTMLFormElement>) => {
      event.preventDefault()
      dismissPlacesAutocompleteDropdown()

      try {
        setIsCapturing(true)
        setIsScanning(true)
        setCaptureError(null)
        setTargetAcquired(null)
        setMarketSummary(null)
        setDeveloperFeatures(null)
        setSiteAcquisitionResult(null)

        // Create a shared abort controller for cancellation
        const sharedController = new AbortController()
        abortControllerRef.current = sharedController

        // If address is provided and hasn't been geocoded yet, geocode it first
        // This ensures the coordinates match the entered address
        const trimmedAddress = address.trim()
        let finalLat = Number(analysisLatitude || latitude)
        let finalLon = Number(analysisLongitude || longitude)
        const selectedPlaceMetadata =
          selectedPlaceMetadataRef.current?.formattedAddress === trimmedAddress
            ? selectedPlaceMetadataRef.current
            : null
        const activeJurisdictionCode = jurisdictionCode || 'SG'

        if (
          activeJurisdictionCode.toUpperCase() !== 'SG' &&
          trimmedAddress &&
          trimmedAddress === lastGeocodedAddressRef.current &&
          hasConflictingResolvedStreetNumber(
            trimmedAddress,
            lastResolvedGeocodeAddressRef.current,
          )
        ) {
          setCaptureError(
            `Geocoding resolved "${trimmedAddress}" to "${lastResolvedGeocodeAddressRef.current}". Please confirm the exact map point before running Capture.`,
          )
          setIsCapturing(false)
          setIsScanning(false)
          return
        }

        const shouldResolveThroughBackend =
          trimmedAddress &&
          (trimmedAddress !== lastGeocodedAddressRef.current ||
            activeJurisdictionCode.toUpperCase() === 'SG' ||
            looksLikeSingaporeAddress(trimmedAddress) ||
            mapCoordinateSourceLabel === 'Google Places autocomplete')

        if (shouldResolveThroughBackend) {
          // Address has changed since last geocode - geocode it now
          // Singapore captures must use the backend resolver because it prefers
          // OneMap coordinates for parcel-to-zoning lookup.
          const geocodeResult = await handleForwardGeocode(trimmedAddress)
          if (!geocodeResult) {
            setCaptureError(
              lastGeocodeErrorRef.current ||
                'Unable to geocode the address. Please check the address and try again.',
            )
            setIsCapturing(false)
            setIsScanning(false)
            return
          }
          if (
            hasConflictingResolvedStreetNumber(
              trimmedAddress,
              geocodeResult.formattedAddress,
            )
          ) {
            setCaptureError(
              `Geocoding resolved "${trimmedAddress}" to "${geocodeResult.formattedAddress}". Please confirm the exact map point before running Capture.`,
            )
            setIsCapturing(false)
            setIsScanning(false)
            return
          }
          // Use the newly geocoded coordinates directly from the result
          finalLat = geocodeResult.latitude
          finalLon = geocodeResult.longitude
        }

        if (!Number.isFinite(finalLat) || !Number.isFinite(finalLon)) {
          setCaptureError('Please provide valid coordinates.')
          setIsCapturing(false)
          setIsScanning(false)
          return
        }
        const currentGfaInput = currentGfaSqm.trim()
        const currentGfaEvidence =
          currentGfaInput.length > 0
            ? Number(currentGfaInput.replace(/,/g, ''))
            : null
        if (
          currentGfaEvidence !== null &&
          (!Number.isFinite(currentGfaEvidence) || currentGfaEvidence < 0)
        ) {
          setCaptureError('Please provide a valid existing GFA.')
          setIsCapturing(false)
          setIsScanning(false)
          return
        }

        // Artificial delay for radar scanning effect (cancellable)
        await new Promise<void>((resolve, reject) => {
          const timer = setTimeout(resolve, 1500)
          sharedController.signal.addEventListener('abort', () => {
            clearTimeout(timer)
            reject(new DOMException('Cancelled', 'AbortError'))
          })
        })

        if (isDeveloperMode) {
          // Developer flow - use site acquisition API
          // Add timeout to prevent infinite loading if backend is unresponsive
          let timedOut = false
          const timeoutId = setTimeout(() => {
            timedOut = true
            sharedController.abort()
          }, 30000)

          let result: SiteAcquisitionResult
          try {
            result = await capturePropertyForDevelopment(
              {
                latitude: finalLat,
                longitude: finalLon,
                submittedAddress: trimmedAddress || undefined,
                placeId: selectedPlaceMetadata?.placeId ?? undefined,
                placeName: selectedPlaceMetadata?.placeName ?? undefined,
                placeTypes: selectedPlaceMetadata?.placeTypes ?? [],
                developmentScenarios:
                  selectedScenarios.length > 0 ? selectedScenarios : [],
                jurisdictionCode: jurisdictionCode || undefined,
                previewDetailLevel: 'medium',
                currentGfaSqm: currentGfaEvidence,
                currentGfaSource: currentGfaSource.trim() || undefined,
              },
              sharedController.signal,
            )
          } catch (err) {
            clearTimeout(timeoutId)
            if (err instanceof Error && err.name === 'AbortError') {
              if (timedOut) {
                throw new Error(
                  'Request timed out. Please check if the backend server is running.',
                )
              }
              // User-initiated cancel — re-throw as AbortError for outer catch
              throw err
            }
            throw err
          }
          clearTimeout(timeoutId)

          setSiteAcquisitionResult(result)

          // Store in sessionStorage for persistence
          sessionStorage.setItem(
            'site-acquisition:captured-property',
            JSON.stringify(result),
          )

          const resolvedAddress =
            result.address?.fullAddress ||
            address ||
            `${finalLat.toFixed(5)}, ${finalLon.toFixed(5)}`
          const capturedAddress = trimmedAddress || resolvedAddress

          // Also add to mission log for consistency
          setCapturedSites((prev) => [
            {
              propertyId: result.propertyId,
              address: capturedAddress,
              district: result.address?.district,
              scenario: selectedScenarios[0] ?? null,
              capturedAt: new Date().toISOString(),
            },
            ...prev,
          ])

          // Show "Target Acquired" confirmation briefly
          setTargetAcquired(capturedAddress)
        } else {
          // Agent flow - use GPS capture API
          const summary = await logPropertyByGpsWithFeatures({
            latitude: finalLat,
            longitude: finalLon,
            developmentScenarios:
              selectedScenarios.length > 0 ? selectedScenarios : undefined,
            jurisdictionCode: jurisdictionCode || undefined,
            enabledFeatures: {
              preview3D: false,
              assetOptimization: false,
              financialSummary: false,
              heritageContext: false,
            },
          })

          setCaptureSummary(summary)
          setDeveloperFeatures(summary.developerFeatures)

          const agentAddress = summary.address.fullAddress.startsWith(
            'Mocked Address',
          )
            ? address || `${finalLat.toFixed(5)}, ${finalLon.toFixed(5)}`
            : summary.address.fullAddress

          setCapturedSites((prev) => [
            {
              propertyId: summary.propertyId,
              address: agentAddress,
              district: summary.address.district,
              scenario: summary.quickAnalysis.scenarios[0]?.scenario ?? null,
              capturedAt: summary.timestamp,
            },
            ...prev,
          ])

          // Show "Target Acquired" confirmation briefly
          setTargetAcquired(agentAddress)

          // Fetch market intelligence
          setMarketLoading(true)
          try {
            const intelligence = await fetchPropertyMarketIntelligence(
              summary.propertyId,
            )
            setMarketSummary(intelligence)
          } finally {
            setMarketLoading(false)
          }
        }
      } catch (error) {
        // User-initiated cancel — not an error
        if (error instanceof Error && error.name === 'AbortError') {
          return
        }
        console.error('Capture failed', error)
        setCaptureError(
          error instanceof Error
            ? error.message
            : 'Unable to capture property. Please try again.',
        )
      } finally {
        setIsCapturing(false)
        setIsScanning(false)
        abortControllerRef.current = null
      }
    },
    [
      latitude,
      longitude,
      analysisLatitude,
      analysisLongitude,
      address,
      currentGfaSqm,
      currentGfaSource,
      jurisdictionCode,
      selectedScenarios,
      isDeveloperMode,
      handleForwardGeocode,
      mapCoordinateSourceLabel,
    ],
  )

  // Cancel in-flight capture
  const handleCancelCapture = useCallback(() => {
    abortControllerRef.current?.abort()
    abortControllerRef.current = null
    setIsCapturing(false)
    setIsScanning(false)
  }, [])

  // Auto-dismiss "Target Acquired" after 3 seconds
  useEffect(() => {
    if (!targetAcquired) return
    const timer = setTimeout(() => setTargetAcquired(null), 3000)
    return () => clearTimeout(timer)
  }, [targetAcquired])

  // Reset for new capture
  const handleNewCapture = useCallback(() => {
    document.body.classList.remove(CAPTURE_RESULTS_ACTIVE_CLASS)

    // Clear results
    setCaptureSummary(null)
    setDeveloperFeatures(null)
    setMarketSummary(null)
    setSiteAcquisitionResult(null)
    setCaptureError(null)
    setGeocodeError(null)
    setTargetAcquired(null)
    clearAnalysisCoordinates()
    setMapCoordinateSourceLabel(null)

    // Reset form — clear fields, re-geolocate
    setAddressState('')
    setCurrentGfaSqm('')
    setCurrentGfaSource('')
    setSelectedScenarios([])
    setJurisdictionCode('')

    // Reset geocoding tracking
    lastGeocodedAddressRef.current = ''
    lastResolvedGeocodeAddressRef.current = ''
    selectedPlaceMetadataRef.current = null

    // Clear sessionStorage
    sessionStorage.removeItem('site-acquisition:captured-property')

    // Re-geolocate to user's position
    getUserPosition().then((pos) => {
      if (pos) {
        setLatitude(pos.latitude.toFixed(6))
        setLongitude(pos.longitude.toFixed(6))
        setMapCoordinateSourceLabel('Browser location')
        if (mapInstanceRef.current) {
          mapInstanceRef.current.setCenter({
            lat: pos.latitude,
            lng: pos.longitude,
          })
          updateMarkerPosition(pos.latitude, pos.longitude)
        }
      } else {
        setLatitude('')
        setLongitude('')
        setMapCoordinateSourceLabel(null)
      }
    })
  }, [clearAnalysisCoordinates, updateMarkerPosition])

  // Compute hasResults
  const hasResults = isDeveloperMode
    ? siteAcquisitionResult !== null
    : captureSummary !== null

  useEffect(() => {
    if (isCapturing || hasResults) {
      document.body.classList.add(CAPTURE_RESULTS_ACTIVE_CLASS)
      return
    }
    document.body.classList.remove(CAPTURE_RESULTS_ACTIVE_CLASS)
  }, [hasResults, isCapturing])

  return {
    // Form state
    latitude,
    longitude,
    analysisLatitude,
    analysisLongitude,
    address,
    currentGfaSqm,
    currentGfaSource,
    selectedScenarios,

    // Setters
    setLatitude,
    setLongitude,
    setAddress,
    setCurrentGfaSqm,
    setCurrentGfaSource,
    handleScenarioToggle,

    // Capture state
    isCapturing,
    isScanning,
    captureError,
    hasResults,

    // Agent results
    captureSummary,
    developerFeatures,
    marketSummary,
    marketLoading,
    capturedSites,

    // Developer results
    siteAcquisitionResult,

    // Geocoding
    geocodeError,
    isGeocoding,
    coordinateSourceLabel,
    mapCoordinateSourceLabel,

    // Map
    mapContainerRef,
    addressInputRef,
    autocompleteHostRef,
    mapError,
    isMapLoading,

    // Post-capture confirmation
    targetAcquired,

    // Handlers
    handleCapture,
    handleNewCapture,
    handleCancelCapture,
  }
}
