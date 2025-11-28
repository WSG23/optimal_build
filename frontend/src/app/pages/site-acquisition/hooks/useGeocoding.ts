/**
 * useGeocoding Hook
 *
 * Manages geocoding state and handlers for converting between
 * addresses and coordinates.
 */

import { useCallback, useState } from 'react'
import { forwardGeocodeAddress, reverseGeocodeCoords } from '../../../../api/geocoding'
import { JURISDICTION_OPTIONS } from '../constants'

// ============================================================================
// Types
// ============================================================================

export interface UseGeocodingOptions {
  initialJurisdiction?: string
  initialLatitude?: string
  initialLongitude?: string
}

export interface UseGeocodingReturn {
  // State
  jurisdictionCode: string
  setJurisdictionCode: (code: string) => void
  address: string
  setAddress: (address: string) => void
  latitude: string
  setLatitude: (lat: string) => void
  longitude: string
  setLongitude: (lon: string) => void
  geocodeError: string | null

  // Handlers
  handleForwardGeocode: () => Promise<void>
  handleReverseGeocode: () => Promise<void>
  handleJurisdictionChange: (newCode: string) => void
}

// ============================================================================
// Hook Implementation
// ============================================================================

export function useGeocoding(options: UseGeocodingOptions = {}): UseGeocodingReturn {
  const {
    initialJurisdiction = 'SG',
    initialLatitude = '1.3000',
    initialLongitude = '103.8500',
  } = options

  const [jurisdictionCode, setJurisdictionCode] = useState(initialJurisdiction)
  const [latitude, setLatitude] = useState(initialLatitude)
  const [longitude, setLongitude] = useState(initialLongitude)
  const [address, setAddress] = useState('')
  const [geocodeError, setGeocodeError] = useState<string | null>(null)

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
    } catch (err) {
      console.error('Forward geocode failed', err)
      setGeocodeError(
        err instanceof Error ? err.message : 'Unable to geocode address.',
      )
    }
  }, [address])

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
    } catch (err) {
      console.error('Reverse geocode failed', err)
      setGeocodeError(
        err instanceof Error ? err.message : 'Unable to reverse geocode.',
      )
    }
  }, [latitude, longitude])

  const handleJurisdictionChange = useCallback((newCode: string) => {
    setJurisdictionCode(newCode)
    const jurisdiction = JURISDICTION_OPTIONS.find((j) => j.code === newCode)
    if (jurisdiction) {
      setLatitude(jurisdiction.defaultLat)
      setLongitude(jurisdiction.defaultLon)
    }
  }, [])

  return {
    jurisdictionCode,
    setJurisdictionCode,
    address,
    setAddress,
    latitude,
    setLatitude,
    longitude,
    setLongitude,
    geocodeError,
    handleForwardGeocode,
    handleReverseGeocode,
    handleJurisdictionChange,
  }
}
