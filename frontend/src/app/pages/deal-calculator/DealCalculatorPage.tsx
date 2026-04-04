import React, { startTransition, useMemo, useState } from 'react'

import {
  evaluateDealCalculator,
  type DealCalculatorResult,
} from '../../../api/dealCalculator'
import type { FinanceScenarioInput } from '../../../api/finance'
import type { ExternalSourceMetadata } from '../../../api/externalSources'
import { saveQuickScreenFinanceDraft } from '../../../modules/finance/quickScreenDraft'

type FormState = {
  projectName: string
  address: string
  landUse: string
  zoneCode: string
  siteAreaSqm: string
  allowablePlotRatio: string
  currentGfaSqm: string
  targetGrossFloorAreaSqm: string
  buildingHeightMeters: string
  equityPct: string
  debtPct: string
  annualInterestRatePct: string
  discountRatePct: string
  exitCapRatePct: string
  saleCostPct: string
  holdYears: string
}

const INITIAL_STATE: FormState = {
  projectName: 'Singapore quick screen',
  address: '1 Marina Boulevard, Singapore',
  landUse: 'residential',
  zoneCode: 'R',
  siteAreaSqm: '5000',
  allowablePlotRatio: '3.5',
  currentGfaSqm: '9000',
  targetGrossFloorAreaSqm: '14000',
  buildingHeightMeters: '45',
  equityPct: '40',
  debtPct: '60',
  annualInterestRatePct: '4.8',
  discountRatePct: '8',
  exitCapRatePct: '4',
  saleCostPct: '2',
  holdYears: '3',
}

function parseOptionalNumber(value: string): number | undefined {
  const trimmed = value.trim()
  if (!trimmed) {
    return undefined
  }
  const parsed = Number(trimmed)
  return Number.isFinite(parsed) ? parsed : undefined
}

function formatCurrency(value: number | null | undefined) {
  if (value == null) {
    return 'Pending'
  }
  return new Intl.NumberFormat('en-SG', {
    style: 'currency',
    currency: 'SGD',
    maximumFractionDigits: 0,
  }).format(value)
}

function formatMetric(value: number | null | undefined, digits = 2) {
  if (value == null) {
    return 'Pending'
  }
  return Number(value).toFixed(digits)
}

function currentQuarterLabel(date: Date) {
  return `${date.getFullYear()}-Q${Math.floor(date.getMonth() / 3) + 1}`
}

function pctToRate(value: string, fallback: string) {
  const parsed = parseOptionalNumber(value)
  if (parsed == null) {
    return fallback
  }
  return (parsed / 100).toFixed(4)
}

function buildQuickScreenScenario(
  form: FormState,
  result: DealCalculatorResult,
): FinanceScenarioInput {
  const now = new Date()
  const holdYears = Math.max(1, parseOptionalNumber(form.holdYears) ?? 3)
  const totalCapex = Math.max(result.financeSummary.totalCapexSgd ?? 0, 0)
  const annualNoi = Math.max(result.financeSummary.totalAnnualNoiSgd ?? 0, 0)
  const annualDebtService = Math.max(
    result.financeSummary.annualDebtServiceSgd ?? 0,
    0,
  )
  const exitValue = Math.max(result.financeSummary.estimatedExitValueSgd ?? 0, 0)
  const saleCostRate = (parseOptionalNumber(form.saleCostPct) ?? 2) / 100
  const finalDistribution = annualNoi + exitValue * (1 - saleCostRate)
  const cashFlows = Array.from({ length: holdYears + 1 }, (_, index) => {
    if (index === 0) {
      return `-${Math.max(totalCapex, 1).toFixed(2)}`
    }
    if (index === holdYears) {
      return finalDistribution.toFixed(2)
    }
    return annualNoi.toFixed(2)
  })

  const dscrIncomes = Array.from({ length: holdYears }, () =>
    annualNoi.toFixed(2),
  )
  const dscrDebtService = Array.from({ length: holdYears }, () =>
    annualDebtService.toFixed(2),
  )
  const debtPct = parseOptionalNumber(form.debtPct) ?? 60
  const equityPct = parseOptionalNumber(form.equityPct) ?? 40
  const debtAmount = Math.max(result.financeSummary.debtAmountSgd ?? 0, 0)
  const equityAmount = Math.max(result.financeSummary.equityRequiredSgd ?? 0, 0)

  return {
    name: `${form.projectName.trim() || 'Quick screen'} finance handoff`,
    description: `Seeded from the standalone deal calculator on ${result.generatedAt}.`,
    currency: 'SGD',
    isPrimary: true,
    costEscalation: {
      amount: Math.max(totalCapex, 1).toFixed(2),
      basePeriod: currentQuarterLabel(now),
      seriesName: 'construction_cost_index',
      jurisdiction: result.site.jurisdictionCode || 'SG',
    },
    cashFlow: {
      discountRate: pctToRate(form.discountRatePct, '0.0800'),
      cashFlows,
    },
    dscr: {
      netOperatingIncomes: dscrIncomes,
      debtServices: dscrDebtService,
      periodLabels: Array.from({ length: holdYears }, (_, index) => `Year ${index + 1}`),
    },
    capitalStack: [
      {
        name: 'Sponsor Equity',
        sourceType: 'equity',
        amount: Math.max(equityAmount, totalCapex * (equityPct / 100), 1).toFixed(2),
        trancheOrder: 1,
      },
      {
        name: 'Senior Debt',
        sourceType: 'debt',
        amount: Math.max(debtAmount, totalCapex * (debtPct / 100), 0).toFixed(2),
        rate: pctToRate(form.annualInterestRatePct, '0.0480'),
        trancheOrder: 2,
      },
    ],
    drawdownSchedule: [
      { period: 'M1', equityDraw: (totalCapex * 0.18).toFixed(2), debtDraw: '0.00' },
      {
        period: 'M2',
        equityDraw: (totalCapex * 0.12).toFixed(2),
        debtDraw: (totalCapex * 0.22).toFixed(2),
      },
      {
        period: 'M3',
        equityDraw: (totalCapex * 0.10).toFixed(2),
        debtDraw: (totalCapex * 0.20).toFixed(2),
      },
      {
        period: 'M4',
        equityDraw: '0.00',
        debtDraw: (totalCapex * 0.18).toFixed(2),
      },
    ],
    assetMix: result.assetBreakdowns.map((asset) => ({
      assetType: asset.assetType,
      allocationPct: asset.allocationPct ?? undefined,
      niaSqm: asset.niaSqm ?? undefined,
      rentPsmMonth: asset.rentPsmMonth ?? undefined,
      estimatedCapexSgd: asset.estimatedCapexSgd ?? undefined,
      absorptionMonths: asset.absorptionMonths ?? undefined,
      riskLevel: asset.riskLevel ?? undefined,
      notes: asset.notes,
    })),
    constructionLoan: {
      interestRate: pctToRate(form.annualInterestRatePct, '0.0480'),
      periodsPerYear: 12,
      capitaliseInterest: true,
      facilities: [
        {
          name: 'Senior Debt',
          amount: Math.max(debtAmount, totalCapex * (debtPct / 100), 0).toFixed(2),
          interestRate: pctToRate(form.annualInterestRatePct, '0.0480'),
          periodsPerYear: 12,
          capitaliseInterest: true,
        },
      ],
    },
    sensitivityBands: [
      { parameter: 'Rent', low: '-8', base: '0', high: '6' },
      { parameter: 'Construction Cost', low: '10', base: '0', high: '-5' },
      { parameter: 'Interest Rate (delta %)', low: '1.50', base: '0', high: '-0.75' },
    ],
  }
}

function SourceBadge({
  label,
  source,
}: {
  label: string
  source: ExternalSourceMetadata | null
}) {
  if (!source) {
    return null
  }

  const tone =
    source.state === 'live'
      ? '#0f766e'
      : source.state === 'mock'
        ? '#9a3412'
        : '#475569'

  return (
    <span
      style={{
        display: 'inline-flex',
        alignItems: 'center',
        gap: 6,
        padding: '6px 10px',
        borderRadius: 999,
        background: `${tone}14`,
        color: tone,
        fontSize: 12,
        fontWeight: 600,
      }}
    >
      <span>{label}</span>
      <span>{source.state}</span>
    </span>
  )
}

function MetricCard({
  label,
  value,
  hint,
}: {
  label: string
  value: string
  hint?: string | null
}) {
  return (
    <div
      style={{
        padding: 16,
        borderRadius: 18,
        background: 'rgba(255,255,255,0.78)',
        border: '1px solid rgba(15,23,42,0.08)',
        boxShadow: '0 10px 30px rgba(15,23,42,0.06)',
      }}
    >
      <div style={{ fontSize: 12, textTransform: 'uppercase', color: '#64748b' }}>
        {label}
      </div>
      <div style={{ marginTop: 8, fontSize: 28, fontWeight: 700, color: '#0f172a' }}>
        {value}
      </div>
      {hint ? (
        <div style={{ marginTop: 8, fontSize: 13, color: '#475569' }}>{hint}</div>
      ) : null}
    </div>
  )
}

function QualityCard({
  title,
  value,
  detail,
}: {
  title: string
  value: string
  detail: string
}) {
  return (
    <div
      style={{
        padding: 16,
        borderRadius: 18,
        background: 'rgba(248,250,252,0.92)',
        border: '1px solid rgba(15,23,42,0.08)',
      }}
    >
      <div style={{ fontSize: 12, textTransform: 'uppercase', color: '#64748b' }}>
        {title}
      </div>
      <div style={{ marginTop: 8, fontSize: 20, fontWeight: 700, color: '#0f172a' }}>
        {value}
      </div>
      <div style={{ marginTop: 8, fontSize: 13, color: '#475569', lineHeight: 1.45 }}>
        {detail}
      </div>
    </div>
  )
}

export function DealCalculatorPage() {
  const [form, setForm] = useState<FormState>(INITIAL_STATE)
  const [result, setResult] = useState<DealCalculatorResult | null>(null)
  const [isSubmitting, setIsSubmitting] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [handoffMessage, setHandoffMessage] = useState<string | null>(null)

  const isManualMode = form.address.trim().length === 0

  const sourceBadges = useMemo(() => {
    if (!result) {
      return null
    }
    return (
      <div style={{ display: 'flex', flexWrap: 'wrap', gap: 10 }}>
        <SourceBadge label="Geocoding" source={result.site.geocodingSource} />
        <SourceBadge label="Amenities" source={result.site.amenitiesSource} />
        <SourceBadge label="URA" source={result.site.uraSource} />
      </div>
    )
  }, [result])

  const sourceNotes = useMemo(() => {
    if (!result) {
      return []
    }
    return [
      { label: 'Geocoding', source: result.site.geocodingSource },
      { label: 'Amenities', source: result.site.amenitiesSource },
      { label: 'URA', source: result.site.uraSource },
    ]
      .filter(
        (
          item,
        ): item is {
          label: string
          source: ExternalSourceMetadata
        } => Boolean(item.source?.reason),
      )
      .map((item) => `${item.label}: ${item.source.reason}`)
  }, [result])

  const updateField = (key: keyof FormState) => (event: React.ChangeEvent<HTMLInputElement | HTMLSelectElement>) => {
    const value = event.target.value
    setForm((current) => ({ ...current, [key]: value }))
  }

  async function handleSubmit(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault()
    setIsSubmitting(true)
    setError(null)

    try {
      const response = await evaluateDealCalculator({
        projectName: form.projectName,
        address: form.address.trim() || undefined,
        landUse: form.landUse || undefined,
        zoneCode: form.zoneCode || undefined,
        siteAreaSqm: parseOptionalNumber(form.siteAreaSqm),
        allowablePlotRatio: parseOptionalNumber(form.allowablePlotRatio),
        currentGfaSqm: parseOptionalNumber(form.currentGfaSqm),
        targetGrossFloorAreaSqm: parseOptionalNumber(form.targetGrossFloorAreaSqm),
        buildingHeightMeters: parseOptionalNumber(form.buildingHeightMeters),
        financing: {
          equityPct: parseOptionalNumber(form.equityPct),
          debtPct: parseOptionalNumber(form.debtPct),
          annualInterestRatePct: parseOptionalNumber(form.annualInterestRatePct),
          discountRatePct: parseOptionalNumber(form.discountRatePct),
          exitCapRatePct: parseOptionalNumber(form.exitCapRatePct),
          saleCostPct: parseOptionalNumber(form.saleCostPct),
          holdYears: parseOptionalNumber(form.holdYears),
        },
      })
      startTransition(() => {
        setResult(response)
        setHandoffMessage(null)
      })
    } catch (submissionError) {
      setError(
        submissionError instanceof Error
          ? submissionError.message
          : 'Unable to run the deal calculator.',
      )
    } finally {
      setIsSubmitting(false)
    }
  }

  function handleFinanceHandoff() {
    if (!result) {
      return
    }
    saveQuickScreenFinanceDraft({
      createdAt: new Date().toISOString(),
      projectName: form.projectName,
      scenario: buildQuickScreenScenario(form, result),
      assessment: {
        generatedAt: result.generatedAt,
        ruleCorpusStatus: result.ruleCorpusStatus ?? result.buildEnvelope.ruleCorpusStatus,
        sourceNotes,
        recommendedRuleIds: result.recommendedRuleIds,
      },
    })
    setHandoffMessage('Finance handoff saved. Open the finance workspace to import it.')
  }

  return (
    <div
      style={{
        minHeight: '100%',
        background:
          'linear-gradient(135deg, rgba(255,247,237,0.88), rgba(248,250,252,0.96) 45%, rgba(226,232,240,0.92))',
        padding: '24px 0 48px',
      }}
    >
      <div
        style={{
          width: 'min(1200px, calc(100vw - 32px))',
          margin: '0 auto',
          display: 'grid',
          gridTemplateColumns: 'minmax(320px, 420px) minmax(0, 1fr)',
          gap: 20,
        }}
      >
        <section
          style={{
            padding: 24,
            borderRadius: 28,
            background: 'rgba(255,255,255,0.86)',
            border: '1px solid rgba(15,23,42,0.08)',
            boxShadow: '0 24px 80px rgba(15,23,42,0.10)',
            alignSelf: 'start',
            position: 'sticky',
            top: 20,
          }}
        >
          <div style={{ fontSize: 12, textTransform: 'uppercase', color: '#9a3412' }}>
            Top-of-funnel
          </div>
          <h1 style={{ margin: '10px 0 8px', fontSize: 34, lineHeight: 1.05 }}>
            Deal calculator
          </h1>
          <p style={{ margin: 0, color: '#475569', lineHeight: 1.5 }}>
            Paste a Singapore address or switch to manual assumptions. The screen
            returns build envelope, feasibility, and quick finance in one pass.
          </p>

          <form onSubmit={handleSubmit} style={{ marginTop: 22, display: 'grid', gap: 14 }}>
            <label style={{ display: 'grid', gap: 6 }}>
              <span style={{ fontSize: 13, fontWeight: 600 }}>Project name</span>
              <input value={form.projectName} onChange={updateField('projectName')} />
            </label>
            <label style={{ display: 'grid', gap: 6 }}>
              <span style={{ fontSize: 13, fontWeight: 600 }}>
                Address
              </span>
              <input
                value={form.address}
                onChange={updateField('address')}
                placeholder="1 Marina Boulevard, Singapore"
              />
            </label>

            <div
              style={{
                padding: 12,
                borderRadius: 16,
                background: isManualMode ? '#fff7ed' : '#f8fafc',
                color: '#475569',
                fontSize: 13,
              }}
            >
              Leave the address blank to run in manual mode.
            </div>

            <div
              style={{
                display: 'grid',
                gridTemplateColumns: 'repeat(2, minmax(0, 1fr))',
                gap: 12,
              }}
            >
              <label style={{ display: 'grid', gap: 6 }}>
                <span style={{ fontSize: 13, fontWeight: 600 }}>Land use</span>
                <select value={form.landUse} onChange={updateField('landUse')}>
                  <option value="residential">Residential</option>
                  <option value="commercial">Commercial</option>
                  <option value="mixed_use">Mixed use</option>
                  <option value="industrial">Industrial</option>
                </select>
              </label>
              <label style={{ display: 'grid', gap: 6 }}>
                <span style={{ fontSize: 13, fontWeight: 600 }}>Zone code</span>
                <input value={form.zoneCode} onChange={updateField('zoneCode')} />
              </label>
              <label style={{ display: 'grid', gap: 6 }}>
                <span style={{ fontSize: 13, fontWeight: 600 }}>Site area (sqm)</span>
                <input value={form.siteAreaSqm} onChange={updateField('siteAreaSqm')} />
              </label>
              <label style={{ display: 'grid', gap: 6 }}>
                <span style={{ fontSize: 13, fontWeight: 600 }}>Plot ratio</span>
                <input
                  value={form.allowablePlotRatio}
                  onChange={updateField('allowablePlotRatio')}
                />
              </label>
              <label style={{ display: 'grid', gap: 6 }}>
                <span style={{ fontSize: 13, fontWeight: 600 }}>Current GFA</span>
                <input value={form.currentGfaSqm} onChange={updateField('currentGfaSqm')} />
              </label>
              <label style={{ display: 'grid', gap: 6 }}>
                <span style={{ fontSize: 13, fontWeight: 600 }}>Target GFA</span>
                <input
                  value={form.targetGrossFloorAreaSqm}
                  onChange={updateField('targetGrossFloorAreaSqm')}
                />
              </label>
            </div>

            <div style={{ borderTop: '1px solid rgba(15,23,42,0.08)', paddingTop: 14 }}>
              <div style={{ fontSize: 13, fontWeight: 700, marginBottom: 10 }}>
                Finance assumptions
              </div>
              <div
                style={{
                  display: 'grid',
                  gridTemplateColumns: 'repeat(2, minmax(0, 1fr))',
                  gap: 12,
                }}
              >
                <label style={{ display: 'grid', gap: 6 }}>
                  <span style={{ fontSize: 13, fontWeight: 600 }}>Equity %</span>
                  <input value={form.equityPct} onChange={updateField('equityPct')} />
                </label>
                <label style={{ display: 'grid', gap: 6 }}>
                  <span style={{ fontSize: 13, fontWeight: 600 }}>Debt %</span>
                  <input value={form.debtPct} onChange={updateField('debtPct')} />
                </label>
                <label style={{ display: 'grid', gap: 6 }}>
                  <span style={{ fontSize: 13, fontWeight: 600 }}>Interest %</span>
                  <input
                    value={form.annualInterestRatePct}
                    onChange={updateField('annualInterestRatePct')}
                  />
                </label>
                <label style={{ display: 'grid', gap: 6 }}>
                  <span style={{ fontSize: 13, fontWeight: 600 }}>Discount %</span>
                  <input
                    value={form.discountRatePct}
                    onChange={updateField('discountRatePct')}
                  />
                </label>
                <label style={{ display: 'grid', gap: 6 }}>
                  <span style={{ fontSize: 13, fontWeight: 600 }}>Exit cap %</span>
                  <input
                    value={form.exitCapRatePct}
                    onChange={updateField('exitCapRatePct')}
                  />
                </label>
                <label style={{ display: 'grid', gap: 6 }}>
                  <span style={{ fontSize: 13, fontWeight: 600 }}>Hold years</span>
                  <input value={form.holdYears} onChange={updateField('holdYears')} />
                </label>
              </div>
            </div>

            <button
              type="submit"
              disabled={isSubmitting}
              style={{
                marginTop: 6,
                padding: '14px 18px',
                borderRadius: 16,
                border: 'none',
                background: '#0f172a',
                color: 'white',
                fontWeight: 700,
                cursor: isSubmitting ? 'progress' : 'pointer',
              }}
            >
              {isSubmitting ? 'Running screen...' : 'Run deal screen'}
            </button>

            {error ? (
              <div
                style={{
                  padding: 12,
                  borderRadius: 14,
                  background: '#fee2e2',
                  color: '#991b1b',
                  fontSize: 13,
                }}
              >
                {error}
              </div>
            ) : null}
          </form>
        </section>

        <section
          style={{
            display: 'grid',
            gap: 18,
          }}
        >
          {result ? (
            <>
              <div
                style={{
                  padding: 24,
                  borderRadius: 28,
                  background: 'rgba(255,255,255,0.88)',
                  border: '1px solid rgba(15,23,42,0.08)',
                  boxShadow: '0 24px 80px rgba(15,23,42,0.08)',
                }}
              >
                <div style={{ display: 'flex', justifyContent: 'space-between', gap: 16, flexWrap: 'wrap' }}>
                  <div>
                    <div style={{ fontSize: 12, textTransform: 'uppercase', color: '#9a3412' }}>
                      Screen result
                    </div>
                    <h2 style={{ margin: '8px 0 6px', fontSize: 28 }}>
                      {result.site.formattedAddress}
                    </h2>
                    <p style={{ margin: 0, color: '#475569' }}>
                      {result.site.landUse.replace(/_/g, ' ')} • {result.site.zoneCode ?? 'Zone pending'} •{' '}
                      {result.ruleCorpusStatus?.coverageState ?? 'unknown'} corpus
                    </p>
                  </div>
                  {sourceBadges}
                </div>
                <div
                  style={{
                    marginTop: 18,
                    display: 'grid',
                    gridTemplateColumns: 'repeat(auto-fit, minmax(180px, 1fr))',
                    gap: 12,
                  }}
                >
                  <QualityCard
                    title="Rule corpus"
                    value={result.ruleCorpusStatus?.coverageState ?? 'unknown'}
                    detail={`Confidence ${result.ruleCorpusStatus?.confidence ?? 'unknown'} • ${result.ruleCorpusStatus?.counts.approved ?? 0} approved / ${result.ruleCorpusStatus?.counts.needsReview ?? 0} needs review`}
                  />
                  <QualityCard
                    title="Applied rules"
                    value={String(result.ruleCorpusStatus?.appliedRuleIds.length ?? 0)}
                    detail="Rules included in this quick screen recommendation set."
                  />
                  <QualityCard
                    title="Source posture"
                    value={
                      sourceNotes.length > 0 ? 'Review notes' : 'No warnings surfaced'
                    }
                    detail={
                      sourceNotes[0] ??
                      'The current source set did not return provider caveats for this run.'
                    }
                  />
                </div>
                {sourceNotes.length > 1 ? (
                  <ul
                    style={{
                      margin: '14px 0 0',
                      paddingLeft: 18,
                      color: '#475569',
                      fontSize: 13,
                    }}
                  >
                    {sourceNotes.slice(1).map((note) => (
                      <li key={note}>{note}</li>
                    ))}
                  </ul>
                ) : null}
              </div>

              <div
                style={{
                  display: 'grid',
                  gridTemplateColumns: 'repeat(4, minmax(0, 1fr))',
                  gap: 14,
                }}
              >
                <MetricCard
                  label="Max GFA"
                  value={`${result.feasibilitySummary.maxPermissibleGfaSqm.toLocaleString()} sqm`}
                  hint={result.feasibilitySummary.accuracyRange}
                />
                <MetricCard
                  label="Achievable GFA"
                  value={`${result.feasibilitySummary.estimatedAchievableGfaSqm.toLocaleString()} sqm`}
                  hint={result.feasibilitySummary.remarks}
                />
                <MetricCard
                  label="NPV"
                  value={formatCurrency(result.financeSummary.npvSgd)}
                  hint="Quick hold model"
                />
                <MetricCard
                  label="IRR / MOIC"
                  value={`${formatMetric(result.financeSummary.irr)} / ${formatMetric(result.financeSummary.moic)}`}
                  hint="Equity return screen"
                />
              </div>

              <div
                style={{
                  display: 'grid',
                  gridTemplateColumns: 'repeat(2, minmax(0, 1fr))',
                  gap: 18,
                }}
              >
                <div
                  style={{
                    padding: 22,
                    borderRadius: 24,
                    background: 'rgba(255,255,255,0.88)',
                    border: '1px solid rgba(15,23,42,0.08)',
                  }}
                >
                  <h3 style={{ marginTop: 0 }}>Feasibility</h3>
                  <dl
                    style={{
                      display: 'grid',
                      gridTemplateColumns: 'repeat(2, minmax(0, 1fr))',
                      gap: 12,
                    }}
                  >
                    <div>
                      <dt style={{ fontSize: 12, color: '#64748b' }}>Site area</dt>
                      <dd style={{ margin: '4px 0 0' }}>
                        {result.buildEnvelope.siteAreaSqm?.toLocaleString() ?? 'Pending'} sqm
                      </dd>
                    </div>
                    <div>
                      <dt style={{ fontSize: 12, color: '#64748b' }}>Plot ratio</dt>
                      <dd style={{ margin: '4px 0 0' }}>
                        {result.buildEnvelope.allowablePlotRatio ?? 'Pending'}
                      </dd>
                    </div>
                    <div>
                      <dt style={{ fontSize: 12, color: '#64748b' }}>Additional GFA</dt>
                      <dd style={{ margin: '4px 0 0' }}>
                        {result.buildEnvelope.additionalPotentialGfaSqm?.toLocaleString() ?? 'Pending'} sqm
                      </dd>
                    </div>
                    <div>
                      <dt style={{ fontSize: 12, color: '#64748b' }}>Units</dt>
                      <dd style={{ margin: '4px 0 0' }}>
                        {result.feasibilitySummary.estimatedUnitCount.toLocaleString()}
                      </dd>
                    </div>
                  </dl>

                  <div style={{ marginTop: 16 }}>
                    <div style={{ fontSize: 13, fontWeight: 700, marginBottom: 8 }}>
                      Assumptions
                    </div>
                    <ul style={{ margin: 0, paddingLeft: 18, color: '#475569' }}>
                      {result.buildEnvelope.assumptions.map((assumption) => (
                        <li key={assumption}>{assumption}</li>
                      ))}
                    </ul>
                  </div>
                </div>

                <div
                  style={{
                    padding: 22,
                    borderRadius: 24,
                    background: 'rgba(255,255,255,0.88)',
                    border: '1px solid rgba(15,23,42,0.08)',
                  }}
                >
                  <h3 style={{ marginTop: 0 }}>Finance</h3>
                  <dl
                    style={{
                      display: 'grid',
                      gridTemplateColumns: 'repeat(2, minmax(0, 1fr))',
                      gap: 12,
                    }}
                  >
                    <div>
                      <dt style={{ fontSize: 12, color: '#64748b' }}>Capex</dt>
                      <dd style={{ margin: '4px 0 0' }}>
                        {formatCurrency(result.financeSummary.totalCapexSgd)}
                      </dd>
                    </div>
                    <div>
                      <dt style={{ fontSize: 12, color: '#64748b' }}>Annual NOI</dt>
                      <dd style={{ margin: '4px 0 0' }}>
                        {formatCurrency(result.financeSummary.totalAnnualNoiSgd)}
                      </dd>
                    </div>
                    <div>
                      <dt style={{ fontSize: 12, color: '#64748b' }}>Debt service</dt>
                      <dd style={{ margin: '4px 0 0' }}>
                        {formatCurrency(result.financeSummary.annualDebtServiceSgd)}
                      </dd>
                    </div>
                    <div>
                      <dt style={{ fontSize: 12, color: '#64748b' }}>DSCR</dt>
                      <dd style={{ margin: '4px 0 0' }}>
                        {formatMetric(result.financeSummary.dscr)}
                      </dd>
                    </div>
                    <div>
                      <dt style={{ fontSize: 12, color: '#64748b' }}>Equity</dt>
                      <dd style={{ margin: '4px 0 0' }}>
                        {formatCurrency(result.financeSummary.equityRequiredSgd)}
                      </dd>
                    </div>
                    <div>
                      <dt style={{ fontSize: 12, color: '#64748b' }}>Exit value</dt>
                      <dd style={{ margin: '4px 0 0' }}>
                        {formatCurrency(result.financeSummary.estimatedExitValueSgd)}
                      </dd>
                    </div>
                  </dl>

                  <div style={{ marginTop: 16 }}>
                    <div style={{ fontSize: 13, fontWeight: 700, marginBottom: 8 }}>
                      Finance notes
                    </div>
                    <ul style={{ margin: 0, paddingLeft: 18, color: '#475569' }}>
                      {result.financeSummary.notes.map((note) => (
                        <li key={note}>{note}</li>
                      ))}
                    </ul>
                  </div>
                </div>
              </div>

              <div
                style={{
                  display: 'grid',
                  gridTemplateColumns: 'repeat(2, minmax(0, 1fr))',
                  gap: 18,
                }}
              >
                <div
                  style={{
                    padding: 22,
                    borderRadius: 24,
                    background: 'rgba(255,255,255,0.88)',
                    border: '1px solid rgba(15,23,42,0.08)',
                  }}
                >
                  <h3 style={{ marginTop: 0 }}>Why this screen says no</h3>
                  <ul style={{ margin: 0, paddingLeft: 18, color: '#475569' }}>
                    {result.feasibilityRules.map((rule) => (
                      <li key={rule.id}>
                        <strong>{rule.title}:</strong> {rule.status}
                        {rule.notes ? ` — ${rule.notes}` : ''}
                      </li>
                    ))}
                  </ul>
                </div>

                <div
                  style={{
                    padding: 22,
                    borderRadius: 24,
                    background: 'rgba(255,255,255,0.88)',
                    border: '1px solid rgba(15,23,42,0.08)',
                  }}
                >
                  <h3 style={{ marginTop: 0 }}>Next actions</h3>
                  <ul style={{ margin: 0, paddingLeft: 18, color: '#475569' }}>
                    {result.recommendations.map((recommendation) => (
                      <li key={recommendation}>{recommendation}</li>
                    ))}
                  </ul>
                  <div style={{ display: 'flex', gap: 12, flexWrap: 'wrap', marginTop: 18 }}>
                    <a
                      href="/finance"
                      onClick={handleFinanceHandoff}
                      style={{
                        display: 'inline-flex',
                        padding: '12px 16px',
                        borderRadius: 14,
                        background: '#0f172a',
                        color: 'white',
                        textDecoration: 'none',
                        fontWeight: 700,
                      }}
                    >
                      Carry into finance
                    </a>
                    <a
                      href="/app/site-acquisition"
                      style={{
                        display: 'inline-flex',
                        padding: '12px 16px',
                        borderRadius: 14,
                        background: '#ea580c',
                        color: 'white',
                        textDecoration: 'none',
                        fontWeight: 700,
                      }}
                    >
                      Continue in site acquisition
                    </a>
                  </div>
                  {handoffMessage ? (
                    <div style={{ marginTop: 12, fontSize: 13, color: '#0f766e' }}>
                      {handoffMessage}
                    </div>
                  ) : null}
                </div>
              </div>
            </>
          ) : (
            <div
              style={{
                padding: 28,
                borderRadius: 28,
                background: 'rgba(255,255,255,0.82)',
                border: '1px dashed rgba(15,23,42,0.14)',
                color: '#475569',
              }}
            >
              Run the screen to generate one-page feasibility and finance.
            </div>
          )}
        </section>
      </div>
    </div>
  )
}

export default DealCalculatorPage
