/**
 * Simplified asset optimization display for GPS Capture page
 * Shows allocation breakdown and key metrics
 */

import type { DeveloperAssetOptimization } from '../../../api/agents'

interface AssetOptimizationSummaryProps {
  optimizations: DeveloperAssetOptimization[]
  currencySymbol?: string
}

function formatCurrency(value: number | null, symbol: string): string {
  if (value === null) return '-'
  return `${symbol}${value.toLocaleString()}`
}

function formatPercent(value: number | null): string {
  if (value === null) return '-'
  return `${(value * 100).toFixed(1)}%`
}

export function AssetOptimizationSummary({
  optimizations,
  currencySymbol = 'S$',
}: AssetOptimizationSummaryProps) {
  if (optimizations.length === 0) {
    return (
      <div className="asset-optimization-summary asset-optimization-summary--empty">
        <h4 className="asset-optimization-summary__title">
          Asset Optimization
        </h4>
        <p className="asset-optimization-summary__empty">
          No asset optimization data available.
        </p>
      </div>
    )
  }

  const totalRevenue = optimizations.reduce(
    (sum, opt) => sum + (opt.estimatedRevenueSgd ?? 0),
    0,
  )
  const totalCapex = optimizations.reduce(
    (sum, opt) => sum + (opt.estimatedCapexSgd ?? 0),
    0,
  )

  return (
    <div className="asset-optimization-summary">
      <h4 className="asset-optimization-summary__title">Asset Optimization</h4>

      <div className="asset-optimization-summary__totals">
        <div className="asset-optimization-summary__total">
          <span className="asset-optimization-summary__total-label">
            Est. Revenue
          </span>
          <span className="asset-optimization-summary__total-value">
            {formatCurrency(totalRevenue || null, currencySymbol)}
          </span>
        </div>
        <div className="asset-optimization-summary__total">
          <span className="asset-optimization-summary__total-label">
            Est. Capex
          </span>
          <span className="asset-optimization-summary__total-value">
            {formatCurrency(totalCapex || null, currencySymbol)}
          </span>
        </div>
      </div>

      <div className="asset-optimization-summary__list">
        {optimizations.map((opt, index) => (
          <div
            key={`${opt.assetType}-${index}`}
            className="asset-optimization-item"
          >
            <div className="asset-optimization-item__header">
              <span className="asset-optimization-item__type">
                {opt.assetType}
              </span>
              <span className="asset-optimization-item__allocation">
                {formatPercent(opt.allocationPct / 100)}
              </span>
            </div>
            <div className="asset-optimization-item__metrics">
              {opt.allocatedGfaSqm != null && (
                <span className="asset-optimization-item__metric">
                  GFA: {opt.allocatedGfaSqm.toLocaleString()} sqm
                </span>
              )}
              {opt.rentPsmMonth != null && (
                <span className="asset-optimization-item__metric">
                  Rent: {currencySymbol}
                  {opt.rentPsmMonth.toFixed(2)}/sqm/mo
                </span>
              )}
              {opt.riskLevel && (
                <span
                  className={`asset-optimization-item__risk asset-optimization-item__risk--${opt.riskLevel.toLowerCase()}`}
                >
                  {opt.riskLevel}
                </span>
              )}
            </div>
            {opt.notes.length > 0 && (
              <ul className="asset-optimization-item__notes">
                {opt.notes.slice(0, 2).map((note, noteIndex) => (
                  <li key={noteIndex}>{note}</li>
                ))}
              </ul>
            )}
          </div>
        ))}
      </div>
    </div>
  )
}
