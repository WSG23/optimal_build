/**
 * Command Bar Component
 *
 * Floating command bar for property capture - AI Studio "Etched Input Strip" pattern.
 * Consolidates address input, coordinates, and capture action into a single bar
 * that floats above the map viewport.
 *
 * Design: Square Cyber-Minimalism with 2px machined edge radius
 */

import type React from 'react'
import { MyLocation, Search } from '@mui/icons-material'
import { IconButton, CircularProgress } from '@mui/material'

import type { DevelopmentScenario } from '../../../../api/siteAcquisition'
import { Button } from '../../../../components/canonical/Button'

// ============================================================================
// Types
// ============================================================================

export interface CommandBarProps {
  // Form state
  address: string
  setAddress: (address: string) => void
  latitude: string
  setLatitude: (lat: string) => void
  longitude: string
  setLongitude: (lon: string) => void
  selectedScenarios: DevelopmentScenario[]
  isCapturing: boolean
  isGeocoding?: boolean

  // Handlers
  onCapture: (e: React.FormEvent) => void
  onAddressBlur?: () => void
  onRecenter?: () => void
}

// ============================================================================
// Component
// ============================================================================

export function CommandBar({
  address,
  setAddress,
  latitude,
  setLatitude,
  longitude,
  setLongitude,
  selectedScenarios,
  isCapturing,
  isGeocoding,
  onCapture,
  onAddressBlur,
  onRecenter,
}: CommandBarProps) {
  const canSubmit = selectedScenarios.length > 0 && !isCapturing

  return (
    <div className="command-bar">
      {/* Target Acquisition Label */}
      <div className="command-bar__label">
        <Search sx={{ fontSize: 16 }} />
        <span>TARGET</span>
      </div>

      {/* Address Input */}
      <div className="command-bar__input-group command-bar__input-group--address">
        <input
          type="text"
          value={address}
          onChange={(e) => setAddress(e.target.value)}
          placeholder="Address or location"
          className="command-bar__input"
          onBlur={() => onAddressBlur?.()}
        />
      </div>

      {/* Coordinate Inputs */}
      <div className="command-bar__input-group command-bar__input-group--coords">
        <input
          type="text"
          value={latitude}
          onChange={(e) => setLatitude(e.target.value)}
          placeholder={isGeocoding ? '...' : 'LAT'}
          disabled={isGeocoding}
          className="command-bar__input command-bar__input--coord"
        />
        <span className="command-bar__coord-separator">,</span>
        <input
          type="text"
          value={longitude}
          onChange={(e) => setLongitude(e.target.value)}
          placeholder={isGeocoding ? '...' : 'LON'}
          disabled={isGeocoding}
          className="command-bar__input command-bar__input--coord"
        />
        {isGeocoding && (
          <CircularProgress
            size={14}
            sx={{
              color: 'var(--ob-color-neon-cyan)',
              ml: 'var(--ob-space-050)',
            }}
          />
        )}
      </div>

      {/* Recenter Button */}
      {onRecenter && (
        <IconButton
          onClick={onRecenter}
          size="small"
          className="command-bar__recenter"
          aria-label="Recenter map"
        >
          <MyLocation sx={{ fontSize: 16 }} />
        </IconButton>
      )}

      {/* Scenario Count Badge */}
      <div className="command-bar__scenario-badge">
        <span className="command-bar__scenario-count">
          {selectedScenarios.length}
        </span>
        <span className="command-bar__scenario-label">SCENARIOS</span>
      </div>

      {/* Capture Button */}
      <Button
        variant="primary"
        size="sm"
        onClick={(e) => {
          e.preventDefault()
          onCapture(e as unknown as React.FormEvent)
        }}
        disabled={!canSubmit}
        className="command-bar__capture-btn"
        title={
          selectedScenarios.length === 0
            ? 'Select at least one scenario to capture'
            : undefined
        }
      >
        {isCapturing
          ? 'CAPTURING...'
          : selectedScenarios.length === 0
            ? 'SELECT SCENARIO'
            : 'CAPTURE'}
      </Button>
    </div>
  )
}
