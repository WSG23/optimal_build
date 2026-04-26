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
import { loadCaptureForProject } from '../utils/captureStorage'

const GOOGLE_MAPS_API_KEY = import.meta.env?.VITE_GOOGLE_MAPS_API_KEY ?? ''

// Track if Google Maps script is loading/loaded
let googleMapsPromise: Promise<void> | null = null

function loadGoogleMapsScript(apiKey: string): Promise<void> {
  if (googleMapsPromise) {
    return googleMapsPromise
  }

  googleMapsPromise = (async () => {
    // Load Maps JS API with marker library via URL params (not loading=async
    // which requires importLibrary and fails in some environments)
    if (!window.google?.maps?.Map) {
      await new Promise<void>((resolve, reject) => {
        const script = document.createElement('script')
        script.src = `https://maps.googleapis.com/maps/api/js?key=${apiKey}&libraries=marker,places`
        script.async = true
        script.defer = true
        script.onload = () => resolve()
        script.onerror = () =>
          reject(
            new Error(
              'Failed to load Google Maps. Check your API key and network connection.',
            ),
          )
        document.head.appendChild(script)
      })
    }
  })()

  return googleMapsPromise
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

export interface UseUnifiedCaptureOptions {
  isDeveloperMode: boolean
  projectId?: string | null
  googleMapsApiKey?: string
}

export interface UseUnifiedCaptureReturn {
  // Form state
  latitude: string
  longitude: string
  address: string
  selectedScenarios: DevelopmentScenario[]

  // Setters
  setLatitude: (value: string) => void
  setLongitude: (value: string) => void
  setAddress: (value: string) => void
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

  // Map
  mapContainerRef: React.RefObject<HTMLDivElement>
  addressInputRef: React.RefObject<HTMLInputElement>
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
  // Form state — start empty; geolocation fills in the user's position
  const [latitude, setLatitude] = useState<string>('')
  const [longitude, setLongitude] = useState<string>('')
  const [address, setAddress] = useState<string>('')
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
  // Track the address that was last geocoded to avoid redundant calls
  const lastGeocodedAddressRef = useRef<string>('')

  // Map
  const [mapError, setMapError] = useState<string | null>(null)
  const [isMapLoaded, setIsMapLoaded] = useState(false)
  const [isMapLoading, setIsMapLoading] = useState(true)
  const mapContainerRef = useRef<HTMLDivElement | null>(null)
  const mapInstanceRef = useRef<google.maps.Map | null>(null)
  const mapMarkerRef = useRef<
    google.maps.marker.AdvancedMarkerElement | google.maps.Marker | null
  >(null)
  const hasHydratedRef = useRef(false)
  const geolocatedRef = useRef(false)
  const addressInputRef = useRef<HTMLInputElement | null>(null)
  const autocompleteRef = useRef<google.maps.places.Autocomplete | null>(null)

  /** Update marker position — handles both AdvancedMarkerElement and classic Marker */
  const updateMarkerPosition = useCallback((lat: number, lng: number) => {
    const m = mapMarkerRef.current
    if (!m) return
    if (m instanceof google.maps.Marker) {
      m.setPosition({ lat, lng })
    } else {
      m.position = { lat, lng }
    }
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
    ): Promise<{ latitude: number; longitude: number } | null> => {
      const targetAddress = addressToGeocode ?? address
      if (!targetAddress.trim()) {
        setGeocodeError('Please enter an address to geocode.')
        return null
      }
      try {
        setGeocodeError(null)
        setIsGeocoding(true)
        const result = await forwardGeocodeAddress(targetAddress.trim())
        setLatitude(result.latitude.toString())
        setLongitude(result.longitude.toString())
        lastGeocodedAddressRef.current = targetAddress.trim()

        if (mapInstanceRef.current) {
          mapInstanceRef.current.setCenter({
            lat: result.latitude,
            lng: result.longitude,
          })
          updateMarkerPosition(result.latitude, result.longitude)
        }
        return { latitude: result.latitude, longitude: result.longitude }
      } catch (error) {
        console.error('Forward geocode failed', error)
        setGeocodeError(
          error instanceof Error ? error.message : 'Unable to geocode address.',
        )
        return null
      } finally {
        setIsGeocoding(false)
      }
    },
    [address, updateMarkerPosition],
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
    loadGoogleMapsScript(apiKey)
      .then(() => {
        setIsMapLoaded(true)
        setIsMapLoading(false)
      })
      .catch((err) => {
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
      setLatitude(storedResult.coordinates.latitude.toString())
      setLongitude(storedResult.coordinates.longitude.toString())
      setJurisdictionCode(storedResult.jurisdictionCode ?? 'SG')
      if (storedResult.address?.fullAddress) {
        setAddress(storedResult.address.fullAddress)
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

    // Create draggable marker — try AdvancedMarkerElement, fall back to classic Marker
    let marker: google.maps.marker.AdvancedMarkerElement | google.maps.Marker

    if (google.maps.marker?.AdvancedMarkerElement) {
      const pinSvg = document.createElement('div')
      pinSvg.innerHTML = `<svg width="24" height="24" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
        <circle cx="12" cy="12" r="10" fill="#ffffff" stroke="${brandColor}" stroke-width="3"/>
      </svg>`
      pinSvg.style.cursor = 'grab'
      pinSvg.title = 'Drag to reposition or click the map'

      marker = new google.maps.marker.AdvancedMarkerElement({
        position: { lat: initialLat, lng: initialLng },
        map,
        gmpDraggable: true,
        content: pinSvg,
      })
    } else {
      // Fallback to classic Marker when AdvancedMarkerElement is unavailable
      marker = new google.maps.Marker({
        position: { lat: initialLat, lng: initialLng },
        map,
        draggable: true,
        icon: {
          path: google.maps.SymbolPath.CIRCLE,
          scale: 10,
          fillColor: '#ffffff',
          fillOpacity: 1,
          strokeColor: brandColor,
          strokeWeight: 3,
        },
      })
    }

    // Guard against setState after unmount
    let mounted = true

    // Helper to update marker position (works for both marker types)
    const setMarkerPosition = (lat: number, lng: number) => {
      if (marker instanceof google.maps.Marker) {
        marker.setPosition({ lat, lng })
      } else {
        marker.position = { lat, lng }
      }
    }

    // Helper to handle drag end for both marker types
    const handleDragEnd = () => {
      if (!mounted) return
      const position =
        marker instanceof google.maps.Marker
          ? marker.getPosition()
          : marker.position
      if (position) {
        const lat =
          typeof position.lat === 'function' ? position.lat() : position.lat
        const lng =
          typeof position.lng === 'function' ? position.lng() : position.lng
        setLatitude(Number(lat).toFixed(6))
        setLongitude(Number(lng).toFixed(6))
        reverseGeocodeCoords(Number(lat), Number(lng))
          .then((result) => {
            if (mounted && result?.formattedAddress) {
              setAddress(result.formattedAddress)
              lastGeocodedAddressRef.current = result.formattedAddress
            }
          })
          .catch(() => {})
      }
    }

    // Bind drag event — different API for each marker type
    if (marker instanceof google.maps.Marker) {
      marker.addListener('dragend', handleDragEnd)
    } else {
      marker.addEventListener('gmp-dragend', handleDragEnd)
    }

    // Handle map click — set pin and reverse-geocode for address
    map.addListener('click', (event: google.maps.MapMouseEvent) => {
      if (!mounted) return
      if (event.latLng) {
        const lat = event.latLng.lat()
        const lng = event.latLng.lng()
        setLatitude(lat.toFixed(6))
        setLongitude(lng.toFixed(6))
        setMarkerPosition(lat, lng)
        reverseGeocodeCoords(lat, lng)
          .then((result) => {
            if (mounted && result?.formattedAddress) {
              setAddress(result.formattedAddress)
              lastGeocodedAddressRef.current = result.formattedAddress
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
        if (mapMarkerRef.current instanceof google.maps.Marker) {
          mapMarkerRef.current.setMap(null)
        } else {
          mapMarkerRef.current.map = null
        }
      }
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [isMapLoaded]) // Only run once when map is loaded

  // Initialize Google Places Autocomplete on address input
  useEffect(() => {
    if (
      !isMapLoaded ||
      !addressInputRef.current ||
      autocompleteRef.current ||
      !google.maps.places
    ) {
      return
    }

    const autocomplete = new google.maps.places.Autocomplete(
      addressInputRef.current,
      {
        types: ['address'],
        fields: ['formatted_address', 'geometry'],
      },
    )

    autocomplete.addListener('place_changed', () => {
      const place = autocomplete.getPlace()
      if (place.formatted_address) {
        setAddress(place.formatted_address)
        lastGeocodedAddressRef.current = place.formatted_address
      }
      if (place.geometry?.location) {
        const lat = place.geometry.location.lat()
        const lng = place.geometry.location.lng()
        setLatitude(lat.toFixed(6))
        setLongitude(lng.toFixed(6))
        if (mapInstanceRef.current) {
          mapInstanceRef.current.setCenter({ lat, lng })
          updateMarkerPosition(lat, lng)
        }
      }
    })

    autocompleteRef.current = autocomplete
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [isMapLoaded]) // Only run once when map + places are loaded

  // Capture handler - routes to appropriate API based on mode
  const handleCapture = useCallback(
    async (event: FormEvent<HTMLFormElement>) => {
      event.preventDefault()

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
        let finalLat = Number(latitude)
        let finalLon = Number(longitude)

        if (
          trimmedAddress &&
          trimmedAddress !== lastGeocodedAddressRef.current
        ) {
          // Address has changed since last geocode - geocode it now
          const geocodeResult = await handleForwardGeocode(trimmedAddress)
          if (!geocodeResult) {
            setCaptureError(
              'Unable to geocode the address. Please check the address and try again.',
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
                developmentScenarios:
                  selectedScenarios.length > 0 ? selectedScenarios : [],
                jurisdictionCode: jurisdictionCode || undefined,
                previewDetailLevel: 'medium',
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

          // Also add to mission log for consistency
          setCapturedSites((prev) => [
            {
              propertyId: result.propertyId,
              address: resolvedAddress,
              district: result.address?.district,
              scenario: selectedScenarios[0] ?? null,
              capturedAt: new Date().toISOString(),
            },
            ...prev,
          ])

          // Show "Target Acquired" confirmation briefly
          setTargetAcquired(resolvedAddress)
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
      address,
      jurisdictionCode,
      selectedScenarios,
      isDeveloperMode,
      handleForwardGeocode,
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
    // Clear results
    setCaptureSummary(null)
    setDeveloperFeatures(null)
    setMarketSummary(null)
    setSiteAcquisitionResult(null)
    setCaptureError(null)
    setGeocodeError(null)
    setTargetAcquired(null)

    // Reset form — clear fields, re-geolocate
    setAddress('')
    setSelectedScenarios([])
    setJurisdictionCode('')

    // Reset geocoding tracking
    lastGeocodedAddressRef.current = ''

    // Clear sessionStorage
    sessionStorage.removeItem('site-acquisition:captured-property')

    // Re-geolocate to user's position
    getUserPosition().then((pos) => {
      if (pos) {
        setLatitude(pos.latitude.toFixed(6))
        setLongitude(pos.longitude.toFixed(6))
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
      }
    })
  }, [updateMarkerPosition])

  // Compute hasResults
  const hasResults = isDeveloperMode
    ? siteAcquisitionResult !== null
    : captureSummary !== null

  return {
    // Form state
    latitude,
    longitude,
    address,
    selectedScenarios,

    // Setters
    setLatitude,
    setLongitude,
    setAddress,
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

    // Map
    mapContainerRef,
    addressInputRef,
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
