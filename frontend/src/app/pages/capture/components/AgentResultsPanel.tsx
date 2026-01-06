/**
 * AgentResultsPanel - HUD widgets for Agent mode post-capture results
 *
 * Displays three floating cards on the right panel:
 * - Quick Analysis: First scenario metrics
 * - Market Intelligence: Property type, zone, transactions
 * - Marketing Packs: PDF/document download buttons
 *
 * Also shows an upsell card to encourage Developer mode upgrade.
 */

import { useState, useCallback } from 'react'
import LockIcon from '@mui/icons-material/Lock'
import PictureAsPdfIcon from '@mui/icons-material/PictureAsPdf'
import DescriptionIcon from '@mui/icons-material/Description'
import RocketLaunchIcon from '@mui/icons-material/RocketLaunch'

import {
  generateProfessionalPack,
  type GpsCaptureSummaryWithFeatures,
  type MarketIntelligenceSummary,
  type ProfessionalPackType,
  type DevelopmentScenario,
} from '../../../../api/agents'
import { Button } from '../../../../components/canonical/Button'

export interface AgentResultsPanelProps {
  captureSummary: GpsCaptureSummaryWithFeatures | null
  marketSummary: MarketIntelligenceSummary | null
  marketLoading: boolean
  onEnableDeveloperMode?: () => void
}

const PACK_TYPES: ProfessionalPackType[] = [
  'universal',
  'investment',
  'sales',
  'lease',
]

export function AgentResultsPanel({
  captureSummary,
  marketSummary,
  marketLoading,
  onEnableDeveloperMode,
}: AgentResultsPanelProps) {
  const [packLoadingType, setPackLoadingType] =
    useState<ProfessionalPackType | null>(null)

  const quickAnalysis = captureSummary?.quickAnalysis ?? null

  const handleGeneratePack = useCallback(
    async (packType: ProfessionalPackType) => {
      if (!captureSummary) return
      try {
        setPackLoadingType(packType)
        await generateProfessionalPack(captureSummary.propertyId, packType)
      } catch (error) {
        console.error('Failed to generate pack', error)
      } finally {
        setPackLoadingType(null)
      }
    },
    [captureSummary],
  )

  return (
    <div className="gps-hud-group">
      {/* Widget 1: Quick Analysis */}
      <div className={`gps-hud-card ${!quickAnalysis ? 'locked' : ''}`}>
        <h3>
          Quick Analysis
          {!quickAnalysis && <LockIcon fontSize="small" />}
        </h3>

        {quickAnalysis ? (
          <div className="gps-hud-content">
            <ul className="gps-panel__list">
              {quickAnalysis.scenarios.slice(0, 1).map((scenario) => {
                const displayMetrics = Object.entries(scenario.metrics)
                  .filter(([key]) => key !== 'accuracy_bands')
                  .slice(0, 3)
                return (
                  <li key={scenario.scenario}>
                    <div className="gps-panel__headline">
                      <strong>{formatScenarioLabel(scenario.scenario)}</strong>
                    </div>
                    {displayMetrics.length > 0 && (
                      <dl className="gps-panel__metrics">
                        {displayMetrics.map(([k, v]) => (
                          <div key={k}>
                            <dt>{humanizeMetricKey(k)}</dt>
                            <dd>
                              {formatMetricValue(
                                v,
                                k,
                                captureSummary?.currencySymbol,
                              )}
                            </dd>
                          </div>
                        ))}
                      </dl>
                    )}
                  </li>
                )
              })}
              {quickAnalysis.scenarios.length > 1 && (
                <p className="gps-hud-more-scenarios">
                  + {quickAnalysis.scenarios.length - 1} more scenarios
                </p>
              )}
            </ul>
          </div>
        ) : (
          <div className="gps-hud-locked-overlay">
            <span>Awaiting Scan</span>
          </div>
        )}
      </div>

      {/* Widget 2: Market Intelligence */}
      <div className={`gps-hud-card ${!marketSummary ? 'locked' : ''}`}>
        <h3>
          Market Intelligence
          {!marketSummary && <LockIcon fontSize="small" />}
        </h3>
        {marketLoading ? (
          <div className="gps-hud-loading">
            <div className="gps-spinner gps-spinner--sm"></div>
            Decrypting market data...
          </div>
        ) : marketSummary ? (
          <div className="gps-hud-content">
            <dl className="gps-panel__metrics">
              <div>
                <dt>Type</dt>
                <dd>
                  {extractReportValue(marketSummary.report, 'property_type')}
                </dd>
              </div>
              <div>
                <dt>Zone</dt>
                <dd>{extractReportValue(marketSummary.report, 'location')}</dd>
              </div>
              <div>
                <dt>Trans</dt>
                <dd>{extractTransactions(marketSummary.report)} recent</dd>
              </div>
            </dl>
          </div>
        ) : (
          <div className="gps-hud-locked-overlay">
            <span>Downlink Offline</span>
          </div>
        )}
      </div>

      {/* Widget 3: Marketing Packs */}
      <div className={`gps-hud-card ${!captureSummary ? 'locked' : ''}`}>
        <h3>
          Marketing Packs
          {!captureSummary && <LockIcon fontSize="small" />}
        </h3>
        <div className="gps-pack-grid gps-hud-content">
          {PACK_TYPES.map((packType) => (
            <button
              key={packType}
              type="button"
              className="gps-pack-btn"
              disabled={packLoadingType === packType || !captureSummary}
              onClick={() => handleGeneratePack(packType)}
            >
              {packLoadingType === packType ? (
                <div className="gps-spinner gps-spinner--xs"></div>
              ) : packType === 'investment' || packType === 'sales' ? (
                <PictureAsPdfIcon />
              ) : (
                <DescriptionIcon />
              )}
              <span>{formatPackLabel(packType).split(' ')[0]}</span>
            </button>
          ))}
        </div>
      </div>

      {/* Upsell Card */}
      {onEnableDeveloperMode && (
        <div className="gps-hud-card gps-hud-card--upsell">
          <h3>
            <RocketLaunchIcon fontSize="small" /> Unlock More
          </h3>
          <p className="gps-hud-upsell-text">
            Get 3D previews, due diligence checklists, condition assessments,
            and multi-scenario analysis with Developer Mode.
          </p>
          <Button
            variant="primary"
            size="sm"
            className="gps-hud-upsell-btn"
            onClick={onEnableDeveloperMode}
          >
            Enable Developer Mode
          </Button>
        </div>
      )}
    </div>
  )
}

// Helper functions (ported from GpsCapturePage)

function formatScenarioLabel(value: DevelopmentScenario) {
  switch (value) {
    case 'raw_land':
      return 'Raw land'
    case 'existing_building':
      return 'Existing building'
    case 'heritage_property':
      return 'Heritage property'
    case 'underused_asset':
      return 'Underused asset'
    case 'mixed_use_redevelopment':
      return 'Mixed-use redevelopment'
    default:
      return value
  }
}

function formatPackLabel(value: ProfessionalPackType) {
  switch (value) {
    case 'universal':
      return 'Universal pack'
    case 'investment':
      return 'Investment memo'
    case 'sales':
      return 'Sales brief'
    case 'lease':
      return 'Lease brochure'
    default:
      return value
  }
}

function humanizeMetricKey(key: string) {
  return key.replace(/_/g, ' ').replace(/\b\w/g, (char) => char.toUpperCase())
}

function formatMetricValue(
  value: unknown,
  metricKey?: string,
  currencySymbol?: string,
) {
  if (value === null || value === undefined) {
    return '—'
  }
  if (typeof value === 'number') {
    const formattedNumber = Number.isInteger(value)
      ? value.toLocaleString()
      : value.toLocaleString(undefined, {
          minimumFractionDigits: 2,
          maximumFractionDigits: 2,
        })

    const isCountField =
      metricKey &&
      (metricKey.includes('count') ||
        metricKey.includes('number') ||
        metricKey.includes('quantity') ||
        metricKey.includes('units'))

    const hasFinancialKeyword =
      metricKey &&
      !isCountField &&
      (metricKey.includes('price') ||
        metricKey.includes('noi') ||
        metricKey.includes('valuation') ||
        metricKey.includes('capex') ||
        metricKey.includes('rent') ||
        metricKey.includes('cost') ||
        metricKey.includes('value') ||
        metricKey.includes('revenue') ||
        metricKey.includes('income'))

    if (currencySymbol && hasFinancialKeyword) {
      return `${currencySymbol}${formattedNumber}`
    }
    return formattedNumber
  }
  return String(value)
}

function extractReportValue(report: Record<string, unknown>, key: string) {
  const value = report[key]
  return typeof value === 'string' && value.trim() !== '' ? value : '—'
}

function extractTransactions(report: Record<string, unknown>) {
  const comparables = report.comparables_analysis
  if (
    comparables &&
    typeof comparables === 'object' &&
    'transaction_count' in comparables
  ) {
    const value = (comparables as Record<string, unknown>).transaction_count
    if (typeof value === 'number') {
      return value.toLocaleString()
    }
  }
  return '—'
}
