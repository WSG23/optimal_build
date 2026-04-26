import React, { startTransition, useMemo, useState } from 'react'
import { Box, Snackbar, Stack } from '@mui/material'

import {
  evaluateDealCalculator,
  type DealCalculatorResult,
} from '../../../api/dealCalculator'
import type { FinanceScenarioInput } from '../../../api/finance'
import type { ExternalSourceMetadata } from '../../../api/externalSources'
import { saveQuickScreenFinanceDraft } from '../../../modules/finance/quickScreenDraft'
import { EmptyState } from '../../../components/canonical'
import { INITIAL_FORM_STATE, type FormState } from './components/dealFormState'
import { DealInputsForm } from './components/DealInputsForm'
import { DealResultsPanel } from './components/DealResultsPanel'

function parseOptionalNumber(value: string): number | undefined {
  const trimmed = value.trim()
  if (!trimmed) {
    return undefined
  }
  const parsed = Number(trimmed)
  return Number.isFinite(parsed) ? parsed : undefined
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

function toUserFacingDealError(error: unknown): string {
  if (!(error instanceof Error)) {
    return 'Unable to run the deal calculator.'
  }

  if (
    /404/.test(error.message) ||
    /Unable to resolve address/i.test(error.message)
  ) {
    return 'We could not match that address. Check the address or switch to manual assumptions.'
  }

  return error.message
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
  const exitValue = Math.max(
    result.financeSummary.estimatedExitValueSgd ?? 0,
    0,
  )
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
      periodLabels: Array.from(
        { length: holdYears },
        (_, index) => `Year ${index + 1}`,
      ),
    },
    capitalStack: [
      {
        name: 'Sponsor Equity',
        sourceType: 'equity',
        amount: Math.max(
          equityAmount,
          totalCapex * (equityPct / 100),
          1,
        ).toFixed(2),
        trancheOrder: 1,
      },
      {
        name: 'Senior Debt',
        sourceType: 'debt',
        amount: Math.max(debtAmount, totalCapex * (debtPct / 100), 0).toFixed(
          2,
        ),
        rate: pctToRate(form.annualInterestRatePct, '0.0480'),
        trancheOrder: 2,
      },
    ],
    drawdownSchedule: [
      {
        period: 'M1',
        equityDraw: (totalCapex * 0.18).toFixed(2),
        debtDraw: '0.00',
      },
      {
        period: 'M2',
        equityDraw: (totalCapex * 0.12).toFixed(2),
        debtDraw: (totalCapex * 0.22).toFixed(2),
      },
      {
        period: 'M3',
        equityDraw: (totalCapex * 0.1).toFixed(2),
        debtDraw: (totalCapex * 0.2).toFixed(2),
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
          amount: Math.max(debtAmount, totalCapex * (debtPct / 100), 0).toFixed(
            2,
          ),
          interestRate: pctToRate(form.annualInterestRatePct, '0.0480'),
          periodsPerYear: 12,
          capitaliseInterest: true,
        },
      ],
    },
    sensitivityBands: [
      { parameter: 'Rent', low: '-8', base: '0', high: '6' },
      { parameter: 'Construction Cost', low: '10', base: '0', high: '-5' },
      {
        parameter: 'Interest Rate (delta %)',
        low: '1.50',
        base: '0',
        high: '-0.75',
      },
    ],
  }
}

export function DealCalculatorPage() {
  const [form, setForm] = useState<FormState>(INITIAL_FORM_STATE)
  const [result, setResult] = useState<DealCalculatorResult | null>(null)
  const [isSubmitting, setIsSubmitting] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [handoffMessage, setHandoffMessage] = useState<string | null>(null)
  const [successMessage, setSuccessMessage] = useState<string | null>(null)

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

  async function handleSubmit(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault()

    if (!form.projectName.trim()) {
      setError('Project name is required.')
      return
    }

    const numericFields: Array<[keyof FormState, string]> = [
      ['siteAreaSqm', 'Site area'],
      ['allowablePlotRatio', 'Plot ratio'],
      ['currentGfaSqm', 'Current GFA'],
      ['targetGrossFloorAreaSqm', 'Target GFA'],
    ]
    for (const [key, label] of numericFields) {
      const val = form[key].trim()
      if (val && !Number.isFinite(Number(val))) {
        setError(`${label} must be a number.`)
        return
      }
    }

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
        targetGrossFloorAreaSqm: parseOptionalNumber(
          form.targetGrossFloorAreaSqm,
        ),
        buildingHeightMeters: parseOptionalNumber(form.buildingHeightMeters),
        financing: {
          equityPct: parseOptionalNumber(form.equityPct),
          debtPct: parseOptionalNumber(form.debtPct),
          annualInterestRatePct: parseOptionalNumber(
            form.annualInterestRatePct,
          ),
          discountRatePct: parseOptionalNumber(form.discountRatePct),
          exitCapRatePct: parseOptionalNumber(form.exitCapRatePct),
          saleCostPct: parseOptionalNumber(form.saleCostPct),
          holdYears: parseOptionalNumber(form.holdYears),
        },
      })
      startTransition(() => {
        setResult(response)
        setHandoffMessage(null)
        setSuccessMessage('Deal screen complete')
      })
    } catch (submissionError) {
      setError(toUserFacingDealError(submissionError))
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
        ruleCorpusStatus:
          result.ruleCorpusStatus ?? result.buildEnvelope.ruleCorpusStatus,
        sourceNotes,
        recommendedRuleIds: result.recommendedRuleIds,
      },
    })
    setHandoffMessage(
      'Finance handoff saved. Open the finance workspace to import it.',
    )
  }

  return (
    <Box
      role="main"
      sx={{
        width: '100%',
        maxWidth: '1200px',
        mx: 'auto',
        pb: 'var(--ob-space-300)',
        display: 'grid',
        gridTemplateColumns: {
          xs: '1fr',
          md: 'minmax(320px, 400px) minmax(0, 1fr)',
        },
        gap: 'var(--ob-space-200)',
        alignItems: 'start',
      }}
    >
      <DealInputsForm
        form={form}
        onFormChange={setForm}
        onSubmit={handleSubmit}
        isSubmitting={isSubmitting}
        error={error}
      />

      <Stack spacing="var(--ob-space-200)">
        {!result && !isSubmitting && (
          <EmptyState
            title="Ready to screen"
            description="Enter site details and run a deal screen to see feasibility results."
            size="sm"
          />
        )}
        <DealResultsPanel
          result={result}
          sourceNotes={sourceNotes}
          handoffMessage={handoffMessage}
          onFinanceHandoff={handleFinanceHandoff}
        />
      </Stack>

      <Snackbar
        open={Boolean(successMessage)}
        autoHideDuration={3000}
        onClose={() => setSuccessMessage(null)}
        message={successMessage}
        anchorOrigin={{ vertical: 'bottom', horizontal: 'center' }}
        ContentProps={{
          role: 'status',
          'aria-live': 'polite' as const,
          sx: {
            bgcolor: 'var(--ob-success-bg)',
            color: 'var(--ob-success-text)',
            border: '1px solid var(--ob-success-400)',
            borderRadius: 'var(--ob-radius-sm)',
            fontWeight: 'var(--ob-font-weight-semibold)',
          },
        }}
      />
    </Box>
  )
}

export default DealCalculatorPage
