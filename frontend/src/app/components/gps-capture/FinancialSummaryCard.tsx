/**
 * Simplified financial summary display for GPS Capture page
 * Shows revenue, capex, and risk profile overview
 */

import type { DeveloperFinancialSummary } from '../../../api/agents'

interface FinancialSummaryCardProps {
  summary: DeveloperFinancialSummary
  currencySymbol?: string
}

function formatCurrency(value: number | null, symbol: string): string {
  if (value === null) return '-'
  if (value >= 1_000_000) {
    return `${symbol}${(value / 1_000_000).toFixed(1)}M`
  }
  if (value >= 1_000) {
    return `${symbol}${(value / 1_000).toFixed(0)}K`
  }
  return `${symbol}${value.toLocaleString()}`
}

function getRiskBadgeClass(risk: string | null): string {
  if (!risk) return ''
  const normalized = risk.toLowerCase()
  if (normalized.includes('low')) return 'financial-summary-card__risk--low'
  if (normalized.includes('high')) return 'financial-summary-card__risk--high'
  return 'financial-summary-card__risk--medium'
}

export function FinancialSummaryCard({
  summary,
  currencySymbol = 'S$',
}: FinancialSummaryCardProps) {
  const hasData =
    summary.totalEstimatedRevenueSgd != null ||
    summary.totalEstimatedCapexSgd != null ||
    summary.dominantRiskProfile != null

  if (!hasData && summary.notes.length === 0) {
    return (
      <div className="financial-summary-card financial-summary-card--empty">
        <h4 className="financial-summary-card__title">Financial Summary</h4>
        <p className="financial-summary-card__empty">
          No financial data available.
        </p>
      </div>
    )
  }

  return (
    <div className="financial-summary-card">
      <h4 className="financial-summary-card__title">Financial Summary</h4>

      <div className="financial-summary-card__metrics">
        <div className="financial-summary-card__metric">
          <span className="financial-summary-card__metric-label">
            Est. Revenue
          </span>
          <span className="financial-summary-card__metric-value">
            {formatCurrency(summary.totalEstimatedRevenueSgd, currencySymbol)}
          </span>
        </div>
        <div className="financial-summary-card__metric">
          <span className="financial-summary-card__metric-label">
            Est. Capex
          </span>
          <span className="financial-summary-card__metric-value">
            {formatCurrency(summary.totalEstimatedCapexSgd, currencySymbol)}
          </span>
        </div>
        {summary.dominantRiskProfile && (
          <div className="financial-summary-card__metric">
            <span className="financial-summary-card__metric-label">
              Risk Profile
            </span>
            <span
              className={`financial-summary-card__risk ${getRiskBadgeClass(summary.dominantRiskProfile)}`}
            >
              {summary.dominantRiskProfile}
            </span>
          </div>
        )}
      </div>

      {summary.notes.length > 0 && (
        <ul className="financial-summary-card__notes">
          {summary.notes.slice(0, 3).map((note, index) => (
            <li key={index}>{note}</li>
          ))}
        </ul>
      )}
    </div>
  )
}
