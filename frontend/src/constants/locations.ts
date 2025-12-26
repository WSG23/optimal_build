/**
 * Location Constants - Single Source of Truth
 *
 * All jurisdiction defaults, coordinates, and geographic constants.
 * NEVER hardcode coordinates or location data in components.
 */

// =============================================================================
// COORDINATE TYPES
// =============================================================================

export interface Coordinates {
  latitude: number
  longitude: number
}

export interface JurisdictionConfig {
  id: string
  name: string
  country: string
  timezone: string
  currency: string
  currencySymbol: string
  defaultCoordinates: Coordinates
  bounds?: {
    north: number
    south: number
    east: number
    west: number
  }
}

// =============================================================================
// DEFAULT COORDINATES BY JURISDICTION
// =============================================================================

export const COORDINATES = {
  SINGAPORE: {
    latitude: 1.3521,
    longitude: 103.8198,
  },
  SEATTLE: {
    latitude: 47.6062,
    longitude: -122.3321,
  },
  HONG_KONG: {
    latitude: 22.3193,
    longitude: 114.1694,
  },
  LONDON: {
    latitude: 51.5074,
    longitude: -0.1278,
  },
  NEW_YORK: {
    latitude: 40.7128,
    longitude: -74.006,
  },
} as const

// =============================================================================
// DEFAULT COORDINATE (Singapore - primary market)
// =============================================================================

export const DEFAULT_COORDINATES: Coordinates = COORDINATES.SINGAPORE

// String versions for form inputs
export const DEFAULT_LATITUDE_STR = DEFAULT_COORDINATES.latitude.toFixed(4)
export const DEFAULT_LONGITUDE_STR = DEFAULT_COORDINATES.longitude.toFixed(4)

// =============================================================================
// JURISDICTION CONFIGURATIONS
// =============================================================================

export const JURISDICTIONS: Record<string, JurisdictionConfig> = {
  SINGAPORE: {
    id: 'singapore',
    name: 'Singapore',
    country: 'Singapore',
    timezone: 'Asia/Singapore',
    currency: 'SGD',
    currencySymbol: 'S$',
    defaultCoordinates: COORDINATES.SINGAPORE,
    bounds: {
      north: 1.4705,
      south: 1.1496,
      east: 104.0885,
      west: 103.6055,
    },
  },
  SEATTLE: {
    id: 'seattle',
    name: 'Seattle',
    country: 'United States',
    timezone: 'America/Los_Angeles',
    currency: 'USD',
    currencySymbol: '$',
    defaultCoordinates: COORDINATES.SEATTLE,
    bounds: {
      north: 47.7341,
      south: 47.4919,
      east: -122.2244,
      west: -122.4597,
    },
  },
  HONG_KONG: {
    id: 'hong_kong',
    name: 'Hong Kong',
    country: 'Hong Kong SAR',
    timezone: 'Asia/Hong_Kong',
    currency: 'HKD',
    currencySymbol: 'HK$',
    defaultCoordinates: COORDINATES.HONG_KONG,
    bounds: {
      north: 22.5619,
      south: 22.1533,
      east: 114.4295,
      west: 113.8259,
    },
  },
} as const

// =============================================================================
// DEFAULT JURISDICTION
// =============================================================================

export const DEFAULT_JURISDICTION = JURISDICTIONS.SINGAPORE

// =============================================================================
// MAP CONFIGURATION
// =============================================================================

export const MAP_CONFIG = {
  /** Default zoom level for property maps */
  DEFAULT_ZOOM: 15,
  /** Zoom level for city-wide view */
  CITY_ZOOM: 12,
  /** Zoom level for neighborhood view */
  NEIGHBORHOOD_ZOOM: 14,
  /** Zoom level for property detail view */
  PROPERTY_ZOOM: 18,
  /** Maximum zoom level */
  MAX_ZOOM: 20,
  /** Minimum zoom level */
  MIN_ZOOM: 3,
} as const

// =============================================================================
// JURISDICTION OPTIONS FOR DROPDOWNS
// =============================================================================

export const JURISDICTION_OPTIONS = Object.values(JURISDICTIONS).map((j) => ({
  value: j.id,
  label: j.name,
  country: j.country,
  coordinates: j.defaultCoordinates,
}))

// =============================================================================
// HELPER FUNCTIONS
// =============================================================================

/**
 * Get jurisdiction config by ID
 */
export function getJurisdiction(id: string): JurisdictionConfig | undefined {
  return Object.values(JURISDICTIONS).find(
    (j) => j.id.toLowerCase() === id.toLowerCase(),
  )
}

/**
 * Get default coordinates for a jurisdiction
 */
export function getDefaultCoordinates(jurisdictionId?: string): Coordinates {
  if (!jurisdictionId) return DEFAULT_COORDINATES
  const jurisdiction = getJurisdiction(jurisdictionId)
  return jurisdiction?.defaultCoordinates || DEFAULT_COORDINATES
}

/**
 * Format coordinates for display
 */
export function formatCoordinates(coords: Coordinates, precision = 4): string {
  return `${coords.latitude.toFixed(precision)}, ${coords.longitude.toFixed(precision)}`
}

/**
 * Check if coordinates are within jurisdiction bounds
 */
export function isWithinBounds(
  coords: Coordinates,
  jurisdictionId: string,
): boolean {
  const jurisdiction = getJurisdiction(jurisdictionId)
  if (!jurisdiction?.bounds) return true

  const { north, south, east, west } = jurisdiction.bounds
  return (
    coords.latitude <= north &&
    coords.latitude >= south &&
    coords.longitude <= east &&
    coords.longitude >= west
  )
}
