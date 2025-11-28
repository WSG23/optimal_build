/**
 * Panel for toggling optional developer features in GPS Capture
 * Allows agents to opt-in to enhanced visualization and analysis features
 */

import { useState } from 'react'
import type {
  FeaturePreferences,
  FeatureEntitlements,
} from '../../../hooks/useFeaturePreferences'

interface FeatureTogglePanelProps {
  preferences: FeaturePreferences
  entitlements: FeatureEntitlements
  onToggle: (feature: keyof FeaturePreferences) => void
  onUnlock: (feature: keyof FeaturePreferences) => void
  disabled?: boolean
}

interface FeatureOption {
  key: keyof FeaturePreferences
  label: string
  description: string
}

const FEATURE_OPTIONS: FeatureOption[] = [
  {
    key: 'preview3D',
    label: '3D Preview',
    description: 'Generate interactive 3D visualization of development massing',
  },
  {
    key: 'assetOptimization',
    label: 'Asset Optimization',
    description:
      'View asset allocation analysis and optimization recommendations',
  },
  {
    key: 'financialSummary',
    label: 'Financial Summary',
    description: 'See estimated revenue, capex, and risk profile overview',
  },
  {
    key: 'heritageContext',
    label: 'Heritage Context',
    description: 'Display heritage constraints and conservation requirements',
  },
]

export function FeatureTogglePanel({
  preferences,
  entitlements,
  onToggle,
  onUnlock,
  disabled = false,
}: FeatureTogglePanelProps) {
  const [isExpanded, setIsExpanded] = useState(false)

  const enabledCount = Object.values(preferences).filter(Boolean).length

  return (
    <div className="feature-toggle-panel">
      <button
        type="button"
        className="feature-toggle-panel__header"
        onClick={() => setIsExpanded(!isExpanded)}
        aria-expanded={isExpanded}
      >
        <span className="feature-toggle-panel__title">
          <span className="feature-toggle-panel__icon">
            {isExpanded ? '▼' : '▶'}
          </span>
          Developer Features
          {enabledCount > 0 && (
            <span className="feature-toggle-panel__badge">
              {enabledCount} enabled
            </span>
          )}
        </span>
        <span className="feature-toggle-panel__hint">
          {isExpanded ? 'Click to collapse' : 'Click to expand'}
        </span>
      </button>

      {isExpanded && (
        <div className="feature-toggle-panel__content">
          <p className="feature-toggle-panel__description">
            Enable optional developer features to enhance your property
            analysis. These features require additional processing time.
          </p>
          <div className="feature-toggle-panel__options">
            {FEATURE_OPTIONS.map((option) => (
              <label
                key={option.key}
                className={`feature-toggle-option ${
                  preferences[option.key]
                    ? 'feature-toggle-option--enabled'
                    : ''
                } ${disabled ? 'feature-toggle-option--disabled' : ''}`}
              >
                <input
                  type="checkbox"
                  checked={preferences[option.key]}
                  onChange={() => onToggle(option.key)}
                  disabled={disabled || !entitlements[option.key]}
                  className="feature-toggle-option__checkbox"
                />
                <span className="feature-toggle-option__content">
                  <span className="feature-toggle-option__label">
                    {option.label}
                  </span>
                  <span className="feature-toggle-option__description">
                    {option.description}
                  </span>
                  {!entitlements[option.key] && (
                    <button
                      type="button"
                      className="feature-toggle-option__unlock"
                      onClick={(event) => {
                        event.preventDefault()
                        onUnlock(option.key)
                      }}
                      disabled={disabled}
                    >
                      Unlock
                    </button>
                  )}
                </span>
              </label>
            ))}
          </div>
        </div>
      )}
    </div>
  )
}
