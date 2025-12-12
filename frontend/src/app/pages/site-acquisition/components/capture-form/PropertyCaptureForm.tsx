/**
 * Property Capture Form Component
 *
 * Renders the property capture form with:
 * - Jurisdiction dropdown
 * - Address input with geocoding buttons
 * - Latitude/longitude inputs
 * - Interactive map for location selection
 * - Development scenario selection
 * - Capture button with loading state
 * - Error and success messages
 */

import type React from 'react'
import { useState, useMemo } from 'react'
import type {
  DevelopmentScenario,
  SiteAcquisitionResult,
} from '../../../../../api/siteAcquisition'
import { SCENARIO_OPTIONS, JURISDICTION_OPTIONS } from '../../constants'
import { VoiceNoteRecorder } from './VoiceNoteRecorder'
import { VoiceNoteList } from './VoiceNoteList'
import {
  PropertyLocationMap,
  type HeritageFeature,
  type NearbyAmenity,
} from '../map'

// ============================================================================
// Types
// ============================================================================

export interface PropertyCaptureFormProps {
  // Form state
  jurisdictionCode: string
  setJurisdictionCode: (code: string) => void
  address: string
  setAddress: (address: string) => void
  latitude: string
  setLatitude: (lat: string) => void
  longitude: string
  setLongitude: (lon: string) => void
  selectedScenarios: DevelopmentScenario[]
  isCapturing: boolean
  error: string | null
  geocodeError: string | null
  capturedProperty: SiteAcquisitionResult | null

  // Handlers
  onCapture: (e: React.FormEvent) => void
  onForwardGeocode: () => void
  onReverseGeocode: () => void
  onToggleScenario: (scenario: DevelopmentScenario) => void
  /** Optional callback when coordinates change from map interaction */
  onCoordinatesChange?: (lat: string, lon: string) => void
}

// ============================================================================
// Component
// ============================================================================

export function PropertyCaptureForm({
  jurisdictionCode,
  setJurisdictionCode,
  address,
  setAddress,
  latitude,
  setLatitude,
  longitude,
  setLongitude,
  selectedScenarios,
  isCapturing,
  error,
  geocodeError,
  capturedProperty,
  onCapture,
  onForwardGeocode,
  onReverseGeocode,
  onToggleScenario,
  onCoordinatesChange,
}: PropertyCaptureFormProps) {
  // Track when a new voice note is uploaded to refresh the list
  const [voiceNoteRefreshTrigger, setVoiceNoteRefreshTrigger] = useState(0)

  const handleVoiceNoteUploaded = () => {
    setVoiceNoteRefreshTrigger((prev) => prev + 1)
  }

  // Handle coordinate changes from map - update form fields and call parent callback
  const handleMapCoordinatesChange = (lat: string, lon: string) => {
    setLatitude(lat)
    setLongitude(lon)
    onCoordinatesChange?.(lat, lon)
  }

  // Transform nearby amenities for the map component (now includes coordinates)
  const mapAmenities = useMemo(() => {
    if (!capturedProperty?.nearbyAmenities) return undefined

    const amenities = capturedProperty.nearbyAmenities
    const hasCoordinates = (item: { latitude?: number; longitude?: number }) =>
      typeof item.latitude === 'number' && typeof item.longitude === 'number'

    return {
      mrtStations: amenities.mrtStations
        ?.filter(hasCoordinates)
        .map((station) => ({
          name: station.name,
          type: 'mrt' as const,
          latitude: station.latitude!,
          longitude: station.longitude!,
          distance_m: station.distanceM ?? undefined,
        })) as NearbyAmenity[] | undefined,
      busStops: amenities.busStops?.filter(hasCoordinates).map((stop) => ({
        name: stop.name,
        type: 'bus' as const,
        latitude: stop.latitude!,
        longitude: stop.longitude!,
        distance_m: stop.distanceM ?? undefined,
      })) as NearbyAmenity[] | undefined,
      schools: amenities.schools?.filter(hasCoordinates).map((school) => ({
        name: school.name,
        type: 'school' as const,
        latitude: school.latitude!,
        longitude: school.longitude!,
        distance_m: school.distanceM ?? undefined,
      })) as NearbyAmenity[] | undefined,
      malls: amenities.shoppingMalls?.filter(hasCoordinates).map((mall) => ({
        name: mall.name,
        type: 'mall' as const,
        latitude: mall.latitude!,
        longitude: mall.longitude!,
        distance_m: mall.distanceM ?? undefined,
      })) as NearbyAmenity[] | undefined,
      parks: amenities.parks?.filter(hasCoordinates).map((park) => ({
        name: park.name,
        type: 'park' as const,
        latitude: park.latitude!,
        longitude: park.longitude!,
        distance_m: park.distanceM ?? undefined,
      })) as NearbyAmenity[] | undefined,
    }
  }, [capturedProperty?.nearbyAmenities])

  // Check if any amenities have coordinates
  const hasAmenityCoordinates = useMemo(() => {
    if (!mapAmenities) return false
    return Object.values(mapAmenities).some((arr) => arr && arr.length > 0)
  }, [mapAmenities])

  // Transform heritage context for the map (if heritage overlay data available)
  const heritageFeatures = useMemo((): HeritageFeature[] | undefined => {
    if (!capturedProperty?.heritageContext?.flag) return undefined
    const heritage = capturedProperty.heritageContext
    // If we have heritage context, create a marker at the property location
    if (heritage.overlay?.name) {
      return [
        {
          name: heritage.overlay.name,
          status: heritage.risk ?? undefined,
          risk_level:
            heritage.risk === 'high'
              ? 'high'
              : heritage.risk === 'low'
                ? 'low'
                : 'medium',
          latitude: parseFloat(latitude) || 1.3,
          longitude: parseFloat(longitude) || 103.85,
        },
      ]
    }
    return undefined
  }, [capturedProperty?.heritageContext, latitude, longitude])

  return (
    <section
      style={{
        background: 'white',
        border: '1px solid #d2d2d7',
        borderRadius: '4px',
        padding: '2rem',
        marginBottom: '2rem',
      }}
    >
      <h2
        style={{
          fontSize: '1.5rem',
          fontWeight: 600,
          marginBottom: '1.5rem',
          letterSpacing: '-0.01em',
        }}
      >
        Property Coordinates
      </h2>

      <form onSubmit={onCapture}>
        {/* Jurisdiction Dropdown */}
        <div style={{ marginBottom: '1.5rem' }}>
          <label
            htmlFor="jurisdiction"
            style={{
              display: 'block',
              fontSize: '0.9375rem',
              fontWeight: 500,
              marginBottom: '0.5rem',
              color: '#1d1d1f',
            }}
          >
            Jurisdiction
          </label>
          <select
            id="jurisdiction"
            value={jurisdictionCode}
            onChange={(e) => {
              const newCode = e.target.value
              setJurisdictionCode(newCode)
              const jurisdiction = JURISDICTION_OPTIONS.find(
                (j) => j.code === newCode,
              )
              if (jurisdiction) {
                setLatitude(jurisdiction.defaultLat)
                setLongitude(jurisdiction.defaultLon)
              }
            }}
            style={{
              width: '100%',
              padding: '0.875rem 1rem',
              fontSize: '1rem',
              border: '1px solid #d2d2d7',
              borderRadius: '6px',
              outline: 'none',
              background: 'white',
              cursor: 'pointer',
              transition: 'all 0.2s ease',
            }}
          >
            {JURISDICTION_OPTIONS.map((j) => (
              <option key={j.code} value={j.code}>
                {j.label} ({j.code})
              </option>
            ))}
          </select>
        </div>

        {/* Address Input with Geocoding */}
        <div style={{ marginBottom: '1.5rem' }}>
          <label
            htmlFor="address"
            style={{
              display: 'block',
              fontSize: '0.9375rem',
              fontWeight: 500,
              marginBottom: '0.5rem',
              color: '#1d1d1f',
            }}
          >
            Address
          </label>
          <div style={{ display: 'flex', gap: '0.5rem' }}>
            <input
              id="address"
              type="text"
              value={address}
              onChange={(e) => setAddress(e.target.value)}
              placeholder="Enter address to geocode..."
              style={{
                flex: 1,
                padding: '0.875rem 1rem',
                fontSize: '1rem',
                border: '1px solid #d2d2d7',
                borderRadius: '6px',
                outline: 'none',
                transition: 'all 0.2s ease',
              }}
              onFocus={(e) => {
                e.currentTarget.style.borderColor = '#1d1d1f'
                e.currentTarget.style.boxShadow =
                  '0 0 0 4px rgba(0, 0, 0, 0.04)'
              }}
              onBlur={(e) => {
                e.currentTarget.style.borderColor = '#d2d2d7'
                e.currentTarget.style.boxShadow = 'none'
              }}
            />
            <button
              type="button"
              onClick={onForwardGeocode}
              title="Geocode address to coordinates"
              style={{
                padding: '0.875rem 1rem',
                fontSize: '0.875rem',
                fontWeight: 500,
                background: '#f5f5f7',
                border: '1px solid #d2d2d7',
                borderRadius: '6px',
                cursor: 'pointer',
                transition: 'all 0.2s ease',
                whiteSpace: 'nowrap',
              }}
            >
              → Coords
            </button>
            <button
              type="button"
              onClick={onReverseGeocode}
              title="Reverse geocode coordinates to address"
              style={{
                padding: '0.875rem 1rem',
                fontSize: '0.875rem',
                fontWeight: 500,
                background: '#f5f5f7',
                border: '1px solid #d2d2d7',
                borderRadius: '6px',
                cursor: 'pointer',
                transition: 'all 0.2s ease',
                whiteSpace: 'nowrap',
              }}
            >
              ← Address
            </button>
          </div>
          {geocodeError && (
            <p
              style={{
                marginTop: '0.5rem',
                fontSize: '0.875rem',
                color: '#dc2626',
              }}
            >
              {geocodeError}
            </p>
          )}
        </div>

        {/* Latitude/Longitude Inputs */}
        <div
          style={{
            display: 'grid',
            gridTemplateColumns: 'repeat(2, 1fr)',
            gap: '1rem',
            marginBottom: '2rem',
          }}
        >
          <div>
            <label
              htmlFor="latitude"
              style={{
                display: 'block',
                fontSize: '0.9375rem',
                fontWeight: 500,
                marginBottom: '0.5rem',
                color: '#1d1d1f',
              }}
            >
              Latitude
            </label>
            <input
              id="latitude"
              type="text"
              value={latitude}
              onChange={(e) => setLatitude(e.target.value)}
              style={{
                width: '100%',
                padding: '0.875rem 1rem',
                fontSize: '1rem',
                border: '1px solid #d2d2d7',
                borderRadius: '6px',
                outline: 'none',
                fontFamily:
                  'ui-monospace, SFMono-Regular, Menlo, Monaco, monospace',
                transition: 'all 0.2s ease',
              }}
              onFocus={(e) => {
                e.currentTarget.style.borderColor = '#1d1d1f'
                e.currentTarget.style.boxShadow =
                  '0 0 0 4px rgba(0, 0, 0, 0.04)'
              }}
              onBlur={(e) => {
                e.currentTarget.style.borderColor = '#d2d2d7'
                e.currentTarget.style.boxShadow = 'none'
              }}
            />
          </div>

          <div>
            <label
              htmlFor="longitude"
              style={{
                display: 'block',
                fontSize: '0.9375rem',
                fontWeight: 500,
                marginBottom: '0.5rem',
                color: '#1d1d1f',
              }}
            >
              Longitude
            </label>
            <input
              id="longitude"
              type="text"
              value={longitude}
              onChange={(e) => setLongitude(e.target.value)}
              style={{
                width: '100%',
                padding: '0.875rem 1rem',
                fontSize: '1rem',
                border: '1px solid #d2d2d7',
                borderRadius: '6px',
                outline: 'none',
                fontFamily:
                  'ui-monospace, SFMono-Regular, Menlo, Monaco, monospace',
                transition: 'all 0.2s ease',
              }}
              onFocus={(e) => {
                e.currentTarget.style.borderColor = '#1d1d1f'
                e.currentTarget.style.boxShadow =
                  '0 0 0 4px rgba(0, 0, 0, 0.04)'
              }}
              onBlur={(e) => {
                e.currentTarget.style.borderColor = '#d2d2d7'
                e.currentTarget.style.boxShadow = 'none'
              }}
            />
          </div>
        </div>

        {/* Interactive Map */}
        <div style={{ marginBottom: '2rem' }}>
          <h3
            style={{
              fontSize: '1.125rem',
              fontWeight: 600,
              marginBottom: '1rem',
              letterSpacing: '-0.01em',
            }}
          >
            Location Map
          </h3>
          <PropertyLocationMap
            latitude={latitude}
            longitude={longitude}
            onCoordinatesChange={handleMapCoordinatesChange}
            address={capturedProperty?.address?.fullAddress}
            district={capturedProperty?.address?.district}
            zoningCode={capturedProperty?.uraZoning?.zoneCode ?? undefined}
            nearbyAmenities={mapAmenities}
            heritageFeatures={heritageFeatures}
            interactive={!isCapturing}
            height={350}
            showAmenities={hasAmenityCoordinates}
            showHeritage={!!capturedProperty?.heritageContext?.flag}
          />
        </div>

        {/* Development Scenarios */}
        <h3
          style={{
            fontSize: '1.125rem',
            fontWeight: 600,
            marginBottom: '1rem',
            letterSpacing: '-0.01em',
          }}
        >
          Development Scenarios
        </h3>

        <div
          style={{
            display: 'grid',
            gridTemplateColumns: 'repeat(auto-fit, minmax(280px, 1fr))',
            gap: '1rem',
            marginBottom: '2rem',
          }}
        >
          {SCENARIO_OPTIONS.map((scenario) => {
            const isSelected = selectedScenarios.includes(scenario.value)
            return (
              <button
                key={scenario.value}
                type="button"
                onClick={() => onToggleScenario(scenario.value)}
                style={{
                  background: isSelected ? '#f5f5f7' : 'white',
                  border: `1px solid ${isSelected ? '#1d1d1f' : '#d2d2d7'}`,
                  borderRadius: '4px',
                  padding: '1.25rem',
                  cursor: 'pointer',
                  textAlign: 'left',
                  transition: 'all 0.2s ease',
                  position: 'relative',
                }}
                onMouseEnter={(e) => {
                  e.currentTarget.style.transform = 'translateY(-2px)'
                  e.currentTarget.style.boxShadow =
                    '0 8px 16px rgba(0, 0, 0, 0.08)'
                }}
                onMouseLeave={(e) => {
                  e.currentTarget.style.transform = 'translateY(0)'
                  e.currentTarget.style.boxShadow = 'none'
                }}
              >
                {isSelected && (
                  <div
                    style={{
                      position: 'absolute',
                      top: '1rem',
                      right: '1rem',
                      width: '20px',
                      height: '20px',
                      borderRadius: '50%',
                      background: '#1d1d1f',
                      display: 'flex',
                      alignItems: 'center',
                      justifyContent: 'center',
                      fontSize: '12px',
                      color: 'white',
                    }}
                  >
                    ✓
                  </div>
                )}
                <div
                  style={{
                    display: 'flex',
                    alignItems: 'center',
                    gap: '0.75rem',
                    marginBottom: '0.5rem',
                  }}
                >
                  <span style={{ fontSize: '1.5rem' }}>{scenario.icon}</span>
                  <div
                    style={{
                      fontSize: '1.0625rem',
                      fontWeight: 600,
                      color: '#1d1d1f',
                      letterSpacing: '-0.005em',
                    }}
                  >
                    {scenario.label}
                  </div>
                </div>
                <div
                  style={{
                    fontSize: '0.875rem',
                    color: '#6e6e73',
                    lineHeight: 1.4,
                    letterSpacing: '-0.005em',
                  }}
                >
                  {scenario.description}
                </div>
              </button>
            )
          })}
        </div>

        {/* Submit Button */}
        <button
          type="submit"
          disabled={isCapturing || selectedScenarios.length === 0}
          style={{
            width: '100%',
            padding: '0.875rem 2rem',
            fontSize: '1.0625rem',
            fontWeight: 500,
            color: 'white',
            background:
              isCapturing || selectedScenarios.length === 0
                ? '#d2d2d7'
                : '#1d1d1f',
            border: 'none',
            borderRadius: '6px',
            cursor:
              isCapturing || selectedScenarios.length === 0
                ? 'not-allowed'
                : 'pointer',
            transition: 'all 0.2s ease',
            letterSpacing: '-0.005em',
          }}
          onMouseEnter={(e) => {
            if (!isCapturing && selectedScenarios.length > 0) {
              e.currentTarget.style.background = '#424245'
            }
          }}
          onMouseLeave={(e) => {
            if (!isCapturing && selectedScenarios.length > 0) {
              e.currentTarget.style.background = '#1d1d1f'
            }
          }}
        >
          {isCapturing ? 'Capturing Property...' : 'Capture Property'}
        </button>

        {/* Error Message */}
        {error && (
          <div
            style={{
              marginTop: '1rem',
              padding: '1rem',
              background: '#fff5f5',
              border: '1px solid #fed7d7',
              borderRadius: '4px',
              color: '#c53030',
              fontSize: '0.9375rem',
            }}
          >
            {error}
          </div>
        )}

        {/* Success Message */}
        {capturedProperty && (
          <div
            style={{
              marginTop: '1rem',
              padding: '1rem',
              background: '#f0fdf4',
              border: '1px solid #bbf7d0',
              borderRadius: '4px',
              color: '#15803d',
              fontSize: '0.9375rem',
            }}
          >
            <strong>Property captured successfully</strong>
            <div style={{ marginTop: '0.5rem', fontSize: '0.875rem' }}>
              {capturedProperty.address.fullAddress} •{' '}
              {capturedProperty.address.district}
            </div>
          </div>
        )}
      </form>

      {/* Voice Note Recorder */}
      <VoiceNoteRecorder
        propertyId={capturedProperty?.propertyId ?? null}
        latitude={latitude ? parseFloat(latitude) : undefined}
        longitude={longitude ? parseFloat(longitude) : undefined}
        disabled={isCapturing}
        onUploadComplete={handleVoiceNoteUploaded}
      />

      {/* Previously Saved Voice Notes */}
      <VoiceNoteList
        propertyId={capturedProperty?.propertyId ?? null}
        refreshTrigger={voiceNoteRefreshTrigger}
      />
    </section>
  )
}
