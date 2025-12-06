/**
 * Property Location Map Component
 *
 * Interactive map for site acquisition using Leaflet + OpenStreetMap (free, no token required).
 * Falls back to Mapbox if VITE_MAPBOX_TOKEN is configured.
 *
 * Features:
 * - View captured property location
 * - Click/drag to adjust coordinates
 * - Display nearby amenities (MRT, bus stops, schools, etc.)
 * - Heritage overlay visualization
 */

import { useCallback, useEffect, useRef, useState } from 'react'
import * as L from 'leaflet'
import 'leaflet/dist/leaflet.css'

// ============================================================================
// Types
// ============================================================================

export interface NearbyAmenity {
  name: string
  type: 'mrt' | 'bus' | 'school' | 'mall' | 'park'
  latitude: number
  longitude: number
  distance_m?: number
}

export interface HeritageFeature {
  name: string
  status?: string
  risk_level?: 'low' | 'medium' | 'high'
  latitude: number
  longitude: number
}

export interface PropertyLocationMapProps {
  /** Current latitude */
  latitude: string
  /** Current longitude */
  longitude: string
  /** Callback when coordinates change (from marker drag or map click) */
  onCoordinatesChange?: (lat: string, lon: string) => void
  /** Property address to display in popup */
  address?: string
  /** District name */
  district?: string
  /** Zoning code */
  zoningCode?: string
  /** Nearby amenities to display as markers */
  nearbyAmenities?: {
    mrtStations?: NearbyAmenity[]
    busStops?: NearbyAmenity[]
    schools?: NearbyAmenity[]
    malls?: NearbyAmenity[]
    parks?: NearbyAmenity[]
  }
  /** Heritage features to display */
  heritageFeatures?: HeritageFeature[]
  /** Whether the map is interactive (allows coordinate changes) */
  interactive?: boolean
  /** Map height in pixels */
  height?: number
  /** Show amenity markers */
  showAmenities?: boolean
  /** Show heritage overlay */
  showHeritage?: boolean
}

// ============================================================================
// Constants
// ============================================================================

const AMENITY_COLORS: Record<string, string> = {
  mrt: '#e74c3c',
  bus: '#3498db',
  school: '#f39c12',
  mall: '#9b59b6',
  park: '#27ae60',
}

const AMENITY_ICONS: Record<string, string> = {
  mrt: '🚇',
  bus: '🚌',
  school: '🏫',
  mall: '🛒',
  park: '🌳',
}

const HERITAGE_COLORS: Record<string, string> = {
  low: '#27ae60',
  medium: '#f39c12',
  high: '#e74c3c',
}

// Grayscale tile providers (free, no token required)
// CartoDB Positron - clean grayscale style, great for UI
const CARTO_POSITRON_URL = 'https://{s}.basemaps.cartocdn.com/light_all/{z}/{x}/{y}{r}.png'
const CARTO_ATTRIBUTION = '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors &copy; <a href="https://carto.com/attributions">CARTO</a>'

// ============================================================================
// Component
// ============================================================================

export function PropertyLocationMap({
  latitude,
  longitude,
  onCoordinatesChange,
  address,
  district,
  zoningCode,
  nearbyAmenities,
  heritageFeatures,
  interactive = true,
  height = 400,
  showAmenities = true,
  showHeritage = true,
}: PropertyLocationMapProps) {
  const mapContainerRef = useRef<HTMLDivElement | null>(null)
  const mapInstanceRef = useRef<L.Map | null>(null)
  const mainMarkerRef = useRef<L.Marker | null>(null)
  const amenityMarkersRef = useRef<L.Marker[]>([])
  const heritageMarkersRef = useRef<L.Marker[]>([])

  const [isMapLoaded, setIsMapLoaded] = useState(false)

  // Parse coordinates
  const lat = parseFloat(latitude) || 1.3
  const lon = parseFloat(longitude) || 103.85

  // Initialize map
  useEffect(() => {
    if (mapInstanceRef.current || !mapContainerRef.current) {
      return
    }

    // Create map with grayscale tiles
    const map = L.map(mapContainerRef.current, {
      center: [lat, lon],
      zoom: 15,
      zoomControl: true,
    })

    // Add grayscale tile layer (CartoDB Positron - clean UI style)
    L.tileLayer(CARTO_POSITRON_URL, {
      attribution: CARTO_ATTRIBUTION,
      maxZoom: 19,
      subdomains: 'abcd',
    }).addTo(map)

    // Create custom marker icon
    const propertyIcon = L.divIcon({
      className: 'property-marker',
      html: `<div style="
        width: 32px;
        height: 32px;
        background: #1d1d1f;
        border: 3px solid white;
        border-radius: 50%;
        box-shadow: 0 2px 8px rgba(0,0,0,0.3);
        display: flex;
        align-items: center;
        justify-content: center;
      "><span style="color: white; font-size: 14px;">📍</span></div>`,
      iconSize: [32, 32],
      iconAnchor: [16, 16],
    })

    // Create main property marker
    const marker = L.marker([lat, lon], {
      icon: propertyIcon,
      draggable: interactive,
    }).addTo(map)

    // Add popup with property info
    if (address || district || zoningCode) {
      marker.bindPopup(buildPopupContent(address, district, zoningCode))
    }

    // Handle marker drag
    if (interactive && onCoordinatesChange) {
      marker.on('dragend', () => {
        const pos = marker.getLatLng()
        onCoordinatesChange(pos.lat.toFixed(6), pos.lng.toFixed(6))
      })
    }

    // Handle map click
    if (interactive && onCoordinatesChange) {
      map.on('click', (event: L.LeafletMouseEvent) => {
        const { lat: clickLat, lng } = event.latlng
        marker.setLatLng([clickLat, lng])
        onCoordinatesChange(clickLat.toFixed(6), lng.toFixed(6))
      })
    }

    mapInstanceRef.current = map
    mainMarkerRef.current = marker
    setIsMapLoaded(true)

    return () => {
      map.remove()
      mapInstanceRef.current = null
      mainMarkerRef.current = null
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps -- Intentionally run only once on mount
  }, [])

  // Update marker position when coordinates change externally
  useEffect(() => {
    if (mainMarkerRef.current && mapInstanceRef.current) {
      const currentPos = mainMarkerRef.current.getLatLng()
      if (Math.abs(currentPos.lat - lat) > 0.00001 || Math.abs(currentPos.lng - lon) > 0.00001) {
        mainMarkerRef.current.setLatLng([lat, lon])
        mapInstanceRef.current.flyTo([lat, lon], 15, { duration: 0.5 })
      }
    }
  }, [lat, lon])

  // Update popup content when address changes
  useEffect(() => {
    if (mainMarkerRef.current && (address || district || zoningCode)) {
      mainMarkerRef.current.unbindPopup()
      mainMarkerRef.current.bindPopup(buildPopupContent(address, district, zoningCode))
    }
  }, [address, district, zoningCode])

  // Add/update amenity markers
  useEffect(() => {
    if (!mapInstanceRef.current || !isMapLoaded || !showAmenities) {
      return
    }

    // Clear existing amenity markers
    amenityMarkersRef.current.forEach((marker) => marker.remove())
    amenityMarkersRef.current = []

    if (!nearbyAmenities) {
      return
    }

    const allAmenities: NearbyAmenity[] = [
      ...(nearbyAmenities.mrtStations || []),
      ...(nearbyAmenities.busStops?.slice(0, 3) || []),
      ...(nearbyAmenities.schools?.slice(0, 3) || []),
      ...(nearbyAmenities.malls?.slice(0, 3) || []),
      ...(nearbyAmenities.parks?.slice(0, 3) || []),
    ]

    allAmenities.forEach((amenity) => {
      const icon = createAmenityIcon(amenity.type)
      const marker = L.marker([amenity.latitude, amenity.longitude], { icon })
        .addTo(mapInstanceRef.current!)

      const distanceText = amenity.distance_m
        ? `${Math.round(amenity.distance_m)}m away`
        : ''
      marker.bindPopup(`
        <div style="font-family: system-ui, sans-serif; padding: 4px;">
          <div style="font-weight: 600; font-size: 13px;">${AMENITY_ICONS[amenity.type]} ${amenity.name}</div>
          ${distanceText ? `<div style="font-size: 11px; color: #666; margin-top: 2px;">${distanceText}</div>` : ''}
        </div>
      `)

      amenityMarkersRef.current.push(marker)
    })
  }, [nearbyAmenities, isMapLoaded, showAmenities])

  // Add/update heritage markers
  useEffect(() => {
    if (!mapInstanceRef.current || !isMapLoaded || !showHeritage) {
      return
    }

    // Clear existing heritage markers
    heritageMarkersRef.current.forEach((marker) => marker.remove())
    heritageMarkersRef.current = []

    if (!heritageFeatures || heritageFeatures.length === 0) {
      return
    }

    heritageFeatures.forEach((feature) => {
      const icon = createHeritageIcon(feature.risk_level || 'medium')
      const marker = L.marker([feature.latitude, feature.longitude], { icon })
        .addTo(mapInstanceRef.current!)

      marker.bindPopup(`
        <div style="font-family: system-ui, sans-serif; padding: 4px;">
          <div style="font-weight: 600; font-size: 13px;">🏛️ ${feature.name}</div>
          ${feature.status ? `<div style="font-size: 11px; color: #666; margin-top: 2px;">Status: ${feature.status}</div>` : ''}
          ${feature.risk_level ? `<div style="font-size: 11px; margin-top: 2px;">
            <span style="display: inline-block; width: 8px; height: 8px; border-radius: 50%; background: ${HERITAGE_COLORS[feature.risk_level]}; margin-right: 4px;"></span>
            ${feature.risk_level.charAt(0).toUpperCase() + feature.risk_level.slice(1)} risk
          </div>` : ''}
        </div>
      `)

      heritageMarkersRef.current.push(marker)
    })
  }, [heritageFeatures, isMapLoaded, showHeritage])

  // Recenter map handler
  const handleRecenter = useCallback(() => {
    if (mapInstanceRef.current) {
      mapInstanceRef.current.flyTo([lat, lon], 15, { duration: 0.5 })
    }
  }, [lat, lon])

  return (
    <div style={{ position: 'relative' }}>
      <div
        ref={mapContainerRef}
        style={{
          width: '100%',
          height: `${height}px`,
          borderRadius: '12px',
          overflow: 'hidden',
          background: '#f5f5f7',
        }}
        aria-label="Property location map"
      />

      {/* Map controls overlay */}
      <div
        style={{
          position: 'absolute',
          bottom: '1rem',
          right: '1rem',
          display: 'flex',
          gap: '0.5rem',
          zIndex: 1000,
        }}
      >
        <button
          type="button"
          onClick={handleRecenter}
          style={{
            padding: '0.5rem 0.75rem',
            fontSize: '0.75rem',
            fontWeight: 500,
            background: 'white',
            border: '1px solid #d2d2d7',
            borderRadius: '8px',
            cursor: 'pointer',
            boxShadow: '0 2px 4px rgba(0,0,0,0.1)',
          }}
          title="Recenter map on property"
        >
          ⊕ Recenter
        </button>
      </div>

      {/* Legend */}
      {(showAmenities || showHeritage) && (
        <div
          style={{
            position: 'absolute',
            top: '0.5rem',
            left: '0.5rem',
            background: 'white',
            borderRadius: '8px',
            padding: '0.5rem 0.75rem',
            fontSize: '0.7rem',
            boxShadow: '0 2px 4px rgba(0,0,0,0.1)',
            maxWidth: '150px',
            zIndex: 1000,
          }}
        >
          <div style={{ fontWeight: 600, marginBottom: '0.25rem' }}>Legend</div>
          {showAmenities && (
            <>
              <div style={{ display: 'flex', alignItems: 'center', gap: '4px' }}>
                <span>🚇</span> MRT
              </div>
              <div style={{ display: 'flex', alignItems: 'center', gap: '4px' }}>
                <span>🚌</span> Bus
              </div>
              <div style={{ display: 'flex', alignItems: 'center', gap: '4px' }}>
                <span>🏫</span> School
              </div>
            </>
          )}
          {showHeritage && (
            <div style={{ display: 'flex', alignItems: 'center', gap: '4px' }}>
              <span>🏛️</span> Heritage
            </div>
          )}
        </div>
      )}

      {/* Map provider indicator */}
      <div
        style={{
          position: 'absolute',
          bottom: '0.5rem',
          left: '0.5rem',
          background: 'rgba(255,255,255,0.9)',
          borderRadius: '4px',
          padding: '2px 6px',
          fontSize: '0.6rem',
          color: '#666',
          zIndex: 1000,
        }}
      >
        CartoDB Positron
      </div>

      {/* Instructions hint */}
      {interactive && (
        <p
          style={{
            margin: '0.5rem 0 0',
            fontSize: '0.8rem',
            color: '#6e6e73',
          }}
        >
          Click on the map or drag the marker to adjust coordinates.
        </p>
      )}
    </div>
  )
}

// ============================================================================
// Helper Functions
// ============================================================================

function createAmenityIcon(type: string): L.DivIcon {
  const color = AMENITY_COLORS[type] || '#666'
  return L.divIcon({
    className: 'amenity-marker',
    html: `<div style="
      width: 24px;
      height: 24px;
      background: ${color};
      border: 2px solid white;
      border-radius: 50%;
      box-shadow: 0 1px 4px rgba(0,0,0,0.2);
      display: flex;
      align-items: center;
      justify-content: center;
      font-size: 12px;
    ">${AMENITY_ICONS[type] || '📌'}</div>`,
    iconSize: [24, 24],
    iconAnchor: [12, 12],
  })
}

function createHeritageIcon(riskLevel: string): L.DivIcon {
  const color = HERITAGE_COLORS[riskLevel] || HERITAGE_COLORS.medium
  return L.divIcon({
    className: 'heritage-marker',
    html: `<div style="
      width: 28px;
      height: 28px;
      background: ${color};
      border: 2px solid white;
      border-radius: 4px;
      box-shadow: 0 1px 4px rgba(0,0,0,0.2);
      display: flex;
      align-items: center;
      justify-content: center;
      font-size: 14px;
    ">🏛️</div>`,
    iconSize: [28, 28],
    iconAnchor: [14, 14],
  })
}

function buildPopupContent(
  address?: string,
  district?: string,
  zoningCode?: string
): string {
  const parts: string[] = []

  if (address) {
    parts.push(`<div style="font-weight: 600; font-size: 13px; margin-bottom: 4px;">${address}</div>`)
  }

  const details: string[] = []
  if (district) details.push(`District: ${district}`)
  if (zoningCode) details.push(`Zoning: ${zoningCode}`)

  if (details.length > 0) {
    parts.push(`<div style="font-size: 11px; color: #666;">${details.join(' • ')}</div>`)
  }

  return `<div style="font-family: system-ui, sans-serif; padding: 4px;">${parts.join('')}</div>`
}

export default PropertyLocationMap
