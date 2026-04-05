import React, { startTransition, useMemo, useState } from 'react'
import {
  Box,
  Collapse,
  Grid,
  IconButton,
  MenuItem,
  Select,
  Stack,
  Typography,
} from '@mui/material'
import { ExpandMore, ExpandLess } from '@mui/icons-material'

import {
  evaluateDealCalculator,
  type DealCalculatorResult,
} from '../../../api/dealCalculator'
import type { FinanceScenarioInput } from '../../../api/finance'
import type { ExternalSourceMetadata } from '../../../api/externalSources'
import { saveQuickScreenFinanceDraft } from '../../../modules/finance/quickScreenDraft'
import { Card } from '../../../components/canonical/Card'
import { Button } from '../../../components/canonical/Button'
import { Input } from '../../../components/canonical/Input'
import { AlertBlock } from '../../../components/canonical/AlertBlock'
import { Tag } from '../../../components/canonical/Tag'
import { MetricTile } from '../../../components/canonical/MetricTile'
import { EmptyState } from '../../../components/canonical/EmptyState'

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

  const colorMap: Record<string, 'success' | 'warning' | 'default'> = {
    live: 'success',
    mock: 'warning',
  }

  return (
    <Tag color={colorMap[source.state] ?? 'default'} size="sm">
      {label}: {source.state}
    </Tag>
  )
}

function DefinitionItem({
  term,
  value,
}: {
  term: string
  value: React.ReactNode
}) {
  return (
    <Box>
      <Typography
        component="dt"
        sx={{
          fontSize: 'var(--ob-font-size-xs)',
          color: 'var(--ob-color-text-secondary)',
          textTransform: 'uppercase',
          letterSpacing: '0.04em',
        }}
      >
        {term}
      </Typography>
      <Typography
        component="dd"
        sx={{
          m: 0,
          mt: 'var(--ob-space-025)',
          fontSize: 'var(--ob-font-size-sm)',
          color: 'var(--ob-color-text-primary)',
        }}
      >
        {value}
      </Typography>
    </Box>
  )
}

export function DealCalculatorPage() {
  const [form, setForm] = useState<FormState>(INITIAL_STATE)
  const [result, setResult] = useState<DealCalculatorResult | null>(null)
  const [isSubmitting, setIsSubmitting] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [handoffMessage, setHandoffMessage] = useState<string | null>(null)
  const [financeOpen, setFinanceOpen] = useState(false)

  const isManualMode = form.address.trim().length === 0

  const sourceBadges = useMemo(() => {
    if (!result) {
      return null
    }
    return (
      <Stack direction="row" spacing="var(--ob-space-050)" flexWrap="wrap">
        <SourceBadge label="Geocoding" source={result.site.geocodingSource} />
        <SourceBadge label="Amenities" source={result.site.amenitiesSource} />
        <SourceBadge label="URA" source={result.site.uraSource} />
      </Stack>
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

  const updateField =
    (key: keyof FormState) =>
    (
      event: React.ChangeEvent<
        HTMLInputElement | HTMLTextAreaElement | { value: unknown }
      >,
    ) => {
      const value = (event.target as HTMLInputElement).value
      setForm((current) => ({ ...current, [key]: value }))
    }

  const updateSelect =
    (key: keyof FormState) => (event: { target: { value: string } }) => {
      setForm((current) => ({ ...current, [key]: event.target.value }))
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
        display: 'grid',
        gridTemplateColumns: {
          xs: '1fr',
          md: 'minmax(320px, 400px) minmax(0, 1fr)',
        },
        gap: 'var(--ob-space-200)',
        alignItems: 'start',
      }}
    >
      {/* Form sidebar */}
      <Card
        variant="default"
        sx={{
          p: 'var(--ob-space-200)',
          position: { md: 'sticky' },
          top: { md: 'var(--ob-space-200)' },
        }}
      >
        <Typography
          variant="overline"
          sx={{
            color: 'var(--ob-color-text-secondary)',
            letterSpacing: '0.08em',
          }}
        >
          Top-of-funnel
        </Typography>
        <Typography
          variant="h5"
          sx={{
            fontWeight: 700,
            mt: 'var(--ob-space-050)',
            mb: 'var(--ob-space-050)',
          }}
        >
          Deal calculator
        </Typography>
        <Typography
          variant="body2"
          sx={{
            color: 'var(--ob-color-text-secondary)',
            mb: 'var(--ob-space-200)',
          }}
        >
          Paste a Singapore address or switch to manual assumptions. Returns
          build envelope, feasibility, and quick finance in one pass.
        </Typography>

        <form onSubmit={handleSubmit} aria-label="Deal screening form">
          <Stack spacing="var(--ob-space-150)">
            <Input
              label="Project name"
              value={form.projectName}
              onChange={updateField('projectName')}
              size="small"
            />
            <Input
              label="Address"
              value={form.address}
              onChange={updateField('address')}
              placeholder="1 Marina Boulevard, Singapore"
              size="small"
            />

            {isManualMode && (
              <AlertBlock type="info" variant="outlined">
                Manual mode active. Fill in site parameters below.
              </AlertBlock>
            )}

            {/* Site parameters */}
            <Grid container spacing="var(--ob-space-100)">
              <Grid item xs={6}>
                <Box>
                  <Typography
                    component="label"
                    variant="caption"
                    sx={{
                      display: 'block',
                      mb: 'var(--ob-space-025)',
                      color: 'var(--ob-color-text-secondary)',
                      fontWeight: 'var(--ob-font-weight-medium)',
                    }}
                  >
                    Land use
                  </Typography>
                  <Select
                    value={form.landUse}
                    onChange={updateSelect('landUse')}
                    size="small"
                    fullWidth
                    sx={{
                      borderRadius: 'var(--ob-radius-sm)',
                      fontSize: 'var(--ob-font-size-sm)',
                    }}
                  >
                    <MenuItem value="residential">Residential</MenuItem>
                    <MenuItem value="commercial">Commercial</MenuItem>
                    <MenuItem value="mixed_use">Mixed use</MenuItem>
                    <MenuItem value="industrial">Industrial</MenuItem>
                  </Select>
                </Box>
              </Grid>
              <Grid item xs={6}>
                <Input
                  label="Zone code"
                  value={form.zoneCode}
                  onChange={updateField('zoneCode')}
                  size="small"
                />
              </Grid>
              <Grid item xs={6}>
                <Input
                  label="Site area (sqm)"
                  value={form.siteAreaSqm}
                  onChange={updateField('siteAreaSqm')}
                  size="small"
                  inputProps={{ inputMode: 'decimal' }}
                />
              </Grid>
              <Grid item xs={6}>
                <Input
                  label="Plot ratio"
                  value={form.allowablePlotRatio}
                  onChange={updateField('allowablePlotRatio')}
                  size="small"
                  inputProps={{ inputMode: 'decimal' }}
                />
              </Grid>
              <Grid item xs={6}>
                <Input
                  label="Current GFA"
                  value={form.currentGfaSqm}
                  onChange={updateField('currentGfaSqm')}
                  size="small"
                  inputProps={{ inputMode: 'decimal' }}
                />
              </Grid>
              <Grid item xs={6}>
                <Input
                  label="Target GFA"
                  value={form.targetGrossFloorAreaSqm}
                  onChange={updateField('targetGrossFloorAreaSqm')}
                  size="small"
                  inputProps={{ inputMode: 'decimal' }}
                />
              </Grid>
            </Grid>

            {/* Finance assumptions - collapsible */}
            <Box
              sx={{
                borderTop: 'var(--ob-border-fine)',
                pt: 'var(--ob-space-100)',
              }}
            >
              <Box
                sx={{
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'space-between',
                  cursor: 'pointer',
                }}
                onClick={() => setFinanceOpen((prev) => !prev)}
                role="button"
                aria-expanded={financeOpen}
                aria-controls="finance-assumptions"
                tabIndex={0}
                onKeyDown={(e) => {
                  if (e.key === 'Enter' || e.key === ' ') {
                    e.preventDefault()
                    setFinanceOpen((prev) => !prev)
                  }
                }}
              >
                <Typography
                  variant="subtitle2"
                  sx={{ fontWeight: 'var(--ob-font-weight-semibold)' }}
                >
                  Finance assumptions
                </Typography>
                <IconButton size="small" tabIndex={-1} aria-hidden>
                  {financeOpen ? <ExpandLess /> : <ExpandMore />}
                </IconButton>
              </Box>
              <Collapse in={financeOpen} id="finance-assumptions">
                <Grid
                  container
                  spacing="var(--ob-space-100)"
                  sx={{ mt: 'var(--ob-space-050)' }}
                >
                  <Grid item xs={6}>
                    <Input
                      label="Equity %"
                      value={form.equityPct}
                      onChange={updateField('equityPct')}
                      size="small"
                      inputProps={{ inputMode: 'decimal' }}
                    />
                  </Grid>
                  <Grid item xs={6}>
                    <Input
                      label="Debt %"
                      value={form.debtPct}
                      onChange={updateField('debtPct')}
                      size="small"
                      inputProps={{ inputMode: 'decimal' }}
                    />
                  </Grid>
                  <Grid item xs={6}>
                    <Input
                      label="Interest %"
                      value={form.annualInterestRatePct}
                      onChange={updateField('annualInterestRatePct')}
                      size="small"
                      inputProps={{ inputMode: 'decimal' }}
                    />
                  </Grid>
                  <Grid item xs={6}>
                    <Input
                      label="Discount %"
                      value={form.discountRatePct}
                      onChange={updateField('discountRatePct')}
                      size="small"
                      inputProps={{ inputMode: 'decimal' }}
                    />
                  </Grid>
                  <Grid item xs={6}>
                    <Input
                      label="Exit cap %"
                      value={form.exitCapRatePct}
                      onChange={updateField('exitCapRatePct')}
                      size="small"
                      inputProps={{ inputMode: 'decimal' }}
                    />
                  </Grid>
                  <Grid item xs={6}>
                    <Input
                      label="Hold years"
                      value={form.holdYears}
                      onChange={updateField('holdYears')}
                      size="small"
                      inputProps={{ inputMode: 'numeric' }}
                    />
                  </Grid>
                </Grid>
              </Collapse>
            </Box>

            <Button
              type="submit"
              variant="primary"
              size="lg"
              disabled={isSubmitting}
              sx={{ width: '100%' }}
            >
              {isSubmitting ? 'Running screen...' : 'Run deal screen'}
            </Button>

            {error && <AlertBlock type="error">{error}</AlertBlock>}
          </Stack>
        </form>
      </Card>

      {/* Results */}
      <Stack spacing="var(--ob-space-200)">
        {result ? (
          <>
            {/* Result header */}
            <Card variant="default" sx={{ p: 'var(--ob-space-200)' }}>
              <Box
                sx={{
                  display: 'flex',
                  justifyContent: 'space-between',
                  gap: 'var(--ob-space-100)',
                  flexWrap: 'wrap',
                }}
              >
                <Box>
                  <Typography
                    variant="overline"
                    sx={{
                      color: 'var(--ob-color-text-secondary)',
                      letterSpacing: '0.08em',
                    }}
                  >
                    Screen result
                  </Typography>
                  <Typography
                    variant="h6"
                    sx={{ fontWeight: 700, mt: 'var(--ob-space-025)' }}
                  >
                    {result.site.formattedAddress}
                  </Typography>
                  <Typography
                    variant="body2"
                    sx={{ color: 'var(--ob-color-text-secondary)' }}
                  >
                    {result.site.landUse.replace(/_/g, ' ')} •{' '}
                    {result.site.zoneCode ?? 'Zone pending'} •{' '}
                    {result.ruleCorpusStatus?.coverageState ?? 'unknown'} corpus
                  </Typography>
                </Box>
                {sourceBadges}
              </Box>

              {/* Quality indicators */}
              <Grid
                container
                spacing="var(--ob-space-100)"
                sx={{ mt: 'var(--ob-space-150)' }}
              >
                <Grid item xs={12} sm={4}>
                  <MetricTile
                    label="Rule corpus"
                    value={result.ruleCorpusStatus?.coverageState ?? 'unknown'}
                    variant="compact"
                  />
                </Grid>
                <Grid item xs={12} sm={4}>
                  <MetricTile
                    label="Applied rules"
                    value={String(
                      result.ruleCorpusStatus?.appliedRuleIds.length ?? 0,
                    )}
                    variant="compact"
                  />
                </Grid>
                <Grid item xs={12} sm={4}>
                  <MetricTile
                    label="Source posture"
                    value={sourceNotes.length > 0 ? 'Review notes' : 'Clear'}
                    variant="compact"
                  />
                </Grid>
              </Grid>

              {sourceNotes.length > 0 && (
                <AlertBlock
                  type="info"
                  variant="outlined"
                  sx={{ mt: 'var(--ob-space-150)' }}
                >
                  {sourceNotes.map((note) => (
                    <Typography
                      key={note}
                      variant="body2"
                      sx={{ fontSize: 'var(--ob-font-size-xs)' }}
                    >
                      {note}
                    </Typography>
                  ))}
                </AlertBlock>
              )}
            </Card>

            {/* Key metrics */}
            <Grid container spacing="var(--ob-space-100)">
              <Grid item xs={6} md={3}>
                <MetricTile
                  label="Max GFA"
                  value={`${result.feasibilitySummary.maxPermissibleGfaSqm.toLocaleString()} sqm`}
                  trendLabel={
                    result.feasibilitySummary.accuracyRange ?? undefined
                  }
                />
              </Grid>
              <Grid item xs={6} md={3}>
                <MetricTile
                  label="Achievable GFA"
                  value={`${result.feasibilitySummary.estimatedAchievableGfaSqm.toLocaleString()} sqm`}
                  trendLabel={result.feasibilitySummary.remarks ?? undefined}
                />
              </Grid>
              <Grid item xs={6} md={3}>
                <MetricTile
                  label="NPV"
                  value={formatCurrency(result.financeSummary.npvSgd)}
                  trendLabel="Quick hold model"
                />
              </Grid>
              <Grid item xs={6} md={3}>
                <MetricTile
                  label="IRR / MOIC"
                  value={`${formatMetric(result.financeSummary.irr)} / ${formatMetric(result.financeSummary.moic)}`}
                  trendLabel="Equity return screen"
                />
              </Grid>
            </Grid>

            {/* Detail panels */}
            <Grid container spacing="var(--ob-space-200)">
              <Grid item xs={12} md={6}>
                <Card
                  variant="default"
                  sx={{ p: 'var(--ob-space-200)', height: '100%' }}
                >
                  <Typography
                    variant="subtitle1"
                    sx={{ fontWeight: 700, mb: 'var(--ob-space-150)' }}
                  >
                    Feasibility
                  </Typography>
                  <Box
                    component="dl"
                    sx={{
                      display: 'grid',
                      gridTemplateColumns: 'repeat(2, 1fr)',
                      gap: 'var(--ob-space-100)',
                      m: 0,
                    }}
                  >
                    <DefinitionItem
                      term="Site area"
                      value={`${result.buildEnvelope.siteAreaSqm?.toLocaleString() ?? 'Pending'} sqm`}
                    />
                    <DefinitionItem
                      term="Plot ratio"
                      value={
                        result.buildEnvelope.allowablePlotRatio ?? 'Pending'
                      }
                    />
                    <DefinitionItem
                      term="Additional GFA"
                      value={`${result.buildEnvelope.additionalPotentialGfaSqm?.toLocaleString() ?? 'Pending'} sqm`}
                    />
                    <DefinitionItem
                      term="Units"
                      value={result.feasibilitySummary.estimatedUnitCount.toLocaleString()}
                    />
                  </Box>

                  <Typography
                    variant="subtitle2"
                    sx={{
                      fontWeight: 700,
                      mt: 'var(--ob-space-150)',
                      mb: 'var(--ob-space-075)',
                    }}
                  >
                    Assumptions
                  </Typography>
                  <Box
                    component="ul"
                    sx={{
                      m: 0,
                      pl: 'var(--ob-space-200)',
                      color: 'var(--ob-color-text-secondary)',
                      fontSize: 'var(--ob-font-size-sm)',
                    }}
                  >
                    {result.buildEnvelope.assumptions.map((assumption) => (
                      <li key={assumption}>{assumption}</li>
                    ))}
                  </Box>
                </Card>
              </Grid>

              <Grid item xs={12} md={6}>
                <Card
                  variant="default"
                  sx={{ p: 'var(--ob-space-200)', height: '100%' }}
                >
                  <Typography
                    variant="subtitle1"
                    sx={{ fontWeight: 700, mb: 'var(--ob-space-150)' }}
                  >
                    Finance
                  </Typography>
                  <Box
                    component="dl"
                    sx={{
                      display: 'grid',
                      gridTemplateColumns: 'repeat(2, 1fr)',
                      gap: 'var(--ob-space-100)',
                      m: 0,
                    }}
                  >
                    <DefinitionItem
                      term="Capex"
                      value={formatCurrency(
                        result.financeSummary.totalCapexSgd,
                      )}
                    />
                    <DefinitionItem
                      term="Annual NOI"
                      value={formatCurrency(
                        result.financeSummary.totalAnnualNoiSgd,
                      )}
                    />
                    <DefinitionItem
                      term="Debt service"
                      value={formatCurrency(
                        result.financeSummary.annualDebtServiceSgd,
                      )}
                    />
                    <DefinitionItem
                      term="DSCR"
                      value={formatMetric(result.financeSummary.dscr)}
                    />
                    <DefinitionItem
                      term="Equity"
                      value={formatCurrency(
                        result.financeSummary.equityRequiredSgd,
                      )}
                    />
                    <DefinitionItem
                      term="Exit value"
                      value={formatCurrency(
                        result.financeSummary.estimatedExitValueSgd,
                      )}
                    />
                  </Box>

                  <Typography
                    variant="subtitle2"
                    sx={{
                      fontWeight: 700,
                      mt: 'var(--ob-space-150)',
                      mb: 'var(--ob-space-075)',
                    }}
                  >
                    Finance notes
                  </Typography>
                  <Box
                    component="ul"
                    sx={{
                      m: 0,
                      pl: 'var(--ob-space-200)',
                      color: 'var(--ob-color-text-secondary)',
                      fontSize: 'var(--ob-font-size-sm)',
                    }}
                  >
                    {result.financeSummary.notes.map((note) => (
                      <li key={note}>{note}</li>
                    ))}
                  </Box>
                </Card>
              </Grid>
            </Grid>

            {/* Rules and next actions */}
            <Grid container spacing="var(--ob-space-200)">
              <Grid item xs={12} md={6}>
                <Card
                  variant="default"
                  sx={{ p: 'var(--ob-space-200)', height: '100%' }}
                >
                  <Typography
                    variant="subtitle1"
                    sx={{ fontWeight: 700, mb: 'var(--ob-space-150)' }}
                  >
                    Why this screen says no
                  </Typography>
                  <Box
                    component="ul"
                    sx={{
                      m: 0,
                      pl: 'var(--ob-space-200)',
                      color: 'var(--ob-color-text-secondary)',
                      fontSize: 'var(--ob-font-size-sm)',
                    }}
                  >
                    {result.feasibilityRules.map((rule) => (
                      <Box
                        component="li"
                        key={rule.id}
                        sx={{ mb: 'var(--ob-space-050)' }}
                      >
                        <Typography
                          component="strong"
                          sx={{
                            fontWeight: 'var(--ob-font-weight-semibold)',
                            color: 'var(--ob-color-text-primary)',
                            fontSize: 'var(--ob-font-size-sm)',
                          }}
                        >
                          {rule.title}:
                        </Typography>{' '}
                        {rule.status}
                        {rule.notes ? ` — ${rule.notes}` : ''}
                      </Box>
                    ))}
                  </Box>
                </Card>
              </Grid>

              <Grid item xs={12} md={6}>
                <Card
                  variant="default"
                  sx={{ p: 'var(--ob-space-200)', height: '100%' }}
                >
                  <Typography
                    variant="subtitle1"
                    sx={{ fontWeight: 700, mb: 'var(--ob-space-150)' }}
                  >
                    Next actions
                  </Typography>
                  <Box
                    component="ul"
                    sx={{
                      m: 0,
                      pl: 'var(--ob-space-200)',
                      color: 'var(--ob-color-text-secondary)',
                      fontSize: 'var(--ob-font-size-sm)',
                      mb: 'var(--ob-space-150)',
                    }}
                  >
                    {result.recommendations.map((recommendation) => (
                      <li key={recommendation}>{recommendation}</li>
                    ))}
                  </Box>

                  <Stack
                    direction="row"
                    spacing="var(--ob-space-100)"
                    flexWrap="wrap"
                  >
                    <Button
                      variant="primary"
                      size="md"
                      href="/finance"
                      onClick={handleFinanceHandoff}
                    >
                      Carry into finance
                    </Button>
                    <Button
                      variant="secondary"
                      size="md"
                      href="/app/site-acquisition"
                    >
                      Continue in site acquisition
                    </Button>
                  </Stack>

                  {handoffMessage && (
                    <AlertBlock
                      type="success"
                      sx={{ mt: 'var(--ob-space-100)' }}
                    >
                      {handoffMessage}
                    </AlertBlock>
                  )}
                </Card>
              </Grid>
            </Grid>
          </>
        ) : (
          <EmptyState
            title="Run a deal screen"
            description="Fill in the form and run the screen to generate one-page feasibility and finance."
            size="lg"
          />
        )}
      </Stack>
    </Box>
  )
}

export default DealCalculatorPage
