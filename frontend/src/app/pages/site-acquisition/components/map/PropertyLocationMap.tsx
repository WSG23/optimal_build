/**
 * Property Location Map Component
 *
 * Interactive map for site acquisition using Leaflet + OpenStreetMap (free, no token required).
 * Falls back to Mapbox if VITE_MAPBOX_ACCESS_TOKEN is configured.
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
import { IconButton } from '@mui/material'
import { MyLocation } from '@mui/icons-material'

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
  /** Property/Asset ID for HUD display */
  propertyId?: string
  /** Status indicator for HUD (e.g., 'capturing', 'idle', 'live') */
  status?: 'capturing' | 'idle' | 'live'
  /** Show tactical HUD overlay with telemetry */
  showHud?: boolean
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
const CARTO_POSITRON_URL =
  'https://{s}.basemaps.cartocdn.com/light_all/{z}/{x}/{y}{r}.png'
const CARTO_ATTRIBUTION =
  '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors &copy; <a href="https://carto.com/attributions">CARTO</a>'

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
  propertyId,
  status = 'idle',
  showHud = true,
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
      if (
        Math.abs(currentPos.lat - lat) > 0.00001 ||
        Math.abs(currentPos.lng - lon) > 0.00001
      ) {
        mainMarkerRef.current.setLatLng([lat, lon])
        mapInstanceRef.current.flyTo([lat, lon], 15, { duration: 0.5 })
      }
    }
  }, [lat, lon])

  // Update popup content when address changes
  useEffect(() => {
    if (mainMarkerRef.current && (address || district || zoningCode)) {
      mainMarkerRef.current.unbindPopup()
      mainMarkerRef.current.bindPopup(
        buildPopupContent(address, district, zoningCode),
      )
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
      const marker = L.marker([amenity.latitude, amenity.longitude], {
        icon,
      }).addTo(mapInstanceRef.current!)

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
      const marker = L.marker([feature.latitude, feature.longitude], {
        icon,
      }).addTo(mapInstanceRef.current!)

      marker.bindPopup(`
        <div style="font-family: system-ui, sans-serif; padding: 4px;">
          <div style="font-weight: 600; font-size: 13px;">🏛️ ${feature.name}</div>
          ${feature.status ? `<div style="font-size: 11px; color: #666; margin-top: 2px;">Status: ${feature.status}</div>` : ''}
          ${
            feature.risk_level
              ? `<div style="font-size: 11px; margin-top: 2px;">
            <span style="display: inline-block; width: 8px; height: 8px; border-radius: 50%; background: ${HERITAGE_COLORS[feature.risk_level]}; margin-right: 4px;"></span>
            ${feature.risk_level.charAt(0).toUpperCase() + feature.risk_level.slice(1)} risk
          </div>`
              : ''
          }
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

  // Generate current timestamp for HUD
  const currentTimestamp = new Date()
    .toISOString()
    .slice(0, 19)
    .replace('T', ' ')

  return (
    <div className="map-hud" style={{ position: 'relative' }}>
      <div
        ref={mapContainerRef}
        className="map-hud__viewport"
        style={{
          width: '100%',
          height: `${height}px`,
          borderRadius: 'var(--ob-radius-sm)',
          overflow: 'hidden',
          background: '#f5f5f7',
        }}
        aria-label="Property location map"
      />

      {/* Tactical HUD Overlay */}
      {showHud && (
        <>
          {/* Top-Left: Coordinates */}
          <div className="map-hud__corner map-hud__corner--top-left">
            <span className="map-hud__label">LAT/LON</span>
            <span className="map-hud__value">
              {lat.toFixed(6)}, {lon.toFixed(6)}
            </span>
          </div>

          {/* Top-Right: Timestamp */}
          <div className="map-hud__corner map-hud__corner--top-right">
            <span className="map-hud__label">SYS TIME</span>
            <span className="map-hud__value">{currentTimestamp}</span>
          </div>

          {/* Bottom-Left: Asset ID */}
          <div className="map-hud__corner map-hud__corner--bottom-left">
            <span className="map-hud__label">ASSET ID</span>
            <span className="map-hud__value">{propertyId || '—'}</span>
          </div>

          {/* Bottom-Right: Status Indicator */}
          <div className="map-hud__corner map-hud__corner--bottom-right">
            <span className="map-hud__label">STATUS</span>
            <span className={`map-hud__status map-hud__status--${status}`}>
              <span className="map-hud__status-dot" />
              {status.toUpperCase()}
            </span>
          </div>
        </>
      )}

      {/* Map controls overlay */}
      <div
        style={{
          position: 'absolute',
          bottom: 'var(--ob-space-300)',
          right: 'var(--ob-space-100)',
          display: 'flex',
          gap: 'var(--ob-space-050)',
          zIndex: 1000,
        }}
      >
        <IconButton
          onClick={handleRecenter}
          aria-label="Recenter map on property"
          size="small"
          sx={{
            bgcolor: 'white',
            border: '1px solid rgba(0, 0, 0, 0.2)',
            borderRadius: 'var(--ob-radius-xs)',
            boxShadow: '0 2px 6px rgba(0,0,0,0.2)',
            color: '#333',
            '&:hover': {
              bgcolor: 'var(--ob-color-neon-cyan-muted)',
              color: 'var(--ob-color-neon-cyan)',
              borderColor: 'var(--ob-color-neon-cyan)',
            },
          }}
        >
          <MyLocation sx={{ fontSize: 18 }} />
        </IconButton>
      </div>

      {/* Legend - repositioned to avoid HUD overlap */}
      {(showAmenities || showHeritage) && (
        <div className="map-hud__legend">
          <div className="map-hud__legend-title">LEGEND</div>
          {showAmenities && (
            <>
              <div className="map-hud__legend-item">
                <span>🚇</span> MRT
              </div>
              <div className="map-hud__legend-item">
                <span>🚌</span> Bus
              </div>
              <div className="map-hud__legend-item">
                <span>🏫</span> School
              </div>
            </>
          )}
          {showHeritage && (
            <div className="map-hud__legend-item">
              <span>🏛️</span> Heritage
            </div>
          )}
        </div>
      )}

      {/* Instructions hint */}
      {interactive && (
        <p className="map-hud__hint">
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
  zoningCode?: string,
): string {
  const parts: string[] = []

  if (address) {
    parts.push(
      `<div style="font-weight: 600; font-size: 13px; margin-bottom: 4px;">${address}</div>`,
    )
  }

  const details: string[] = []
  if (district) details.push(`District: ${district}`)
  if (zoningCode) details.push(`Zoning: ${zoningCode}`)

  if (details.length > 0) {
    parts.push(
      `<div style="font-size: 11px; color: #666;">${details.join(' • ')}</div>`,
    )
  }

  return `<div style="font-family: system-ui, sans-serif; padding: 4px;">${parts.join('')}</div>`
}

export default PropertyLocationMap
