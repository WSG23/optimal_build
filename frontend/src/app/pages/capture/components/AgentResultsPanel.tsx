/**
 * AgentResultsPanel — Agent-mode results column.
 *
 * Pre-capture: a single instructive empty state describing what will appear.
 * Post-capture: a denser layout that emphasises Quick analysis (primary card),
 * with Market intelligence collapsed into an inline stat row, and Marketing
 * packs rendered as an inline action row. The Developer-mode upsell is a
 * quiet footer rather than another card.
 */

import React, { useState, useCallback } from 'react'
import PictureAsPdfIcon from '@mui/icons-material/PictureAsPdf'
import DescriptionIcon from '@mui/icons-material/Description'
import RequestQuoteIcon from '@mui/icons-material/RequestQuote'
import HomeWorkIcon from '@mui/icons-material/HomeWork'

import {
  generateProfessionalPack,
  type GpsCaptureSummaryWithFeatures,
  type MarketIntelligenceSummary,
  type ProfessionalPackType,
} from '../../../../api/agents'
import { formatScenarioLabel } from '../utils/formatScenario'

interface PackButtonProps {
  packType: ProfessionalPackType
  isLoading: boolean
  disabled: boolean
  onGenerate: (packType: ProfessionalPackType) => void
}
const PACK_META: Record<
  ProfessionalPackType,
  {
    label: string
    icon: React.ComponentType<{ fontSize?: 'inherit' | 'small' }>
  }
> = {
  universal: { label: 'Universal pack', icon: DescriptionIcon },
  investment: { label: 'Investment memo', icon: RequestQuoteIcon },
  sales: { label: 'Sales brief', icon: PictureAsPdfIcon },
  lease: { label: 'Lease brochure', icon: HomeWorkIcon },
}

const PackButton = React.memo(function PackButton({
  packType,
  isLoading,
  disabled,
  onGenerate,
}: PackButtonProps) {
  const meta = PACK_META[packType] ?? {
    label: packType,
    icon: DescriptionIcon,
  }
  const Icon = meta.icon
  return (
    <button
      type="button"
      className="gps-pack-btn"
      disabled={isLoading || disabled}
      onClick={() => onGenerate(packType)}
    >
      {isLoading ? (
        <div className="gps-spinner gps-spinner--xs" />
      ) : (
        <Icon fontSize="small" />
      )}
      <span>{meta.label}</span>
    </button>
  )
})

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
  const [packError, setPackError] = useState<string | null>(null)

  const quickAnalysis = captureSummary?.quickAnalysis ?? null

  const handleGeneratePack = useCallback(
    async (packType: ProfessionalPackType) => {
      if (!captureSummary) return
      try {
        setPackError(null)
        setPackLoadingType(packType)
        await generateProfessionalPack(captureSummary.propertyId, packType)
      } catch (error) {
        console.error('Failed to generate pack', error)
        setPackError(
          error instanceof Error
            ? error.message
            : `Failed to generate ${packType} pack. Please try again.`,
        )
      } finally {
        setPackLoadingType(null)
      }
    },
    [captureSummary],
  )

  // Pre-capture: one quiet, instructive empty state.
  if (!captureSummary) {
    return (
      <aside className="gps-results gps-results--empty" aria-label="Results">
        <p className="gps-results__empty-eyebrow">Results</p>
        <p className="gps-results__empty-headline">
          Run a capture to see analysis here.
        </p>
        <ul className="gps-results__empty-list">
          <li>Quick analysis — first-scenario metrics</li>
          <li>Market intelligence — type, zone, recent transactions</li>
          <li>
            Marketing packs — investment memo, sales brief, lease brochure
          </li>
        </ul>
        {onEnableDeveloperMode && (
          <p className="gps-results__upsell">
            Need 3D preview, feasibility, condition assessment, and
            multi-scenario comparison?{' '}
            <button
              type="button"
              className="gps-results__upsell-link"
              onClick={onEnableDeveloperMode}
            >
              Enable Developer mode
            </button>
          </p>
        )}
      </aside>
    )
  }

  return (
    <aside className="gps-results" aria-label="Results">
      {/* Primary card — Quick analysis */}
      <section className="gps-results__primary" aria-label="Quick analysis">
        <header className="gps-results__primary-header">
          <h3>Quick analysis</h3>
        </header>
        {quickAnalysis && quickAnalysis.scenarios.length > 0 ? (
          <>
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
                                captureSummary.currencySymbol,
                              )}
                            </dd>
                          </div>
                        ))}
                      </dl>
                    )}
                  </li>
                )
              })}
            </ul>
            {quickAnalysis.scenarios.length > 1 && (
              <p className="gps-results__more">
                +{quickAnalysis.scenarios.length - 1} more scenarios available
                in Developer mode
              </p>
            )}
          </>
        ) : (
          <p className="gps-results__inline-empty">
            No quick analysis available for this capture.
          </p>
        )}
      </section>

      {/* Secondary — Market intelligence as a thin stat row */}
      <section className="gps-results__row" aria-label="Market intelligence">
        <p className="gps-results__row-eyebrow">Market intelligence</p>
        {marketLoading ? (
          <div
            className="gps-results__row-loading"
            role="status"
            aria-live="polite"
          >
            <div className="gps-spinner gps-spinner--sm" />
            <span>Loading market data…</span>
          </div>
        ) : marketSummary ? (
          <dl className="gps-results__row-metrics">
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
              <dt>Recent transactions</dt>
              <dd>{extractTransactions(marketSummary.report)}</dd>
            </div>
          </dl>
        ) : (
          <p className="gps-results__row-empty">
            Market data unavailable for this property.
          </p>
        )}
      </section>

      {/* Tertiary — Marketing packs as an action row */}
      <section className="gps-results__row" aria-label="Marketing packs">
        <p className="gps-results__row-eyebrow">Marketing packs</p>
        <div className="gps-pack-grid">
          {PACK_TYPES.map((packType) => (
            <PackButton
              key={packType}
              packType={packType}
              isLoading={packLoadingType === packType}
              disabled={false}
              onGenerate={handleGeneratePack}
            />
          ))}
        </div>
        {packError && (
          <p className="gps-error-text" role="alert" aria-live="assertive">
            {packError}
          </p>
        )}
      </section>

      {/* Footer — Developer-mode invitation, not a card */}
      {onEnableDeveloperMode && (
        <p className="gps-results__upsell">
          Need 3D preview, feasibility, condition assessment, and multi-scenario
          comparison?{' '}
          <button
            type="button"
            className="gps-results__upsell-link"
            onClick={onEnableDeveloperMode}
          >
            Enable Developer mode
          </button>
        </p>
      )}
    </aside>
  )
}

// Helper functions

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
