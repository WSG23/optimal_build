/**
 * API Constants - Single Source of Truth
 *
 * All API endpoints, timeouts, and base URLs must be defined here.
 * NEVER hardcode API paths in components or services.
 */

// =============================================================================
// BASE URLS
// =============================================================================

/**
 * Backend API base URL - resolves from environment or falls back to localhost
 */
export const API_BASE_URL =
  import.meta.env.VITE_API_URL || 'http://localhost:8000'

/**
 * WebSocket base URL - derived from API base URL
 */
export const WS_BASE_URL = API_BASE_URL.replace(/^http/, 'ws')

// =============================================================================
// TIMEOUTS (in milliseconds)
// =============================================================================

export const TIMEOUTS = {
  /** Default request timeout */
  DEFAULT: 30_000,
  /** Long-running operations (PDF generation, file uploads) */
  LONG: 60_000,
  /** Short operations (health checks) */
  SHORT: 10_000,
  /** Polling interval for status checks */
  POLL_INTERVAL: 2_000,
  /** Maximum wait time for polling operations */
  POLL_MAX: 60_000,
  /** WebSocket reconnection delay */
  WS_RECONNECT: 3_000,
} as const

// =============================================================================
// API VERSION
// =============================================================================

export const API_VERSION = 'v1'
export const API_PREFIX = `/api/${API_VERSION}`

// =============================================================================
// ENDPOINT PATHS - Grouped by domain
// =============================================================================

export const ENDPOINTS = {
  // Auth
  AUTH: {
    LOGIN: `${API_PREFIX}/auth/login`,
    LOGOUT: `${API_PREFIX}/auth/logout`,
    REFRESH: `${API_PREFIX}/auth/refresh`,
    ME: `${API_PREFIX}/auth/me`,
  },

  // Properties
  PROPERTIES: {
    BASE: `${API_PREFIX}/properties`,
    BY_ID: (id: string | number) => `${API_PREFIX}/properties/${id}`,
    SEARCH: `${API_PREFIX}/properties/search`,
  },

  // Developers / Site Acquisition
  DEVELOPERS: {
    BASE: `${API_PREFIX}/developers`,
    PROPERTIES: `${API_PREFIX}/developers/properties`,
    LOG_GPS: `${API_PREFIX}/developers/properties/log-gps`,
    VOICE_NOTES: `${API_PREFIX}/developers/properties/voice-notes`,
    PHOTOS: `${API_PREFIX}/developers/properties/photos`,
    CONDITION_ASSESSMENT: `${API_PREFIX}/developers/properties/condition-assessment`,
    QUICK_ANALYSIS: `${API_PREFIX}/developers/properties/quick-analysis`,
    HISTORY: `${API_PREFIX}/developers/properties/history`,
  },

  // Feasibility
  FEASIBILITY: {
    BASE: `${API_PREFIX}/feasibility`,
    ANALYZE: `${API_PREFIX}/feasibility/analyze`,
    SCENARIOS: `${API_PREFIX}/feasibility/scenarios`,
    WS: `${WS_BASE_URL}${API_PREFIX}/feasibility/ws`,
  },

  // Finance
  FINANCE: {
    BASE: `${API_PREFIX}/finance`,
    SCENARIOS: `${API_PREFIX}/finance/scenarios`,
    METRICS: `${API_PREFIX}/finance/metrics`,
    CAPITAL_STACK: `${API_PREFIX}/finance/capital-stack`,
  },

  // CAD / Overlay
  CAD: {
    BASE: `${API_PREFIX}/cad`,
    UPLOAD: `${API_PREFIX}/cad/upload`,
    OVERLAY: `${API_PREFIX}/cad/overlay`,
    PIPELINES: `${API_PREFIX}/cad/pipelines`,
  },

  // Market Intelligence
  MARKET: {
    BASE: `${API_PREFIX}/market-intelligence`,
    COMPARABLES: `${API_PREFIX}/market-intelligence/comparables`,
    TRENDS: `${API_PREFIX}/market-intelligence/trends`,
  },

  // Regulatory
  REGULATORY: {
    BASE: `${API_PREFIX}/regulatory`,
    COMPLIANCE: `${API_PREFIX}/regulatory/compliance`,
    SUBMISSIONS: `${API_PREFIX}/regulatory/submissions`,
  },

  // Agents
  AGENTS: {
    BASE: `${API_PREFIX}/agents`,
    PERFORMANCE: `${API_PREFIX}/agents/performance`,
  },

  // Notifications
  NOTIFICATIONS: {
    BASE: `${API_PREFIX}/notifications`,
    MARK_READ: (id: string | number) =>
      `${API_PREFIX}/notifications/${id}/read`,
  },

  // Health
  HEALTH: {
    BASE: '/health',
    READY: '/health/ready',
  },
} as const

// =============================================================================
// FETCH LIMITS
// =============================================================================

export const FETCH_LIMITS = {
  /** Default page size for list endpoints */
  DEFAULT_PAGE_SIZE: 20,
  /** Maximum items per page */
  MAX_PAGE_SIZE: 100,
  /** History fetch limit for condition assessments */
  HISTORY_FETCH_LIMIT: 10,
  /** Maximum file upload size in bytes (10MB) */
  MAX_FILE_SIZE: 10 * 1024 * 1024,
  /** Maximum photos per property */
  MAX_PHOTOS_PER_PROPERTY: 50,
} as const

// =============================================================================
// HTTP HEADERS
// =============================================================================

export const HEADERS = {
  JSON: {
    'Content-Type': 'application/json',
  },
  MULTIPART: {
    'Content-Type': 'multipart/form-data',
  },
} as const

// =============================================================================
// TYPE EXPORTS
// =============================================================================

export type EndpointKey = keyof typeof ENDPOINTS
export type TimeoutKey = keyof typeof TIMEOUTS
