import { useMemo } from 'react'

import type { StoredAssetOptimization, FinancialSummary } from '../types'

interface AssetMixViewProps {
  capturedAssetMix: StoredAssetOptimization[]
  capturedFinancialSummary: FinancialSummary | null
  numberFormatter: Intl.NumberFormat
  oneDecimalFormatter: Intl.NumberFormat
}

export function AssetMixView({
  capturedAssetMix,
  capturedFinancialSummary,
  numberFormatter,
  oneDecimalFormatter,
}: AssetMixViewProps) {
  const formatRow = useMemo(
    () => (plan: StoredAssetOptimization) => {
      const parts: string[] = [`${numberFormatter.format(plan.allocationPct)}%`]
      if (plan.allocatedGfaSqm != null) {
        parts.push(`${numberFormatter.format(Math.round(plan.allocatedGfaSqm))} sqm`)
      }
      if (plan.niaEfficiency != null) {
        parts.push(`${oneDecimalFormatter.format(plan.niaEfficiency * 100)}% NIA`)
      }
      if (plan.targetFloorHeightM != null) {
        parts.push(`${oneDecimalFormatter.format(plan.targetFloorHeightM)} m floors`)
      }
      if (plan.parkingRatioPer1000Sqm != null) {
        parts.push(
          `${oneDecimalFormatter.format(plan.parkingRatioPer1000Sqm)} lots / 1000 sqm`,
        )
      }
      if (plan.estimatedRevenueSgd != null && plan.estimatedRevenueSgd > 0) {
        parts.push(
          `Rev ≈ $${oneDecimalFormatter.format(plan.estimatedRevenueSgd / 1_000_000)}M`,
        )
      }
      if (plan.estimatedCapexSgd != null && plan.estimatedCapexSgd > 0) {
        parts.push(
          `CAPEX ≈ $${oneDecimalFormatter.format(plan.estimatedCapexSgd / 1_000_000)}M`,
        )
      }
      if (plan.riskLevel) {
        const risk = `${plan.riskLevel.charAt(0).toUpperCase()}${plan.riskLevel.slice(1)}`
        parts.push(
          `${risk} risk${
            plan.absorptionMonths
              ? ` · ~${numberFormatter.format(plan.absorptionMonths)}m absorption`
              : ''
          }`,
        )
      }
      return parts.join(' • ')
    },
    [numberFormatter, oneDecimalFormatter],
  )

  if (!capturedAssetMix.length) {
    return null
  }

  return (
    <section className="feasibility-asset-mix" data-testid="asset-mix">
      <h3>Captured asset mix</h3>
      <dl>
        {capturedAssetMix.map((plan) => (
          <div key={plan.assetType} className="feasibility-asset-mix__item">
            <dt>{plan.assetType}</dt>
            <dd>{formatRow(plan)}</dd>
            {plan.notes && plan.notes.length > 0 && (
              <p className="feasibility-asset-mix__note">{plan.notes[0]}</p>
            )}
          </div>
        ))}
      </dl>
      {capturedFinancialSummary ? (
        <div className="feasibility-asset-mix__summary">
          <h4>Financial snapshot</h4>
          <ul>
            <li>
              Total revenue:{' '}
              {capturedFinancialSummary.totalEstimatedRevenueSgd != null
                ? `$${oneDecimalFormatter.format(
                    capturedFinancialSummary.totalEstimatedRevenueSgd / 1_000_000,
                  )}M`
                : '—'}
            </li>
            <li>
              Total capex:{' '}
              {capturedFinancialSummary.totalEstimatedCapexSgd != null
                ? `$${oneDecimalFormatter.format(
                    capturedFinancialSummary.totalEstimatedCapexSgd / 1_000_000,
                  )}M`
                : '—'}
            </li>
            <li>
              Dominant risk: {capturedFinancialSummary.dominantRiskProfile ?? '—'}
            </li>
          </ul>
          {capturedFinancialSummary.notes.length > 0 && (
            <p className="feasibility-asset-mix__note">
              {capturedFinancialSummary.notes[0]}
            </p>
          )}
        </div>
      ) : null}
    </section>
  )
}
