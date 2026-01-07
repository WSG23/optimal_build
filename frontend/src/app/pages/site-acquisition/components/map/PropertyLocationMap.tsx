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
import { Box, IconButton } from '@mui/material'
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
  /** Map height (CSS value) */
  height?: string
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

const AMENITY_ICONS: Record<string, string> = {
  mrt: '🚇',
  bus: '🚌',
  school: '🏫',
  mall: '🛒',
  park: '🌳',
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
  height = 'var(--ob-size-controls-min)',
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
      className: 'ob-map-marker ob-map-marker--property',
      html: `<div class="ob-map-marker__inner"><span class="ob-map-marker__icon" aria-hidden="true">📍</span></div>`,
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
      marker.bindPopup(buildPropertyPopupContent(address, district, zoningCode))
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
        buildPropertyPopupContent(address, district, zoningCode),
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
      marker.bindPopup(buildAmenityPopupContent(amenity, distanceText))

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

      marker.bindPopup(buildHeritagePopupContent(feature))

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
    <div className="map-hud">
      <Box
        ref={mapContainerRef}
        className="map-hud__viewport"
        sx={{ height }}
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
      <div className="map-hud__controls">
        <IconButton
          onClick={handleRecenter}
          aria-label="Recenter map on property"
          size="small"
          className="map-hud__control-btn"
          sx={{
            bgcolor: 'var(--ob-color-bg-surface)',
            border: '1px solid var(--ob-color-border-subtle)',
            borderRadius: 'var(--ob-radius-xs)',
            boxShadow: 'var(--ob-shadow-sm)',
            color: 'var(--ob-color-text-primary)',
            '&:hover': {
              bgcolor: 'var(--ob-color-neon-cyan-muted)',
              color: 'var(--ob-color-neon-cyan)',
              borderColor: 'var(--ob-color-neon-cyan)',
            },
          }}
        >
          <MyLocation sx={{ fontSize: 'var(--ob-font-size-lg)' }} />
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
  return L.divIcon({
    className: `ob-map-marker ob-map-marker--amenity ob-map-marker--amenity-${type}`,
    html: `<div class="ob-map-marker__inner"><span class="ob-map-marker__icon" aria-hidden="true">${AMENITY_ICONS[type] || '📌'}</span></div>`,
    iconSize: [24, 24],
    iconAnchor: [12, 12],
  })
}

function createHeritageIcon(riskLevel: string): L.DivIcon {
  return L.divIcon({
    className: `ob-map-marker ob-map-marker--heritage ob-map-marker--heritage-${riskLevel}`,
    html: `<div class="ob-map-marker__inner"><span class="ob-map-marker__icon" aria-hidden="true">🏛️</span></div>`,
    iconSize: [28, 28],
    iconAnchor: [14, 14],
  })
}

function buildPropertyPopupContent(
  address?: string,
  district?: string,
  zoningCode?: string,
): string {
  const safeAddress = address ? escapeHtml(address) : null
  const safeDistrict = district ? escapeHtml(district) : null
  const safeZoning = zoningCode ? escapeHtml(zoningCode) : null

  const details: string[] = []
  if (safeDistrict) details.push(`District: ${safeDistrict}`)
  if (safeZoning) details.push(`Zoning: ${safeZoning}`)

  return `
    <div class="ob-map-popup">
      ${safeAddress ? `<div class="ob-map-popup__title">${safeAddress}</div>` : ''}
      ${
        details.length > 0
          ? `<div class="ob-map-popup__subtitle">${details.join(' • ')}</div>`
          : ''
      }
    </div>
  `
}

function buildAmenityPopupContent(
  amenity: NearbyAmenity,
  distanceText: string,
): string {
  const safeName = escapeHtml(amenity.name)
  const safeDistance = distanceText ? escapeHtml(distanceText) : null
  return `
    <div class="ob-map-popup">
      <div class="ob-map-popup__title">${AMENITY_ICONS[amenity.type]} ${safeName}</div>
      ${
        safeDistance
          ? `<div class="ob-map-popup__subtitle">${safeDistance}</div>`
          : ''
      }
    </div>
  `
}

function buildHeritagePopupContent(feature: HeritageFeature): string {
  const safeName = escapeHtml(feature.name)
  const safeStatus = feature.status ? escapeHtml(feature.status) : null
  const riskLevel = feature.risk_level
  const safeRiskLabel = riskLevel
    ? escapeHtml(
        `${riskLevel.charAt(0).toUpperCase()}${riskLevel.slice(1)} risk`,
      )
    : null

  return `
    <div class="ob-map-popup">
      <div class="ob-map-popup__title">🏛️ ${safeName}</div>
      ${
        safeStatus
          ? `<div class="ob-map-popup__subtitle">Status: ${safeStatus}</div>`
          : ''
      }
      ${
        riskLevel && safeRiskLabel
          ? `<div class="ob-map-popup__meta">
              <span class="ob-map-popup__risk-dot ob-map-popup__risk-dot--${escapeHtml(riskLevel)}" aria-hidden="true"></span>
              ${safeRiskLabel}
            </div>`
          : ''
      }
    </div>
  `
}

function escapeHtml(value: string): string {
  return value
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;')
    .replace(/'/g, '&#039;')
}

export default PropertyLocationMap
