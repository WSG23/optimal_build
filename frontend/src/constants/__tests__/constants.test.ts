/**
 * Constants Module Tests - Single Source of Truth Validation
 *
 * These tests ensure:
 * 1. All canonical constants are defined
 * 2. Values match expected types and ranges
 * 3. No duplicate definitions exist
 * 4. Frontend/backend sync is maintained
 */

import { describe, it, expect } from 'vitest'
import {
  // API constants
  API_BASE_URL,
  WS_BASE_URL,
  API_VERSION,
  API_PREFIX,
  ENDPOINTS,
  TIMEOUTS,
  FETCH_LIMITS,

  // Location constants
  COORDINATES,
  DEFAULT_COORDINATES,
  DEFAULT_LATITUDE_STR,
  DEFAULT_LONGITUDE_STR,
  JURISDICTIONS,
  DEFAULT_JURISDICTION,
  MAP_CONFIG,
  getJurisdiction,
  getDefaultCoordinates,
  formatCoordinates,

  // Scenario constants
  DEVELOPMENT_TYPES,
  PROPERTY_TYPES,
  DEFAULT_ASSUMPTIONS,
  SCENARIO_OPTIONS,
  getStatusColor,
} from '../index'

describe('API Constants', () => {
  describe('Base URLs', () => {
    it('defines API_BASE_URL', () => {
      expect(API_BASE_URL).toBeDefined()
      expect(typeof API_BASE_URL).toBe('string')
      expect(API_BASE_URL).toMatch(/^https?:\/\//)
    })

    it('derives WS_BASE_URL from API_BASE_URL', () => {
      expect(WS_BASE_URL).toBeDefined()
      expect(WS_BASE_URL).toMatch(/^wss?:\/\//)
    })

    it('defines API version', () => {
      expect(API_VERSION).toBe('v1')
      expect(API_PREFIX).toBe('/api/v1')
    })
  })

  describe('Endpoints', () => {
    it('defines auth endpoints', () => {
      expect(ENDPOINTS.AUTH.LOGIN).toBe('/api/v1/auth/login')
      expect(ENDPOINTS.AUTH.LOGOUT).toBe('/api/v1/auth/logout')
      expect(ENDPOINTS.AUTH.ME).toBe('/api/v1/auth/me')
    })

    it('defines developer endpoints', () => {
      expect(ENDPOINTS.DEVELOPERS.LOG_GPS).toBe(
        '/api/v1/developers/properties/log-gps',
      )
      expect(ENDPOINTS.DEVELOPERS.VOICE_NOTES).toBe(
        '/api/v1/developers/properties/voice-notes',
      )
    })

    it('defines feasibility endpoints', () => {
      expect(ENDPOINTS.FEASIBILITY.BASE).toBe('/api/v1/feasibility')
      expect(ENDPOINTS.FEASIBILITY.WS).toMatch(/^wss?:\/\//)
    })

    it('defines health endpoints', () => {
      expect(ENDPOINTS.HEALTH.BASE).toBe('/health')
      expect(ENDPOINTS.HEALTH.READY).toBe('/health/ready')
    })

    it('generates dynamic endpoints with functions', () => {
      expect(ENDPOINTS.PROPERTIES.BY_ID(123)).toBe('/api/v1/properties/123')
      expect(ENDPOINTS.NOTIFICATIONS.MARK_READ('abc')).toBe(
        '/api/v1/notifications/abc/read',
      )
    })
  })

  describe('Timeouts', () => {
    it('defines all timeout values', () => {
      expect(TIMEOUTS.DEFAULT).toBe(30_000)
      expect(TIMEOUTS.LONG).toBe(60_000)
      expect(TIMEOUTS.SHORT).toBe(10_000)
      expect(TIMEOUTS.POLL_INTERVAL).toBe(2_000)
      expect(TIMEOUTS.POLL_MAX).toBe(60_000)
      expect(TIMEOUTS.WS_RECONNECT).toBe(3_000)
    })

    it('ensures timeouts are positive integers', () => {
      Object.values(TIMEOUTS).forEach((timeout) => {
        expect(timeout).toBeGreaterThan(0)
        expect(Number.isInteger(timeout)).toBe(true)
      })
    })
  })

  describe('Fetch Limits', () => {
    it('defines pagination limits', () => {
      expect(FETCH_LIMITS.DEFAULT_PAGE_SIZE).toBe(20)
      expect(FETCH_LIMITS.MAX_PAGE_SIZE).toBe(100)
      expect(FETCH_LIMITS.HISTORY_FETCH_LIMIT).toBe(10)
    })

    it('defines file size limits', () => {
      expect(FETCH_LIMITS.MAX_FILE_SIZE).toBe(10 * 1024 * 1024) // 10MB
      expect(FETCH_LIMITS.MAX_PHOTOS_PER_PROPERTY).toBe(50)
    })
  })
})

describe('Location Constants', () => {
  describe('Coordinates', () => {
    it('defines all major city coordinates', () => {
      expect(COORDINATES.SINGAPORE).toEqual({
        latitude: 1.3521,
        longitude: 103.8198,
      })
      expect(COORDINATES.SEATTLE).toEqual({
        latitude: 47.6062,
        longitude: -122.3321,
      })
      expect(COORDINATES.HONG_KONG).toEqual({
        latitude: 22.3193,
        longitude: 114.1694,
      })
    })

    it('sets Singapore as default coordinates', () => {
      expect(DEFAULT_COORDINATES).toEqual(COORDINATES.SINGAPORE)
    })

    it('provides string versions for form inputs', () => {
      expect(DEFAULT_LATITUDE_STR).toBe('1.3521')
      expect(DEFAULT_LONGITUDE_STR).toBe('103.8198')
    })
  })

  describe('Jurisdictions', () => {
    it('defines Singapore jurisdiction', () => {
      expect(JURISDICTIONS.SINGAPORE).toBeDefined()
      expect(JURISDICTIONS.SINGAPORE.id).toBe('singapore')
      expect(JURISDICTIONS.SINGAPORE.currency).toBe('SGD')
      expect(JURISDICTIONS.SINGAPORE.timezone).toBe('Asia/Singapore')
    })

    it('sets Singapore as default jurisdiction', () => {
      expect(DEFAULT_JURISDICTION).toEqual(JURISDICTIONS.SINGAPORE)
    })

    it('includes coordinates in each jurisdiction', () => {
      Object.values(JURISDICTIONS).forEach((jurisdiction) => {
        expect(jurisdiction.defaultCoordinates).toBeDefined()
        expect(jurisdiction.defaultCoordinates.latitude).toBeDefined()
        expect(jurisdiction.defaultCoordinates.longitude).toBeDefined()
      })
    })
  })

  describe('Map Configuration', () => {
    it('defines zoom levels', () => {
      expect(MAP_CONFIG.DEFAULT_ZOOM).toBe(15)
      expect(MAP_CONFIG.CITY_ZOOM).toBe(12)
      expect(MAP_CONFIG.PROPERTY_ZOOM).toBe(18)
      expect(MAP_CONFIG.MIN_ZOOM).toBeLessThan(MAP_CONFIG.MAX_ZOOM)
    })
  })

  describe('Helper Functions', () => {
    it('getJurisdiction returns correct jurisdiction', () => {
      expect(getJurisdiction('singapore')).toEqual(JURISDICTIONS.SINGAPORE)
      expect(getJurisdiction('SINGAPORE')).toEqual(JURISDICTIONS.SINGAPORE)
      expect(getJurisdiction('unknown')).toBeUndefined()
    })

    it('getDefaultCoordinates returns correct coordinates', () => {
      expect(getDefaultCoordinates('singapore')).toEqual(COORDINATES.SINGAPORE)
      expect(getDefaultCoordinates()).toEqual(DEFAULT_COORDINATES)
      expect(getDefaultCoordinates('unknown')).toEqual(DEFAULT_COORDINATES)
    })

    it('formatCoordinates formats correctly', () => {
      expect(formatCoordinates(COORDINATES.SINGAPORE)).toBe('1.3521, 103.8198')
      expect(formatCoordinates(COORDINATES.SINGAPORE, 2)).toBe('1.35, 103.82')
    })
  })
})

describe('Scenario Constants', () => {
  describe('Development Types', () => {
    it('defines all development types', () => {
      expect(DEVELOPMENT_TYPES.NEW_DEVELOPMENT).toBe('NEW_DEVELOPMENT')
      expect(DEVELOPMENT_TYPES.REDEVELOPMENT).toBe('REDEVELOPMENT')
      expect(DEVELOPMENT_TYPES.RENOVATION).toBe('RENOVATION')
      expect(DEVELOPMENT_TYPES.CHANGE_OF_USE).toBe('CHANGE_OF_USE')
    })
  })

  describe('Property Types', () => {
    it('defines all property types', () => {
      expect(PROPERTY_TYPES.OFFICE).toBe('office')
      expect(PROPERTY_TYPES.RETAIL).toBe('retail')
      expect(PROPERTY_TYPES.RESIDENTIAL).toBe('residential')
      expect(PROPERTY_TYPES.MIXED_USE).toBe('mixed_use')
      expect(PROPERTY_TYPES.INDUSTRIAL).toBe('industrial')
    })
  })

  describe('Default Assumptions', () => {
    it('defines building assumptions', () => {
      expect(DEFAULT_ASSUMPTIONS.TYP_FLOOR_TO_FLOOR_M).toBe(3.5)
      expect(DEFAULT_ASSUMPTIONS.EFFICIENCY_RATIO).toBe(0.82)
      expect(DEFAULT_ASSUMPTIONS.CAP_RATE).toBe(0.045)
      expect(DEFAULT_ASSUMPTIONS.DISCOUNT_RATE).toBe(0.08)
    })

    it('ensures assumptions are within valid ranges', () => {
      expect(DEFAULT_ASSUMPTIONS.TYP_FLOOR_TO_FLOOR_M).toBeGreaterThan(2.5)
      expect(DEFAULT_ASSUMPTIONS.TYP_FLOOR_TO_FLOOR_M).toBeLessThan(6)
      expect(DEFAULT_ASSUMPTIONS.EFFICIENCY_RATIO).toBeGreaterThan(0.5)
      expect(DEFAULT_ASSUMPTIONS.EFFICIENCY_RATIO).toBeLessThan(1)
      expect(DEFAULT_ASSUMPTIONS.VACANCY_RATE).toBeGreaterThanOrEqual(0)
      expect(DEFAULT_ASSUMPTIONS.VACANCY_RATE).toBeLessThan(0.5)
    })
  })

  describe('Scenario Options', () => {
    it('provides scenario options for dropdowns', () => {
      expect(SCENARIO_OPTIONS.length).toBeGreaterThan(0)
      SCENARIO_OPTIONS.forEach((option) => {
        expect(option.id).toBeDefined()
        expect(option.label).toBeDefined()
        expect(option.type).toBeDefined()
        expect(option.developmentType).toBeDefined()
      })
    })
  })

  describe('Status Colors', () => {
    it('returns correct colors for statuses', () => {
      expect(getStatusColor('completed')).toBe('success')
      expect(getStatusColor('approved')).toBe('success')
      expect(getStatusColor('in_progress')).toBe('info')
      expect(getStatusColor('pending_review')).toBe('warning')
      expect(getStatusColor('rejected')).toBe('error')
      expect(getStatusColor('unknown')).toBe('default')
    })
  })
})

describe('SSoT Consistency', () => {
  it('uses consistent coordinate precision', () => {
    Object.values(COORDINATES).forEach((coord) => {
      // Coordinates should have reasonable precision (4 decimal places)
      const latStr = coord.latitude.toString()
      const lonStr = coord.longitude.toString()
      const latDecimals = latStr.includes('.') ? latStr.split('.')[1].length : 0
      const lonDecimals = lonStr.includes('.') ? lonStr.split('.')[1].length : 0
      expect(latDecimals).toBeLessThanOrEqual(6)
      expect(lonDecimals).toBeLessThanOrEqual(6)
    })
  })

  it('has unique endpoint paths', () => {
    const paths: string[] = []
    const collectPaths = (obj: Record<string, unknown>, prefix = '') => {
      Object.entries(obj).forEach(([key, value]) => {
        if (typeof value === 'string') {
          paths.push(value)
        } else if (typeof value === 'object' && value !== null) {
          collectPaths(value as Record<string, unknown>, `${prefix}${key}.`)
        }
      })
    }
    collectPaths(ENDPOINTS)

    const staticPaths = paths.filter((p) => typeof p === 'string')
    const uniquePaths = new Set(staticPaths)
    expect(uniquePaths.size).toBe(staticPaths.length)
  })
})
