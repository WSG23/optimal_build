/**
 * Optimal Intelligence Card Component
 *
 * AI insight card with gradient background for Site Acquisition sidebar.
 * Displays key insights and provides access to detailed reports.
 *
 * Design Principles:
 * - Square Cyber-Minimalism: 4px radius
 * - Functional Color Language: Cyan gradient for AI/intelligence
 * - Progressive Disclosure: Summary with CTA for details
 */

import { AutoAwesome, ArrowForward } from '@mui/icons-material'

// ============================================================================
// Types
// ============================================================================

export interface OptimalIntelligenceCardProps {
  /** AI-generated insight text */
  insight: string | null
  /** Whether the property has been captured */
  hasProperty: boolean
  /** Callback when "Generate Report" is clicked */
  onGenerateReport?: () => void
  /** Whether report generation is in progress */
  isGenerating?: boolean
}

// ============================================================================
// Component
// ============================================================================

export function OptimalIntelligenceCard({
  insight,
  hasProperty,
  onGenerateReport,
  isGenerating = false,
}: OptimalIntelligenceCardProps) {
  return (
    <div className="optimal-intelligence-card">
      {/* Header */}
      <div className="optimal-intelligence-card__header">
        <AutoAwesome
          sx={{ fontSize: 20, color: 'var(--ob-color-bg-default)' }}
        />
        <span className="optimal-intelligence-card__title">
          Optimal Intelligence
        </span>
      </div>

      {/* Content */}
      <div className="optimal-intelligence-card__content">
        {hasProperty ? (
          insight ? (
            <p className="optimal-intelligence-card__insight">{insight}</p>
          ) : (
            <p className="optimal-intelligence-card__placeholder">
              AI analysis will appear here after property capture and scenario
              evaluation.
            </p>
          )
        ) : (
          <p className="optimal-intelligence-card__placeholder">
            Capture a property to receive AI-powered development insights and
            recommendations.
          </p>
        )}
      </div>

      {/* CTA Button */}
      {hasProperty && onGenerateReport && (
        <button
          type="button"
          onClick={onGenerateReport}
          disabled={isGenerating}
          className="optimal-intelligence-card__cta"
        >
          {isGenerating ? 'Generating...' : 'Generate Detailed Report'}
          <ArrowForward sx={{ fontSize: 16, ml: 'var(--ob-space-050)' }} />
        </button>
      )}
    </div>
  )
}
