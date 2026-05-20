/**
 * UnifiedCapturePage - Consolidated capture page for Agents and Developers
 *
 * Pre-capture: map background with capture form panel.
 * Post-capture (role-based):
 *   Agent mode    — Quick analysis + market intelligence + marketing packs.
 *   Developer mode — Full workspace (Property Overview, 3D Preview, etc.).
 */

import { lazy, Suspense, useEffect, useMemo, useRef } from 'react'
import RadarIcon from '@mui/icons-material/Radar'
import AddIcon from '@mui/icons-material/Add'
import MapIcon from '@mui/icons-material/Map'
import ErrorOutlineIcon from '@mui/icons-material/ErrorOutline'
import CloseIcon from '@mui/icons-material/Close'
import CheckIcon from '@mui/icons-material/Check'

function detectShortcutKeyLabel(): 'Cmd' | 'Ctrl' {
  if (typeof navigator === 'undefined') {
    return 'Ctrl'
  }
  const nav = navigator as Navigator & {
    userAgentData?: { platform?: string }
  }
  const ua = nav.userAgentData?.platform ?? nav.platform ?? ''
  return /mac|iphone|ipad|ipod/i.test(ua) ? 'Cmd' : 'Ctrl'
}

import { useDeveloperMode } from '../../../contexts/useDeveloperMode'
import { useUnifiedCapture } from './hooks/useUnifiedCapture'
import { AgentResultsPanel } from './components/AgentResultsPanel'
import { MissionLog } from './components/MissionLog'
import { VoiceObservationsPanel } from '../site-acquisition/components/VoiceObservationsPanel'
import { DEFAULT_SCENARIO_ORDER } from '../../../api/siteAcquisition'
import { useRouterParams } from '../../../router'

import '../../../styles/gps-capture.css'

// Lazy load developer results to avoid bundle bloat for agents
const DeveloperResults = lazy(() =>
  import('./components/DeveloperResults').then((m) => ({
    default: m.DeveloperResults,
  })),
)

export function UnifiedCapturePage() {
  const { isDeveloperMode, toggleDeveloperMode } = useDeveloperMode()
  const { projectId } = useRouterParams()

  const {
    latitude,
    longitude,
    analysisLatitude,
    analysisLongitude,
    address,
    selectedScenarios,
    setAddress,
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
    isGeocoding,
    coordinateSourceLabel,
    mapCoordinateSourceLabel,
    mapContainerRef,
    addressInputRef,
    autocompleteHostRef,
    mapError,
    isMapLoading,
    targetAcquired,
    handleCapture,
    handleNewCapture,
    handleCancelCapture,
  } = useUnifiedCapture({ isDeveloperMode, projectId })

  const propertyId = isDeveloperMode
    ? (siteAcquisitionResult?.propertyId ?? null)
    : (captureSummary?.propertyId ?? null)
  const effectiveSelectedScenarios =
    selectedScenarios.length > 0
      ? selectedScenarios
      : [...DEFAULT_SCENARIO_ORDER]

  const formRef = useRef<HTMLFormElement | null>(null)
  const targetAcquiredRef = useRef<HTMLDivElement | null>(null)
  const shortcutKey = useMemo(detectShortcutKeyLabel, [])
  const shouldShowMapPreview =
    Boolean(latitude || longitude || mapCoordinateSourceLabel) &&
    mapCoordinateSourceLabel !== 'Browser location'
  const visibleCaptureError =
    captureError && captureError !== geocodeError ? captureError : null

  // Focus the target-acquired confirmation when it appears
  useEffect(() => {
    if (targetAcquired && targetAcquiredRef.current) {
      targetAcquiredRef.current.focus()
    }
  }, [targetAcquired])

  // Keyboard shortcuts: Ctrl+Enter to scan, Escape to cancel
  useEffect(() => {
    const handler = (e: KeyboardEvent) => {
      if ((e.ctrlKey || e.metaKey) && e.key === 'Enter') {
        if (isCapturing) return
        e.preventDefault()
        formRef.current?.requestSubmit()
      }
      if (e.key === 'Escape' && isCapturing) {
        e.preventDefault()
        handleCancelCapture()
      }
    }
    document.addEventListener('keydown', handler)
    return () => document.removeEventListener('keydown', handler)
  }, [isCapturing, handleCancelCapture])

  return (
    <div className="gps-page">
      {/* Full-screen dark map background */}
      <div
        ref={mapContainerRef}
        className={`gps-background-map ${isScanning ? 'scanning' : ''}`}
      >
        {/* Map loading / error fallback — rendered inside the map container,
            Google Maps will replace these children when it initializes */}
        {isMapLoading && !mapError && (
          <div className="gps-map-fallback">
            <MapIcon className="gps-map-fallback__icon" />
            <span className="gps-map-fallback__text">Loading map…</span>
            <div className="gps-spinner" />
          </div>
        )}
        {mapError && (
          <div className="gps-map-fallback gps-map-fallback--error">
            <ErrorOutlineIcon className="gps-map-fallback__icon" />
            <span className="gps-map-fallback__text">{mapError}</span>
            <span className="gps-map-fallback__hint">
              You can still enter coordinates manually in the form.
            </span>
          </div>
        )}
      </div>

      {/* Content overlay */}
      <div className="gps-content-overlay">
        {/* Main capture section */}
        <section className="gps-page__summary">
          {/* LEFT PANEL: Capture form */}
          <div className="gps-capture-card">
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

            <form
              ref={formRef}
              className="gps-form"
              onSubmit={handleCapture}
              noValidate
            >
              {/* ── Section 1: Location ── */}
              <fieldset className="gps-fieldset">
                <legend className="gps-fieldset__legend">Location</legend>

                {/* Address — Places API (New) PlaceAutocompleteElement.
                    Renders its own input via Web Component; we host it here
                    and style it via `::part(input)` in gps-capture.css.
                    The hidden legacy input remains for tests / a11y label-for
                    associations and is kept in sync via the hook. */}
                <div className="gps-form__address-row">
                  {/* Hidden legacy input retained as the canonical
                      controlled-input surface for tests; the visible
                      address field is the web component below, which
                      carries its own accessible name via aria-label on
                      the host. aria-hidden here prevents AT from seeing
                      a duplicate "Address" label. */}
                  <input
                    ref={addressInputRef}
                    type="text"
                    aria-hidden="true"
                    tabIndex={-1}
                    value={address}
                    onChange={(e) => setAddress(e.target.value)}
                    className="gps-form__hidden-input"
                  />
                  <div
                    ref={autocompleteHostRef}
                    role="group"
                    aria-label="Address"
                    className="gps-form__autocomplete-host gps-input-ghost gps-input-ghost--lg"
                    data-testid="address-autocomplete-host"
                  />
                  {isGeocoding && (
                    <span className="gps-form__geocoding-indicator" />
                  )}
                </div>
                <p className="gps-form__assistive-copy">
                  {isGeocoding
                    ? 'Resolving address...'
                    : 'Address updates the map and coordinates automatically.'}
                </p>
                {geocodeError && (
                  <p className="gps-error-text">{geocodeError}</p>
                )}

                <p className="gps-form__coordinate-heading">
                  Analysis coordinates
                </p>
                <div className="gps-form__coords-row">
                  <div className="gps-form__coord">
                    <label
                      className="gps-form__inline-label"
                      htmlFor="capture-lat"
                    >
                      Lat
                    </label>
                    <input
                      id="capture-lat"
                      type="text"
                      className="gps-input-ghost gps-input-ghost--sm"
                      placeholder="Pending"
                      value={analysisLatitude}
                      readOnly
                      inputMode="decimal"
                    />
                  </div>
                  <div className="gps-form__coord">
                    <label
                      className="gps-form__inline-label"
                      htmlFor="capture-lng"
                    >
                      Lng
                    </label>
                    <input
                      id="capture-lng"
                      type="text"
                      className="gps-input-ghost gps-input-ghost--sm"
                      placeholder="Pending"
                      value={analysisLongitude}
                      readOnly
                      inputMode="decimal"
                    />
                  </div>
                </div>
                <p className="gps-form__coordinate-source">
                  Used for zoning:{' '}
                  <span>{coordinateSourceLabel ?? 'Not resolved yet'}</span>
                </p>
                {shouldShowMapPreview && (
                  <p className="gps-form__coordinate-source">
                    Map preview:{' '}
                    <span>
                      {latitude && longitude ? `${latitude}, ${longitude}` : ''}
                      {mapCoordinateSourceLabel
                        ? `${latitude && longitude ? ' · ' : ''}${mapCoordinateSourceLabel}`
                        : ''}
                    </span>
                  </p>
                )}
              </fieldset>

              {/* ── Section 2: Mode + Action ── */}
              <div className="gps-form__actions">
                <label className="gps-developer-mode-toggle">
                  <input
                    type="checkbox"
                    checked={isDeveloperMode}
                    onChange={toggleDeveloperMode}
                  />
                  <span className="gps-developer-mode-toggle__label">
                    <span className="gps-developer-mode-toggle__title">
                      Developer mode
                    </span>
                    <span className="gps-developer-mode-toggle__desc">
                      {isDeveloperMode
                        ? 'On — 3D preview, feasibility, condition assessment, multi-scenario comparison.'
                        : 'Off — runs quick analysis only. Enable for 3D preview, feasibility, condition assessment, multi-scenario comparison.'}
                    </span>
                  </span>
                </label>

                {isCapturing ? (
                  <button
                    type="button"
                    className="gps-scan-button gps-scan-button--cancel"
                    onClick={handleCancelCapture}
                    aria-label={`Cancel capture (${shortcutKey === 'Cmd' ? 'Esc' : 'Escape'})`}
                  >
                    <CloseIcon />
                    <span>Cancel</span>
                  </button>
                ) : (
                  <button
                    type="submit"
                    className="gps-scan-button"
                    aria-keyshortcuts={`${shortcutKey === 'Cmd' ? 'Meta' : 'Control'}+Enter`}
                  >
                    <RadarIcon />
                    <span>Scan &amp; Analyze</span>
                    <kbd className="gps-kbd">{shortcutKey}+Enter</kbd>
                  </button>
                )}
              </div>
            </form>

            {/* Feedback */}
            {visibleCaptureError && (
              <p className="gps-error-text" role="alert">
                {visibleCaptureError}
              </p>
            )}

            {/* Capture confirmation — auto-dismisses after 3s */}
            {targetAcquired && (
              <div
                ref={targetAcquiredRef}
                className="gps-capture-confirm"
                role="status"
                aria-live="polite"
                tabIndex={-1}
              >
                <CheckIcon className="gps-capture-confirm__icon" />
                <div className="gps-capture-confirm__content">
                  <span className="gps-capture-confirm__label">Captured</span>
                  <span className="gps-capture-confirm__address">
                    {targetAcquired}
                  </span>
                </div>
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
                selectedScenarios={effectiveSelectedScenarios}
              />
            </Suspense>
          </section>
        )}

        <MissionLog capturedSites={capturedSites} />
      </div>
    </div>
  )
}
