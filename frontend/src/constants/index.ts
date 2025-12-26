/**
 * Constants Module - Single Source of Truth
 *
 * This module exports all canonical constants for the application.
 * Import from here instead of defining values inline.
 *
 * @example
 * import { ENDPOINTS, DEFAULT_COORDINATES, DEFAULT_ASSUMPTIONS } from '@/constants'
 */

// API constants
export {
  API_BASE_URL,
  WS_BASE_URL,
  API_VERSION,
  API_PREFIX,
  ENDPOINTS,
  TIMEOUTS,
  FETCH_LIMITS,
  HEADERS,
  type EndpointKey,
  type TimeoutKey,
} from './api'

// Location constants
export {
  COORDINATES,
  DEFAULT_COORDINATES,
  DEFAULT_LATITUDE_STR,
  DEFAULT_LONGITUDE_STR,
  JURISDICTIONS,
  DEFAULT_JURISDICTION,
  JURISDICTION_OPTIONS,
  MAP_CONFIG,
  getJurisdiction,
  getDefaultCoordinates,
  formatCoordinates,
  isWithinBounds,
  type Coordinates,
  type JurisdictionConfig,
} from './locations'

// Scenario and development constants
export {
  DEVELOPMENT_TYPES,
  PROPERTY_TYPES,
  PROPERTY_TENURE,
  DEVELOPMENT_STATUS,
  ACQUISITION_STATUS,
  FEASIBILITY_STATUS,
  COMPLIANCE_STATUS,
  DEFAULT_ASSUMPTIONS,
  SCENARIO_OPTIONS,
  GENERATIVE_OPTIONS,
  CAPITAL_STACK_TYPES,
  FINANCING_SOURCES,
  getScenarioOption,
  getPropertyTypeLabel,
  getStatusColor,
  type DevelopmentType,
  type PropertyType,
  type PropertyTenure,
} from './scenarios'
