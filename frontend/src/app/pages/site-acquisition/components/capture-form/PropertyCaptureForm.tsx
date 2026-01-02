/**
 * Property Capture Form Component
 *
 * Renders the property capture form with:
 * - Address input (auto-geocodes to coordinates on blur)
 * - Latitude/longitude inputs
 * - Interactive map for location selection
 * - Development scenario selection
 * - Capture button with loading state
 * - Error and success messages
 */

import type React from 'react'
import { useMemo } from 'react'

import type {
  DevelopmentScenario,
  SiteAcquisitionResult,
} from '../../../../../api/siteAcquisition'
import { Button } from '../../../../../components/canonical/Button'
import { SCENARIO_OPTIONS } from '../../constants'
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
  address: string
  setAddress: (address: string) => void
  latitude: string
  setLatitude: (lat: string) => void
  longitude: string
  setLongitude: (lon: string) => void
  selectedScenarios: DevelopmentScenario[]
  isCapturing: boolean
  /** Whether address is being geocoded to coordinates */
  isGeocoding?: boolean
  error: string | null
  capturedProperty: SiteAcquisitionResult | null

  // Handlers
  onCapture: (e: React.FormEvent) => void
  onToggleScenario: (scenario: DevelopmentScenario) => void
  /** Optional callback when coordinates change from map interaction */
  onCoordinatesChange?: (lat: string, lon: string) => void
  /** Optional callback when address field loses focus (for auto-geocoding) */
  onAddressBlur?: () => void
  /** Optional callback for saving draft (work in progress) */
  onSaveDraft?: () => void
  /** Whether draft is being saved */
  isSavingDraft?: boolean
}

// ============================================================================
// Component
// ============================================================================

export function PropertyCaptureForm({
  address,
  setAddress,
  latitude,
  setLatitude,
  longitude,
  setLongitude,
  selectedScenarios,
  isCapturing,
  isGeocoding,
  error,
  capturedProperty,
  onCapture,
  onToggleScenario,
  onCoordinatesChange,
  onAddressBlur,
  onSaveDraft,
  isSavingDraft,
}: PropertyCaptureFormProps) {
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

  // Determine if form can be submitted
  const canSubmit = selectedScenarios.length > 0 && !isCapturing
  const canSaveDraft = !!onSaveDraft && !isSavingDraft && !isCapturing

  return (
    <section className="property-capture-form">
      {/* Action buttons (header text is provided by AppShell) */}
      <div className="property-capture-form__header">
        <div className="property-capture-form__header-actions">
          {onSaveDraft && (
            <Button
              variant="secondary"
              size="sm"
              onClick={onSaveDraft}
              disabled={!canSaveDraft}
            >
              {isSavingDraft ? 'Saving…' : 'Save Draft'}
            </Button>
          )}
          <Button
            variant="primary"
            size="sm"
            onClick={(e) => {
              e.preventDefault()
              onCapture(e as unknown as React.FormEvent)
            }}
            disabled={!canSubmit}
          >
            {isCapturing ? 'Capturing…' : 'Capture Property'}
          </Button>
        </div>
      </div>

      {/* Form content - seamless glass surface */}
      <div className="ob-seamless-panel ob-seamless-panel--glass property-capture-form__surface">
        <form onSubmit={onCapture}>
          {/* Location inputs - Address and Coordinates on one row */}
          <div className="property-capture-form__location-row">
            <input
              id="address"
              type="text"
              value={address}
              onChange={(e) => setAddress(e.target.value)}
              placeholder="Address"
              className="property-capture-form__address-input"
              onBlur={() => onAddressBlur?.()}
            />
            <input
              id="latitude"
              type="text"
              value={latitude}
              onChange={(e) => setLatitude(e.target.value)}
              placeholder={isGeocoding ? 'Loading...' : 'Latitude'}
              disabled={isGeocoding}
              className={`property-capture-form__coord-input ${isGeocoding ? 'property-capture-form__coord-input--loading' : ''}`}
            />
            <input
              id="longitude"
              type="text"
              value={longitude}
              onChange={(e) => setLongitude(e.target.value)}
              placeholder={isGeocoding ? 'Loading...' : 'Longitude'}
              disabled={isGeocoding}
              className={`property-capture-form__coord-input ${isGeocoding ? 'property-capture-form__coord-input--loading' : ''}`}
            />
          </div>

          {/* Interactive Map */}
          <div className="property-capture-form__map-section">
            <h3 className="property-capture-form__map-section-title">
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
          <h3 className="property-capture-form__scenarios-title">
            Development Scenarios
          </h3>

          <div className="property-capture-form__scenarios-grid">
            {SCENARIO_OPTIONS.map((scenario) => {
              const isSelected = selectedScenarios.includes(scenario.value)
              return (
                <button
                  key={scenario.value}
                  type="button"
                  onClick={() => onToggleScenario(scenario.value)}
                  className={`property-capture-form__scenario-card ${isSelected ? 'property-capture-form__scenario-card--selected' : ''}`}
                >
                  {isSelected && (
                    <div className="property-capture-form__scenario-check">
                      ✓
                    </div>
                  )}
                  <div className="property-capture-form__scenario-header">
                    <span className="property-capture-form__scenario-icon">
                      {scenario.icon}
                    </span>
                    <div className="property-capture-form__scenario-name">
                      {scenario.label}
                    </div>
                  </div>
                  <div className="property-capture-form__scenario-desc">
                    {scenario.description}
                  </div>
                </button>
              )
            })}
          </div>

          {/* Error Message */}
          {error && (
            <div className="property-capture-form__error-message">{error}</div>
          )}

          {/* Success Message */}
          {capturedProperty && (
            <div className="property-capture-form__success-message">
              <strong>Property captured successfully</strong>
              <div className="property-capture-form__success-detail">
                {capturedProperty.address.fullAddress} •{' '}
                {capturedProperty.address.district}
              </div>
            </div>
          )}
        </form>
      </div>
    </section>
  )
}
