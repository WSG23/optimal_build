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

import {
  DEFAULT_SCENARIO_ORDER,
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

const GOOGLE_MAPS_API_KEY = import.meta.env?.VITE_GOOGLE_MAPS_API_KEY ?? ''

// Track if Google Maps script is loading/loaded
let googleMapsPromise: Promise<void> | null = null

function loadGoogleMapsScript(): Promise<void> {
  if (window.google?.maps) {
    return Promise.resolve()
  }

  if (googleMapsPromise) {
    return googleMapsPromise
  }

  googleMapsPromise = new Promise((resolve, reject) => {
    const script = document.createElement('script')
    script.src = `https://maps.googleapis.com/maps/api/js?key=${GOOGLE_MAPS_API_KEY}`
    script.async = true
    script.defer = true
    script.onload = () => resolve()
    script.onerror = () => reject(new Error('Failed to load Google Maps'))
    document.head.appendChild(script)
  })

  return googleMapsPromise
}

export interface CapturedSite {
  propertyId: string
  address: string
  district?: string
  scenario: DevelopmentScenario | null
  capturedAt: string
}

export interface UseUnifiedCaptureOptions {
  isDeveloperMode: boolean
}

export interface UseUnifiedCaptureReturn {
  // Form state
  latitude: string
  longitude: string
  address: string
  jurisdictionCode: string
  selectedScenarios: DevelopmentScenario[]

  // Setters
  setLatitude: (value: string) => void
  setLongitude: (value: string) => void
  setAddress: (value: string) => void
  setJurisdictionCode: (value: string) => void
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
  handleForwardGeocode: () => Promise<void>
  handleReverseGeocode: () => Promise<void>

  // Map
  mapContainerRef: React.RefObject<HTMLDivElement>
  mapError: string | null

  // Handlers
  handleCapture: (event: FormEvent<HTMLFormElement>) => Promise<void>
  handleNewCapture: () => void
}

export function useUnifiedCapture({
  isDeveloperMode,
}: UseUnifiedCaptureOptions): UseUnifiedCaptureReturn {
  // Form state
  const [latitude, setLatitude] = useState<string>('1.3000')
  const [longitude, setLongitude] = useState<string>('103.8500')
  const [address, setAddress] = useState<string>('')
  const [jurisdictionCode, setJurisdictionCode] = useState<string>('SG')
  const [selectedScenarios, setSelectedScenarios] = useState<
    DevelopmentScenario[]
  >([...DEFAULT_SCENARIO_ORDER])

  // Capture state
  const [isCapturing, setIsCapturing] = useState(false)
  const [isScanning, setIsScanning] = useState(false)
  const [captureError, setCaptureError] = useState<string | null>(null)

  // Agent results
  const [captureSummary, setCaptureSummary] =
    useState<GpsCaptureSummaryWithFeatures | null>(null)
  const [developerFeatures, setDeveloperFeatures] =
    useState<DeveloperFeatureData | null>(null)
  const [marketSummary, setMarketSummary] =
    useState<MarketIntelligenceSummary | null>(null)
  const [marketLoading, setMarketLoading] = useState(false)
  const [capturedSites, setCapturedSites] = useState<CapturedSite[]>([])

  // Developer results
  const [siteAcquisitionResult, setSiteAcquisitionResult] =
    useState<SiteAcquisitionResult | null>(null)

  // Geocoding
  const [geocodeError, setGeocodeError] = useState<string | null>(null)

  // Map
  const [mapError, setMapError] = useState<string | null>(null)
  const [isMapLoaded, setIsMapLoaded] = useState(false)
  const mapContainerRef = useRef<HTMLDivElement | null>(null)
  const mapInstanceRef = useRef<google.maps.Map | null>(null)
  const mapMarkerRef = useRef<google.maps.Marker | null>(null)

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
  const handleForwardGeocode = useCallback(async () => {
    if (!address.trim()) {
      setGeocodeError('Please enter an address to geocode.')
      return
    }
    try {
      setGeocodeError(null)
      const result = await forwardGeocodeAddress(address.trim())
      setLatitude(result.latitude.toString())
      setLongitude(result.longitude.toString())

      if (mapInstanceRef.current && mapMarkerRef.current) {
        mapInstanceRef.current.setCenter({
          lat: result.latitude,
          lng: result.longitude,
        })
        mapMarkerRef.current.setPosition({
          lat: result.latitude,
          lng: result.longitude,
        })
      }
    } catch (error) {
      console.error('Forward geocode failed', error)
      setGeocodeError(
        error instanceof Error ? error.message : 'Unable to geocode address.',
      )
    }
  }, [address])

  // Reverse geocode (coordinates → address)
  const handleReverseGeocode = useCallback(async () => {
    const parsedLat = Number(latitude)
    const parsedLon = Number(longitude)
    if (!Number.isFinite(parsedLat) || !Number.isFinite(parsedLon)) {
      setGeocodeError(
        'Please provide valid coordinates before reverse geocoding.',
      )
      return
    }
    try {
      setGeocodeError(null)
      const result = await reverseGeocodeCoords(parsedLat, parsedLon)
      setAddress(result.formattedAddress)
    } catch (error) {
      console.error('Reverse geocode failed', error)
      setGeocodeError(
        error instanceof Error ? error.message : 'Unable to reverse geocode.',
      )
    }
  }, [latitude, longitude])

  // Load Google Maps script
  useEffect(() => {
    if (!GOOGLE_MAPS_API_KEY) {
      setMapError('Google Maps API key not set; map preview disabled.')
      return
    }

    loadGoogleMapsScript()
      .then(() => setIsMapLoaded(true))
      .catch((err) => setMapError(err.message))
  }, [])

  // Initialize Google Map
  useEffect(() => {
    if (!isMapLoaded || !mapContainerRef.current || mapInstanceRef.current) {
      return
    }

    // Dark mode map style
    const darkMapStyle: google.maps.MapTypeStyle[] = [
      { elementType: 'geometry', stylers: [{ color: '#242f3e' }] },
      { elementType: 'labels.text.stroke', stylers: [{ color: '#242f3e' }] },
      { elementType: 'labels.text.fill', stylers: [{ color: '#746855' }] },
      {
        featureType: 'administrative.locality',
        elementType: 'labels.text.fill',
        stylers: [{ color: '#d59563' }],
      },
      {
        featureType: 'poi',
        elementType: 'labels.text.fill',
        stylers: [{ color: '#d59563' }],
      },
      {
        featureType: 'poi.park',
        elementType: 'geometry',
        stylers: [{ color: '#263c3f' }],
      },
      {
        featureType: 'road',
        elementType: 'geometry',
        stylers: [{ color: '#38414e' }],
      },
      {
        featureType: 'road',
        elementType: 'labels.text.fill',
        stylers: [{ color: '#9ca5b3' }],
      },
      {
        featureType: 'road.highway',
        elementType: 'geometry',
        stylers: [{ color: '#746855' }],
      },
      {
        featureType: 'water',
        elementType: 'geometry',
        stylers: [{ color: '#17263c' }],
      },
      {
        featureType: 'water',
        elementType: 'labels.text.fill',
        stylers: [{ color: '#515c6d' }],
      },
    ]

    const initialLat = Number(latitude) || 1.3
    const initialLng = Number(longitude) || 103.85

    const map = new google.maps.Map(mapContainerRef.current, {
      center: { lat: initialLat, lng: initialLng },
      zoom: 16,
      tilt: 45, // Add tilt for 3D feel
      styles: darkMapStyle,
      mapTypeControl: false,
      streetViewControl: false,
    })

    // Create draggable marker
    const marker = new google.maps.Marker({
      position: { lat: initialLat, lng: initialLng },
      map,
      draggable: true,
      icon: {
        path: google.maps.SymbolPath.CIRCLE,
        scale: 12,
        fillColor: '#3b82f6',
        fillOpacity: 1,
        strokeColor: 'white',
        strokeWeight: 3,
      },
    })

    // Handle marker drag
    marker.addListener('dragend', () => {
      const position = marker.getPosition()
      if (position) {
        setLatitude(position.lat().toFixed(6))
        setLongitude(position.lng().toFixed(6))
      }
    })

    // Handle map click
    map.addListener('click', (event: google.maps.MapMouseEvent) => {
      if (event.latLng) {
        const lat = event.latLng.lat()
        const lng = event.latLng.lng()
        setLatitude(lat.toFixed(6))
        setLongitude(lng.toFixed(6))
        marker.setPosition({ lat, lng })
      }
    })

    mapInstanceRef.current = map
    mapMarkerRef.current = marker

    return () => {
      if (mapMarkerRef.current) {
        mapMarkerRef.current.setMap(null)
      }
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [isMapLoaded]) // Only run once when map is loaded

  // Capture handler - routes to appropriate API based on mode
  const handleCapture = useCallback(
    async (event: FormEvent<HTMLFormElement>) => {
      event.preventDefault()
      const parsedLat = Number(latitude)
      const parsedLon = Number(longitude)

      if (!Number.isFinite(parsedLat) || !Number.isFinite(parsedLon)) {
        setCaptureError('Please provide valid coordinates.')
        return
      }

      try {
        setIsCapturing(true)
        setIsScanning(true)
        setCaptureError(null)
        setMarketSummary(null)
        setDeveloperFeatures(null)
        setSiteAcquisitionResult(null)

        // Artificial delay for radar scanning effect
        await new Promise((resolve) => setTimeout(resolve, 1500))

        if (isDeveloperMode) {
          // Developer flow - use site acquisition API
          // Add timeout to prevent infinite loading if backend is unresponsive
          const controller = new AbortController()
          const timeoutId = setTimeout(() => controller.abort(), 30000) // 30s timeout

          let result: SiteAcquisitionResult
          try {
            result = await capturePropertyForDevelopment(
              {
                latitude: parsedLat,
                longitude: parsedLon,
                developmentScenarios:
                  selectedScenarios.length > 0 ? selectedScenarios : undefined,
                jurisdictionCode: jurisdictionCode || undefined,
                previewDetailLevel: 'medium',
              },
              controller.signal,
            )
          } catch (err) {
            clearTimeout(timeoutId)
            // Re-throw with more descriptive message for timeout
            if (err instanceof Error && err.name === 'AbortError') {
              throw new Error(
                'Request timed out. Please check if the backend server is running.',
              )
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

          // Also add to mission log for consistency
          setCapturedSites((prev) => [
            {
              propertyId: result.propertyId,
              address:
                result.address?.fullAddress ||
                address ||
                `Captured site (${parsedLat.toFixed(5)}, ${parsedLon.toFixed(5)})`,
              district: result.address?.district,
              scenario: selectedScenarios[0] ?? null,
              capturedAt: new Date().toISOString(),
            },
            ...prev,
          ])
        } else {
          // Agent flow - use GPS capture API
          const summary = await logPropertyByGpsWithFeatures({
            latitude: parsedLat,
            longitude: parsedLon,
            developmentScenarios:
              selectedScenarios.length > 0 ? selectedScenarios : undefined,
            jurisdictionCode: jurisdictionCode || undefined,
            enabledFeatures: {
              preview3D: false,
              assetOptimization: false,
              financialSummary: false,
              heritageContext: false,
              photoDocumentation: false,
            },
          })

          setCaptureSummary(summary)
          setDeveloperFeatures(summary.developerFeatures)

          setCapturedSites((prev) => [
            {
              propertyId: summary.propertyId,
              address: summary.address.fullAddress.startsWith('Mocked Address')
                ? address ||
                  `Captured site (${parsedLat.toFixed(5)}, ${parsedLon.toFixed(5)})`
                : summary.address.fullAddress,
              district: summary.address.district,
              scenario: summary.quickAnalysis.scenarios[0]?.scenario ?? null,
              capturedAt: summary.timestamp,
            },
            ...prev,
          ])

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
        console.error('Capture failed', error)
        setCaptureError(
          error instanceof Error
            ? error.message
            : 'Unable to capture property. Please try again.',
        )
      } finally {
        setIsCapturing(false)
        setIsScanning(false)
      }
    },
    [
      latitude,
      longitude,
      address,
      jurisdictionCode,
      selectedScenarios,
      isDeveloperMode,
    ],
  )

  // Reset for new capture
  const handleNewCapture = useCallback(() => {
    // Clear results
    setCaptureSummary(null)
    setDeveloperFeatures(null)
    setMarketSummary(null)
    setSiteAcquisitionResult(null)
    setCaptureError(null)
    setGeocodeError(null)

    // Reset form to defaults
    setLatitude('1.3000')
    setLongitude('103.8500')
    setAddress('')
    setSelectedScenarios([...DEFAULT_SCENARIO_ORDER])

    // Clear sessionStorage
    sessionStorage.removeItem('site-acquisition:captured-property')

    // Reset map marker to default position
    if (mapInstanceRef.current && mapMarkerRef.current) {
      mapInstanceRef.current.setCenter({ lat: 1.3, lng: 103.85 })
      mapMarkerRef.current.setPosition({ lat: 1.3, lng: 103.85 })
    }
  }, [])

  // Compute hasResults
  const hasResults = isDeveloperMode
    ? siteAcquisitionResult !== null
    : captureSummary !== null

  return {
    // Form state
    latitude,
    longitude,
    address,
    jurisdictionCode,
    selectedScenarios,

    // Setters
    setLatitude,
    setLongitude,
    setAddress,
    setJurisdictionCode,
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
    handleForwardGeocode,
    handleReverseGeocode,

    // Map
    mapContainerRef,
    mapError,

    // Handlers
    handleCapture,
    handleNewCapture,
  }
}
