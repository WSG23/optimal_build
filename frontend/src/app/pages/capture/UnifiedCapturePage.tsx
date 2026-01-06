/**
 * UnifiedCapturePage - Consolidated capture page for Agents and Developers
 *
 * PRE-CAPTURE (same for all users):
 * - Dark Mapbox 3D map (always dark-v11, never light mode)
 * - Radar sweep animation during scanning
 * - Glass card capture form (left panel)
 * - Developer mode toggle (visible to entitled users)
 *
 * POST-CAPTURE (role-based):
 * - Agent Mode: HUD widgets + Mission Log
 * - Developer Mode: Full workspace (Property Overview, 3D Preview, etc.)
 */

import { lazy, Suspense } from 'react'
import ConstructionIcon from '@mui/icons-material/Construction'
import DomainIcon from '@mui/icons-material/Domain'
import AccountBalanceIcon from '@mui/icons-material/AccountBalance'
import TrendingUpIcon from '@mui/icons-material/TrendingUp'
import MapsHomeWorkIcon from '@mui/icons-material/MapsHomeWork'
import RadarIcon from '@mui/icons-material/Radar'

import { useDeveloperMode } from '../../../contexts/useDeveloperMode'
import { useUnifiedCapture } from './hooks/useUnifiedCapture'
import { AgentResultsPanel } from './components/AgentResultsPanel'
import { MissionLog } from './components/MissionLog'
import type { DevelopmentScenario } from '../../../api/agents'

import 'mapbox-gl/dist/mapbox-gl.css'
import '../../../styles/gps-capture.css'

// Lazy load developer results to avoid bundle bloat for agents
const DeveloperResults = lazy(() =>
  import('./components/DeveloperResults').then((m) => ({
    default: m.DeveloperResults,
  })),
)

// Scenario configuration
const SCENARIOS: {
  value: DevelopmentScenario
  label: string
  icon: React.ReactNode
}[] = [
  { value: 'raw_land', label: 'Raw Land', icon: <ConstructionIcon /> },
  {
    value: 'existing_building',
    label: 'Existing Building',
    icon: <DomainIcon />,
  },
  {
    value: 'heritage_property',
    label: 'Heritage Property',
    icon: <AccountBalanceIcon />,
  },
  {
    value: 'underused_asset',
    label: 'Underused Asset',
    icon: <TrendingUpIcon />,
  },
  {
    value: 'mixed_use_redevelopment',
    label: 'Mixed-Use',
    icon: <MapsHomeWorkIcon />,
  },
]

const JURISDICTIONS = [
  { value: 'SG', label: 'Singapore' },
  { value: 'HK', label: 'Hong Kong' },
  { value: 'NZ', label: 'New Zealand' },
  { value: 'SEA', label: 'Southeast Asia' },
  { value: 'TOR', label: 'Toronto' },
]

export function UnifiedCapturePage() {
  const { isDeveloperMode, toggleDeveloperMode } = useDeveloperMode()

  const {
    // Form state
    latitude,
    longitude,
    address,
    jurisdictionCode,
    selectedScenarios,
    setLatitude,
    setLongitude,
    setAddress,
    setJurisdictionCode,
    handleScenarioToggle,

    // Capture state
    isCapturing,
    isScanning,
    captureError,

    // Agent results
    captureSummary,
    marketSummary,
    marketLoading,
    capturedSites,

    // Developer results
    siteAcquisitionResult,

    // Geocoding
    geocodeError,
    handleForwardGeocode,
    handleReverseGeocode,

    // Map
    mapContainerRef,
    mapError,

    // Handlers
    handleCapture,
  } = useUnifiedCapture({ isDeveloperMode })

  const hasResults = isDeveloperMode
    ? siteAcquisitionResult !== null
    : captureSummary !== null

  return (
    <div className="gps-page">
      {/* Full-screen dark Mapbox background */}
      <div
        ref={mapContainerRef}
        className={`gps-background-map ${isScanning ? 'scanning' : ''}`}
      />

      {/* Content overlay */}
      <div className="gps-content-overlay">
        {/* Main capture section */}
        <section className="gps-page__summary">
          {/* LEFT PANEL: Glass capture form */}
          <div className="capture-card-glass">
            <h2 className="gps-form__title">
              <RadarIcon /> Property Capture
            </h2>

            <form className="gps-form" onSubmit={handleCapture}>
              {/* Address input with geocode buttons */}
              <div className="gps-form__group">
                <label className="gps-form__label">Address</label>
                <div className="gps-form__address-row">
                  <input
                    type="text"
                    className="gps-input-ghost"
                    placeholder="Enter address..."
                    value={address}
                    onChange={(e) => setAddress(e.target.value)}
                  />
                  <div className="gps-form__address-actions">
                    <button
                      type="button"
                      className="gps-geocode-btn"
                      onClick={handleForwardGeocode}
                      title="Geocode address"
                    >
                      →
                    </button>
                    <button
                      type="button"
                      className="gps-geocode-btn"
                      onClick={handleReverseGeocode}
                      title="Reverse geocode"
                    >
                      ←
                    </button>
                  </div>
                </div>
                {geocodeError && (
                  <p className="gps-error-text">{geocodeError}</p>
                )}
              </div>

              {/* Coordinate inputs */}
              <div className="gps-form__row">
                <div className="gps-form__group gps-form__group--half">
                  <label className="gps-form__label">Latitude</label>
                  <input
                    type="text"
                    className="gps-input-ghost"
                    placeholder="1.3000"
                    value={latitude}
                    onChange={(e) => setLatitude(e.target.value)}
                  />
                </div>
                <div className="gps-form__group gps-form__group--half">
                  <label className="gps-form__label">Longitude</label>
                  <input
                    type="text"
                    className="gps-input-ghost"
                    placeholder="103.8500"
                    value={longitude}
                    onChange={(e) => setLongitude(e.target.value)}
                  />
                </div>
              </div>

              {/* Jurisdiction selector */}
              <div className="gps-form__group">
                <label className="gps-form__label">Jurisdiction</label>
                <select
                  className="gps-select-ghost"
                  value={jurisdictionCode}
                  onChange={(e) => setJurisdictionCode(e.target.value)}
                >
                  {JURISDICTIONS.map((j) => (
                    <option key={j.value} value={j.value}>
                      {j.label}
                    </option>
                  ))}
                </select>
              </div>

              {/* Scenario tiles */}
              <div className="gps-form__group">
                <label className="gps-form__label">Mission Scenarios</label>
                <div className="gps-scenarios-grid">
                  {SCENARIOS.map((scenario) => (
                    <button
                      key={scenario.value}
                      type="button"
                      className={`gps-scenario-tile ${
                        selectedScenarios.includes(scenario.value)
                          ? 'selected'
                          : ''
                      }`}
                      onClick={() => handleScenarioToggle(scenario.value)}
                    >
                      {scenario.icon}
                      <span>{scenario.label}</span>
                    </button>
                  ))}
                </div>
              </div>

              {/* Developer mode toggle */}
              <div className="gps-form__group">
                <label className="gps-developer-mode-toggle">
                  <input
                    type="checkbox"
                    checked={isDeveloperMode}
                    onChange={toggleDeveloperMode}
                  />
                  <span>Developer Mode</span>
                  <span className="gps-developer-mode-hint">
                    {isDeveloperMode ? 'Full workspace' : 'HUD only'}
                  </span>
                </label>
              </div>

              {/* Scan button */}
              <button
                type="submit"
                className="gps-scan-button"
                disabled={isCapturing || selectedScenarios.length === 0}
              >
                {isCapturing ? (
                  <>
                    <div className="gps-spinner"></div>
                    <span>Scanning...</span>
                  </>
                ) : (
                  <>
                    <RadarIcon />
                    <span>Scan &amp; Analyze</span>
                  </>
                )}
              </button>
            </form>

            {/* Capture error */}
            {captureError && <p className="gps-error">{captureError}</p>}

            {/* Map error */}
            {mapError && <p className="gps-warning">{mapError}</p>}

            {/* Capture confirmation */}
            {hasResults && !isDeveloperMode && captureSummary && (
              <div className="gps-capture-meta">
                <p>
                  Target Locked:{' '}
                  <strong>{captureSummary.address.fullAddress}</strong>
                </p>
                <p>
                  Captured:{' '}
                  {new Date(captureSummary.timestamp).toLocaleTimeString()}
                </p>
              </div>
            )}
          </div>

          {/* RIGHT PANEL: Role-based results */}
          {!isDeveloperMode && (
            <AgentResultsPanel
              captureSummary={captureSummary}
              marketSummary={marketSummary}
              marketLoading={marketLoading}
              onEnableDeveloperMode={toggleDeveloperMode}
            />
          )}
        </section>

        {/* Developer workspace (below map section) */}
        {isDeveloperMode && siteAcquisitionResult && (
          <section className="gps-page__developer-workspace">
            <Suspense
              fallback={
                <div className="gps-panel__loading">
                  Loading developer workspace...
                </div>
              }
            >
              <DeveloperResults
                result={siteAcquisitionResult}
                selectedScenarios={selectedScenarios}
              />
            </Suspense>
          </section>
        )}

        {/* Mission Log (both modes) */}
        <MissionLog capturedSites={capturedSites} />
      </div>
    </div>
  )
}
