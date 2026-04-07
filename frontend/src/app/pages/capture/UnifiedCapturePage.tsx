/**
 * UnifiedCapturePage - Consolidated capture page for Agents and Developers
 *
 * PRE-CAPTURE: Dark map with capture form panel
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
import AddIcon from '@mui/icons-material/Add'

import { useDeveloperMode } from '../../../contexts/useDeveloperMode'
import { useUnifiedCapture } from './hooks/useUnifiedCapture'
import { AgentResultsPanel } from './components/AgentResultsPanel'
import { MissionLog } from './components/MissionLog'
import { VoiceObservationsPanel } from '../site-acquisition/components/VoiceObservationsPanel'
import type { DevelopmentScenario } from '../../../api/agents'
import { useRouterParams } from '../../../router'

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

export function UnifiedCapturePage() {
  const { isDeveloperMode, toggleDeveloperMode } = useDeveloperMode()
  const { projectId } = useRouterParams()

  const {
    latitude,
    longitude,
    address,
    selectedScenarios,
    setLatitude,
    setLongitude,
    setAddress,
    handleScenarioToggle,
    isCapturing,
    isScanning,
    captureError,
    hasResults,
    captureSummary,
    marketSummary,
    marketLoading,
    capturedSites,
    siteAcquisitionResult,
    geocodeError,
    mapContainerRef,
    mapError,
    handleCapture,
    handleNewCapture,
  } = useUnifiedCapture({ isDeveloperMode, projectId })

  const propertyId = isDeveloperMode
    ? (siteAcquisitionResult?.propertyId ?? null)
    : (captureSummary?.propertyId ?? null)

  return (
    <div className="gps-page">
      {/* Full-screen dark map background */}
      <div
        ref={mapContainerRef}
        className={`gps-background-map ${isScanning ? 'scanning' : ''}`}
      />

      {/* Content overlay */}
      <div className="gps-content-overlay">
        {/* Main capture section */}
        <section className="gps-page__summary">
          {/* LEFT PANEL: Capture form */}
          <div className="capture-card-glass">
            {/* Header */}
            <div className="gps-form__header">
              <h2 className="gps-form__title">
                <RadarIcon /> Property Capture
              </h2>
              {hasResults && (
                <button
                  type="button"
                  className="gps-new-capture-btn"
                  onClick={handleNewCapture}
                  title="Start a new capture"
                >
                  <AddIcon /> New
                </button>
              )}
            </div>

            <form className="gps-form" onSubmit={handleCapture}>
              {/* ── Section 1: Location ── */}
              <fieldset className="gps-fieldset">
                <legend className="gps-fieldset__legend">Location</legend>

                {/* Address — primary input, full width */}
                <div className="gps-form__address-row">
                  <input
                    type="text"
                    className="gps-input-ghost gps-input-ghost--lg"
                    placeholder="Click the map or type an address..."
                    value={address}
                    onChange={(e) => setAddress(e.target.value)}
                    aria-label="Address"
                  />
                </div>
                <p className="gps-form__assistive-copy">
                  Address updates the map and coordinates automatically.
                </p>
                {geocodeError && (
                  <p className="gps-error-text">{geocodeError}</p>
                )}

                {/* Coords — compact row */}
                <div className="gps-form__coords-row">
                  <div className="gps-form__coord">
                    <label className="gps-form__inline-label">Lat</label>
                    <input
                      type="text"
                      className="gps-input-ghost gps-input-ghost--sm"
                      placeholder="1.3000"
                      value={latitude}
                      onChange={(e) => setLatitude(e.target.value)}
                      inputMode="decimal"
                    />
                  </div>
                  <div className="gps-form__coord">
                    <label className="gps-form__inline-label">Lng</label>
                    <input
                      type="text"
                      className="gps-input-ghost gps-input-ghost--sm"
                      placeholder="103.8500"
                      value={longitude}
                      onChange={(e) => setLongitude(e.target.value)}
                      inputMode="decimal"
                    />
                  </div>
                </div>
              </fieldset>

              {/* ── Section 2: Scenario Selection ── */}
              <fieldset className="gps-fieldset">
                <legend className="gps-fieldset__legend">Scenario</legend>
                <div className="gps-scenarios-grid">
                  {SCENARIOS.map((scenario) => (
                    <button
                      key={scenario.value}
                      type="button"
                      className={`gps-scenario-tile ${
                        selectedScenarios.includes(scenario.value)
                          ? 'gps-scenario-tile--selected'
                          : ''
                      }`}
                      onClick={() => handleScenarioToggle(scenario.value)}
                      aria-pressed={selectedScenarios.includes(scenario.value)}
                    >
                      {scenario.icon}
                      <span>{scenario.label}</span>
                    </button>
                  ))}
                </div>
              </fieldset>

              {/* ── Section 3: Mode + Action ── */}
              <div className="gps-form__actions">
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

                <button
                  type="submit"
                  className="gps-scan-button"
                  disabled={isCapturing || selectedScenarios.length === 0}
                  title={
                    selectedScenarios.length === 0
                      ? 'Select at least one scenario to capture'
                      : undefined
                  }
                >
                  {isCapturing ? (
                    <>
                      <div className="gps-spinner"></div>
                      <span>Scanning...</span>
                    </>
                  ) : selectedScenarios.length === 0 ? (
                    <>
                      <RadarIcon />
                      <span>Select Scenario</span>
                    </>
                  ) : (
                    <>
                      <RadarIcon />
                      <span>Scan &amp; Analyze</span>
                    </>
                  )}
                </button>
              </div>
            </form>

            {/* Feedback */}
            {captureError && <p className="gps-error">{captureError}</p>}
            {mapError && <p className="gps-warning">{mapError}</p>}

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

            {/* Voice notes */}
            <VoiceObservationsPanel
              propertyId={propertyId}
              latitude={parseFloat(latitude) || undefined}
              longitude={parseFloat(longitude) || undefined}
              disabled={isCapturing}
            />
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
