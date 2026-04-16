import { FormEvent, useCallback, useEffect, useMemo, useState } from 'react'
import {
  Box,
  Typography,
  IconButton,
  Stack,
  useTheme,
  alpha,
  useMediaQuery,
} from '@mui/material'
import { ArrowForward, Close } from '@mui/icons-material'

import { runFinanceFeasibility } from '../../../api/finance'
import type {
  FinanceScenarioSummary,
  FinanceFeasibilityRequest,
} from '../../../api/finance'
import { Button } from '../../../components/canonical/Button'
import { Card } from '../../../components/canonical/Card'
import { Input } from '../../../components/canonical/Input'
import { useTranslation } from '../../../i18n'
import { AllocationRing } from './AllocationRing'

type AssetFormRow = {
  id: string
  assetType: string
  allocationPct: string
  niaSqm: string
  rentPsmMonth: string
  vacancyPct: string
  opexPct: string
  estimatedRevenue: string
  estimatedCapex: string
  absorptionMonths: string
  riskLevel: string
  notes: string
}

const DEFAULT_ASSET_ROWS: Array<Omit<AssetFormRow, 'id'>> = [
  {
    assetType: 'Office',
    allocationPct: '55',
    niaSqm: '1000',
    rentPsmMonth: '10',
    vacancyPct: '5',
    opexPct: '20',
    estimatedRevenue: '91200',
    estimatedCapex: '500000',
    absorptionMonths: '6',
    riskLevel: 'balanced',
    notes: 'Office baseline with healthy demand.',
  },
  {
    assetType: 'Retail',
    allocationPct: '25',
    niaSqm: '500',
    rentPsmMonth: '8',
    vacancyPct: '10',
    opexPct: '25',
    estimatedRevenue: '32400',
    estimatedCapex: '150000',
    absorptionMonths: '9',
    riskLevel: 'moderate',
    notes: 'Retail uplift assumes curated tenant mix.',
  },
]

function createAssetRows(
  rows: Array<Omit<AssetFormRow, 'id'>>,
): AssetFormRow[] {
  const timestamp = Date.now()
  return rows.map((row, index) => ({
    id: `asset-${timestamp}-${index}`,
    ...row,
  }))
}

const BASE_FINANCE_REQUEST: Omit<
  FinanceFeasibilityRequest['scenario'],
  'name' | 'assetMix'
> = {
  description: 'Phase 2C feasibility scenario',
  currency: 'SGD',
  isPrimary: true,
  costEscalation: {
    amount: '38950000',
    basePeriod: '2024-Q1',
    seriesName: 'construction_all_in',
    jurisdiction: 'SG',
  },
  cashFlow: {
    discountRate: '0.085',
    cashFlows: ['-38950000', '5000000', '7500000', '9500000', '12000000'],
  },
  drawdownSchedule: [
    { period: 'M1', equityDraw: '6000000', debtDraw: '0' },
    { period: 'M2', equityDraw: '4500000', debtDraw: '2500000' },
    { period: 'M3', equityDraw: '3000000', debtDraw: '4500000' },
    { period: 'M4', equityDraw: '1200000', debtDraw: '5000000' },
    { period: 'M5', equityDraw: '800000', debtDraw: '6500000' },
    { period: 'M6', equityDraw: '300000', debtDraw: '4870000' },
  ],
  constructionLoan: {
    interestRate: '0.05',
    periodsPerYear: 12,
    capitaliseInterest: true,
    facilities: [
      {
        name: 'Senior Loan',
        amount: '23370000',
        interestRate: '0.045',
        periodsPerYear: 12,
        capitaliseInterest: true,
      },
      {
        name: 'Mezz Loan',
        amount: '6000000',
        interestRate: '0.08',
        periodsPerYear: 12,
        capitaliseInterest: false,
        upfrontFeePct: '1.0',
        exitFeePct: '2.0',
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

type FinanceScenarioDefaults = Omit<
  FinanceFeasibilityRequest['scenario'],
  'name' | 'assetMix'
>

type FinanceTemplateDefinition = {
  id: string
  label: string
  description: string
  scenarioName: string
  scenarioDefaults: FinanceScenarioDefaults
  assets: Array<Omit<AssetFormRow, 'id'>>
}

const SG_FINANCE_TEMPLATES: FinanceTemplateDefinition[] = [
  {
    id: 'sg_mixed_use',
    label: 'SG Mixed-Use',
    description:
      'Balanced residential-retail podium scheme for early Singapore feasibility.',
    scenarioName: 'Singapore Mixed-Use Base Case',
    scenarioDefaults: BASE_FINANCE_REQUEST,
    assets: [
      {
        assetType: 'Residential',
        allocationPct: '60',
        niaSqm: '1800',
        rentPsmMonth: '7',
        vacancyPct: '3',
        opexPct: '12',
        estimatedRevenue: '146664',
        estimatedCapex: '680000',
        absorptionMonths: '7',
        riskLevel: 'balanced',
        notes: 'Assumes city-fringe apartment pricing and stable demand.',
      },
      {
        assetType: 'Retail Podium',
        allocationPct: '25',
        niaSqm: '620',
        rentPsmMonth: '11',
        vacancyPct: '8',
        opexPct: '24',
        estimatedRevenue: '75293',
        estimatedCapex: '210000',
        absorptionMonths: '9',
        riskLevel: 'moderate',
        notes: 'Neighbourhood-serving retail with curated tenant mix.',
      },
      {
        assetType: 'Office',
        allocationPct: '15',
        niaSqm: '420',
        rentPsmMonth: '10',
        vacancyPct: '6',
        opexPct: '18',
        estimatedRevenue: '47376',
        estimatedCapex: '160000',
        absorptionMonths: '8',
        riskLevel: 'moderate',
        notes: 'Flexible office floors above podium retail.',
      },
    ],
  },
  {
    id: 'sg_repositioning',
    label: 'Office Repositioning',
    description:
      'CBD or fringe-office repositioning with capex-led upside and staged leasing risk.',
    scenarioName: 'Singapore Office Repositioning',
    scenarioDefaults: {
      ...BASE_FINANCE_REQUEST,
      cashFlow: {
        discountRate: '0.09',
        cashFlows: ['-32500000', '4500000', '7200000', '10400000', '13800000'],
      },
      sensitivityBands: [
        { parameter: 'Rent', low: '-10', base: '0', high: '8' },
        { parameter: 'Construction Cost', low: '12', base: '0', high: '-4' },
        {
          parameter: 'Interest Rate (delta %)',
          low: '1.75',
          base: '0',
          high: '-0.5',
        },
      ],
    },
    assets: [
      {
        assetType: 'Grade B+ Office',
        allocationPct: '80',
        niaSqm: '2200',
        rentPsmMonth: '12',
        vacancyPct: '7',
        opexPct: '19',
        estimatedRevenue: '294624',
        estimatedCapex: '980000',
        absorptionMonths: '10',
        riskLevel: 'moderate',
        notes: 'Repositioned office floors with lobby and MEP upgrade.',
      },
      {
        assetType: 'Retail / F&B',
        allocationPct: '20',
        niaSqm: '500',
        rentPsmMonth: '13',
        vacancyPct: '9',
        opexPct: '28',
        estimatedRevenue: '70980',
        estimatedCapex: '240000',
        absorptionMonths: '12',
        riskLevel: 'high',
        notes: 'Ground-floor activation and amenity-led rent premium.',
      },
    ],
  },
  {
    id: 'sg_industrial',
    label: 'Industrial / Adaptive Reuse',
    description:
      'Light industrial or adaptive-reuse underwriting with conservative rent and debt assumptions.',
    scenarioName: 'Singapore Industrial Reuse',
    scenarioDefaults: {
      ...BASE_FINANCE_REQUEST,
      cashFlow: {
        discountRate: '0.0825',
        cashFlows: ['-27800000', '3200000', '6100000', '8600000', '11100000'],
      },
      constructionLoan: {
        interestRate: '0.0475',
        periodsPerYear: 12,
        capitaliseInterest: true,
        facilities: [
          {
            name: 'Senior Loan',
            amount: '18370000',
            interestRate: '0.0425',
            periodsPerYear: 12,
            capitaliseInterest: true,
          },
        ],
      },
    },
    assets: [
      {
        assetType: 'Light Industrial',
        allocationPct: '70',
        niaSqm: '2600',
        rentPsmMonth: '6',
        vacancyPct: '5',
        opexPct: '16',
        estimatedRevenue: '177840',
        estimatedCapex: '620000',
        absorptionMonths: '6',
        riskLevel: 'balanced',
        notes: 'Assumes JTC-compatible positioning and efficient floorplates.',
      },
      {
        assetType: 'Ancillary Office',
        allocationPct: '20',
        niaSqm: '700',
        rentPsmMonth: '8',
        vacancyPct: '7',
        opexPct: '18',
        estimatedRevenue: '62496',
        estimatedCapex: '170000',
        absorptionMonths: '7',
        riskLevel: 'moderate',
        notes: 'Support office space tied to industrial occupiers.',
      },
      {
        assetType: 'Retail Support',
        allocationPct: '10',
        niaSqm: '220',
        rentPsmMonth: '9',
        vacancyPct: '10',
        opexPct: '24',
        estimatedRevenue: '21384',
        estimatedCapex: '90000',
        absorptionMonths: '9',
        riskLevel: 'moderate',
        notes: 'Small convenience-led retail component.',
      },
    ],
  },
]

function cloneScenarioDefaults(
  template: FinanceScenarioDefaults,
): FinanceScenarioDefaults {
  return {
    ...template,
    costEscalation: { ...template.costEscalation },
    cashFlow: {
      ...template.cashFlow,
      cashFlows: [...template.cashFlow.cashFlows],
    },
    drawdownSchedule: template.drawdownSchedule?.map((entry) => ({ ...entry })),
    constructionLoan: template.constructionLoan
      ? {
          ...template.constructionLoan,
          facilities: template.constructionLoan.facilities?.map((facility) => ({
            ...facility,
            metadata: facility.metadata
              ? { ...facility.metadata }
              : facility.metadata,
          })),
        }
      : template.constructionLoan,
    sensitivityBands: template.sensitivityBands?.map((band) => ({ ...band })),
  }
}

interface FinanceScenarioCreatorProps {
  projectId: string | number
  projectName: string
  initialTemplateId?: string | null
  onCreated: (summary: FinanceScenarioSummary) => void
  onError: (message: string) => void
  onRefresh: () => void
}

export function FinanceScenarioCreator({
  projectId,
  projectName,
  initialTemplateId,
  onCreated,
  onError,
  onRefresh,
}: FinanceScenarioCreatorProps) {
  const { t } = useTranslation()
  const theme = useTheme()
  const isCompactLayout = useMediaQuery(theme.breakpoints.down('md'))
  const [selectedTemplateId, setSelectedTemplateId] =
    useState<string>('sg_mixed_use')
  const [requestDefaults, setRequestDefaults] =
    useState<FinanceScenarioDefaults>(() =>
      cloneScenarioDefaults(BASE_FINANCE_REQUEST),
    )
  const [scenarioName, setScenarioName] = useState(
    'Singapore Mixed-Use Base Case',
  )
  const [assets, setAssets] = useState<AssetFormRow[]>(() =>
    createAssetRows(SG_FINANCE_TEMPLATES[0].assets),
  )
  const [saving, setSaving] = useState(false)

  const applyTemplate = useCallback((templateId: string) => {
    const template =
      SG_FINANCE_TEMPLATES.find((entry) => entry.id === templateId) ??
      SG_FINANCE_TEMPLATES[0]
    setSelectedTemplateId(template.id)
    setScenarioName(template.scenarioName)
    setRequestDefaults(cloneScenarioDefaults(template.scenarioDefaults))
    setAssets(createAssetRows(template.assets))
  }, [])

  useEffect(() => {
    if (!initialTemplateId) {
      return
    }
    if (initialTemplateId === selectedTemplateId) {
      return
    }
    applyTemplate(initialTemplateId)
  }, [applyTemplate, initialTemplateId, selectedTemplateId])

  const totalAllocation = useMemo(() => {
    return assets.reduce(
      (acc, asset) => acc + Number(asset.allocationPct || 0),
      0,
    )
  }, [assets])

  const chartData = useMemo(() => {
    // Cyan family palette for chart visualization
    const cyanPalette = ['#00f3ff', '#0096cc', '#0077a3', '#005577']

    const data = assets
      .filter((a) => Number(a.allocationPct) > 0)
      .map((asset, index) => ({
        name: asset.assetType || `Asset ${index + 1}`,
        value: Number(asset.allocationPct),
        color: cyanPalette[index % cyanPalette.length],
      }))

    const allocated = data.reduce((acc, item) => acc + item.value, 0)
    const unallocated = Math.max(0, 100 - allocated)

    if (unallocated > 0) {
      data.push({
        name: 'Pending',
        value: unallocated,
        color: theme.palette.action.disabledBackground,
      })
    }
    return data
  }, [assets, theme.palette.action.disabledBackground])

  const unallocated = Math.max(0, 100 - totalAllocation)

  const handleAssetChange = (
    id: string,
    key: keyof AssetFormRow,
    value: string,
  ) => {
    setAssets((prev) =>
      prev.map((asset) => {
        if (asset.id !== id) return asset

        let updated = { ...asset, [key]: value }

        if (
          key === 'vacancyPct' ||
          key === 'rentPsmMonth' ||
          key === 'niaSqm'
        ) {
          const nia = Number(updated.niaSqm) || 0
          const rent = Number(updated.rentPsmMonth) || 0
          const vacancy = Number(updated.vacancyPct) || 0

          // Simple annual revenue calc: NIA * Rent * 12 * (1 - Vacancy/100)
          if (nia && rent) {
            const annualRev = nia * rent * 12 * (1 - vacancy / 100)
            updated.estimatedRevenue = annualRev.toFixed(0)
          }
        }
        return updated
      }),
    )
  }

  const totalRevenue = useMemo(() => {
    return assets.reduce(
      (acc, asset) => acc + (Number(asset.estimatedRevenue) || 0),
      0,
    )
  }, [assets])

  const handleAddAsset = () => {
    const nextIndex = assets.length
    setAssets((prev) => [
      ...prev,
      {
        ...DEFAULT_ASSET_ROWS[0],
        id: `asset-${Date.now()}-${nextIndex}`,
        assetType: '',
        allocationPct: '',
        notes: '',
      },
    ])
  }

  const handleRemoveAsset = (id: string) => {
    setAssets((prev) => prev.filter((asset) => asset.id !== id))
  }

  const handleReset = () => {
    applyTemplate(selectedTemplateId)
  }

  const handleSubmit = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault()
    if (saving) {
      return
    }
    if (!scenarioName.trim()) {
      onError(
        t('finance.scenarioCreator.errors.nameRequired', {
          defaultValue: 'Enter a scenario name.',
        }),
      )
      return
    }

    const filteredAssets = assets.filter((asset) => asset.assetType.trim())
    if (filteredAssets.length === 0) {
      onError(
        t('finance.scenarioCreator.errors.assetRequired', {
          defaultValue: 'Add at least one asset before running feasibility.',
        }),
      )
      return
    }

    setSaving(true)
    try {
      const request: FinanceFeasibilityRequest = {
        projectId,
        projectName,
        scenario: {
          ...requestDefaults,
          name: scenarioName.trim(),
          assetMix: filteredAssets.map((asset) => ({
            assetType: asset.assetType.trim(),
            allocationPct: asset.allocationPct.trim() || undefined,
            niaSqm: asset.niaSqm.trim() || undefined,
            rentPsmMonth: asset.rentPsmMonth.trim() || undefined,
            stabilisedVacancyPct: asset.vacancyPct.trim() || undefined,
            opexPctOfRent: asset.opexPct.trim() || undefined,
            estimatedRevenueSgd: asset.estimatedRevenue.trim() || undefined,
            estimatedCapexSgd: asset.estimatedCapex.trim() || undefined,
            absorptionMonths: asset.absorptionMonths.trim() || undefined,
            riskLevel: asset.riskLevel.trim() || undefined,
            notes: asset.notes ? [asset.notes] : [],
          })),
        },
      }
      const summary = await runFinanceFeasibility(request)
      onCreated(summary)
      onRefresh()
      handleReset()
    } catch (error) {
      const message =
        error instanceof Error
          ? error.message
          : t('finance.scenarioCreator.errors.generic', {
              defaultValue: 'Unable to run finance feasibility.',
            })
      onError(message)
    } finally {
      setSaving(false)
    }
  }

  const selectedTemplate =
    SG_FINANCE_TEMPLATES.find(
      (template) => template.id === selectedTemplateId,
    ) ?? SG_FINANCE_TEMPLATES[0]

  return (
    <Box component="form" onSubmit={handleSubmit}>
      <Box
        sx={{
          display: 'grid',
          gridTemplateColumns: {
            xs: '1fr',
            lg: 'minmax(0, 1fr) var(--ob-size-finance-summary-panel)',
          },
          gap: 'var(--ob-space-150)',
        }}
      >
        {/* LEFT COLUMN: ASSET MIX INPUTS */}
        <Box sx={{ minWidth: 0 }}>
          <Card sx={{ p: 'var(--ob-space-100)', mb: 'var(--ob-space-100)' }}>
            <Stack spacing={1.25}>
              <Box>
                <Typography variant="subtitle2" sx={{ mb: 0.75 }}>
                  Singapore deal templates
                </Typography>
                <Stack
                  direction={{ xs: 'column', md: 'row' }}
                  spacing={1}
                  useFlexGap
                  flexWrap="wrap"
                >
                  {SG_FINANCE_TEMPLATES.map((template) => {
                    const active = template.id === selectedTemplateId
                    return (
                      <Box
                        key={template.id}
                        component="button"
                        type="button"
                        onClick={() => applyTemplate(template.id)}
                        sx={{
                          textAlign: 'left',
                          p: 'var(--ob-space-100)',
                          borderRadius: 'var(--ob-radius-sm)',
                          border: '1px solid',
                          borderColor: active ? 'primary.main' : 'divider',
                          backgroundColor: active
                            ? 'rgba(0, 243, 255, 0.08)'
                            : 'transparent',
                          color: 'inherit',
                          cursor: 'pointer',
                          minWidth: { xs: '100%', md: 180 },
                        }}
                      >
                        <Typography variant="body2" sx={{ fontWeight: 700 }}>
                          {template.label}
                        </Typography>
                        <Typography
                          variant="caption"
                          sx={{ color: 'text.secondary' }}
                        >
                          {template.description}
                        </Typography>
                      </Box>
                    )
                  })}
                </Stack>
              </Box>

              <Box
                sx={{
                  p: 'var(--ob-space-100)',
                  borderRadius: 'var(--ob-radius-sm)',
                  bgcolor: alpha(theme.palette.primary.main, 0.06),
                }}
              >
                <Typography variant="body2" sx={{ fontWeight: 700 }}>
                  {selectedTemplate.label}
                </Typography>
                <Typography variant="body2" color="text.secondary">
                  {selectedTemplate.description}
                </Typography>
              </Box>

              <Input
                label={t('finance.scenarioCreator.fields.name')}
                value={scenarioName}
                onChange={(event) => setScenarioName(event.target.value)}
                placeholder={t('finance.scenarioCreator.placeholders.name')}
              />
            </Stack>
          </Card>

          <Card sx={{ overflow: 'hidden' }}>
            <Box
              sx={{
                px: 'var(--ob-space-150)',
                py: 'var(--ob-space-125)',
                borderBottom: 1,
                borderColor: 'divider',
                bgcolor: alpha(theme.palette.background.default, 0.5),
                display: 'flex',
                justifyContent: 'space-between',
                alignItems: 'center',
              }}
            >
              <Typography variant="h6" sx={{ fontWeight: 600 }}>
                {t('finance.scenarioCreator.title')}
              </Typography>
              <Button variant="ghost" size="sm" onClick={handleReset}>
                {t('finance.scenarioCreator.actions.reset')}
              </Button>
            </Box>

            {isCompactLayout ? (
              <Stack
                spacing="var(--ob-space-100)"
                sx={{ p: 'var(--ob-space-100)' }}
              >
                {assets.map((asset, index) => (
                  <Box
                    key={asset.id}
                    sx={{
                      border: '1px solid',
                      borderColor: 'divider',
                      borderRadius: 'var(--ob-radius-sm)',
                      p: 'var(--ob-space-100)',
                    }}
                  >
                    <Stack
                      direction="row"
                      justifyContent="space-between"
                      alignItems="center"
                      spacing="var(--ob-space-100)"
                      sx={{ mb: 'var(--ob-space-100)' }}
                    >
                      <Typography variant="subtitle2" sx={{ fontWeight: 600 }}>
                        Asset {index + 1}
                      </Typography>
                      <IconButton
                        aria-label={t('finance.scenarioCreator.actions.remove')}
                        size="small"
                        onClick={() => handleRemoveAsset(asset.id)}
                        disabled={assets.length <= 1}
                        sx={{
                          borderRadius: 'var(--ob-radius-xs)',
                          border: 'var(--ob-border-fine)',
                        }}
                      >
                        <Close fontSize="small" />
                      </IconButton>
                    </Stack>

                    <Stack spacing="var(--ob-space-100)">
                      <Input
                        label={t(
                          'finance.scenarioCreator.assets.headers.assetType',
                        )}
                        value={asset.assetType}
                        onChange={(e) =>
                          handleAssetChange(
                            asset.id,
                            'assetType',
                            e.target.value,
                          )
                        }
                        placeholder="Type"
                        size="small"
                      />
                      <Input
                        label={t('finance.scenarioCreator.fields.allocation')}
                        value={asset.allocationPct}
                        onChange={(e) =>
                          handleAssetChange(
                            asset.id,
                            'allocationPct',
                            e.target.value,
                          )
                        }
                        type="number"
                        size="small"
                        endAdornment="%"
                      />
                      <Input
                        label={t('finance.scenarioCreator.assets.headers.nia')}
                        value={asset.niaSqm}
                        onChange={(e) =>
                          handleAssetChange(asset.id, 'niaSqm', e.target.value)
                        }
                        type="number"
                        size="small"
                      />
                      <Input
                        label={t('finance.scenarioCreator.assets.headers.rent')}
                        value={asset.rentPsmMonth}
                        onChange={(e) =>
                          handleAssetChange(
                            asset.id,
                            'rentPsmMonth',
                            e.target.value,
                          )
                        }
                        type="number"
                        size="small"
                        startAdornment="$"
                      />
                      <Input
                        label={t(
                          'finance.scenarioCreator.assets.headers.vacancy',
                        )}
                        value={asset.vacancyPct}
                        onChange={(e) =>
                          handleAssetChange(
                            asset.id,
                            'vacancyPct',
                            e.target.value,
                          )
                        }
                        type="number"
                        size="small"
                        endAdornment="%"
                      />
                      <Input
                        label={t(
                          'finance.scenarioCreator.assets.headers.capex',
                        )}
                        value={asset.estimatedCapex}
                        onChange={(e) =>
                          handleAssetChange(
                            asset.id,
                            'estimatedCapex',
                            e.target.value,
                          )
                        }
                        type="number"
                        size="small"
                        startAdornment="$"
                      />
                      <Box>
                        <Typography variant="caption" color="text.secondary">
                          {t('finance.scenarioCreator.assets.headers.revenue')}
                        </Typography>
                        <Typography
                          variant="body2"
                          sx={{
                            mt: 'var(--ob-space-025)',
                            fontFamily: 'var(--ob-font-family-mono)',
                            fontWeight: 600,
                          }}
                        >
                          ${Number(asset.estimatedRevenue).toLocaleString()}
                        </Typography>
                      </Box>
                    </Stack>
                  </Box>
                ))}
              </Stack>
            ) : (
              <Box sx={{ overflowX: 'auto' }}>
                <Box
                  component="table"
                  sx={{
                    width: '100%',
                    minWidth: '960px',
                    borderCollapse: 'separate',
                    borderSpacing: 0,
                    '& th': {
                      px: 'var(--ob-space-100)',
                      py: 'var(--ob-space-100)',
                      textAlign: 'left',
                      color: 'text.secondary',
                      fontSize: 'var(--ob-font-size-xs)',
                      fontWeight: 600,
                      textTransform: 'uppercase',
                      letterSpacing: 'var(--ob-letter-spacing-wider)',
                      whiteSpace: 'nowrap',
                      borderBottom: 1,
                      borderColor: 'divider',
                    },
                    '& td': {
                      px: 'var(--ob-space-100)',
                      py: 'var(--ob-space-100)',
                      borderBottom: 1,
                      borderColor: 'divider',
                      verticalAlign: 'middle',
                    },
                    '& tr:last-child td': {
                      borderBottom: 'none',
                    },
                    '& th:nth-of-type(1), & td:nth-of-type(1)': {
                      minWidth: '160px',
                    },
                    '& th:nth-of-type(2), & td:nth-of-type(2)': {
                      minWidth: '120px',
                    },
                    '& th:nth-of-type(3), & td:nth-of-type(3)': {
                      minWidth: '112px',
                    },
                    '& th:nth-of-type(4), & td:nth-of-type(4)': {
                      minWidth: '128px',
                    },
                    '& th:nth-of-type(5), & td:nth-of-type(5)': {
                      minWidth: '128px',
                    },
                    '& th:nth-of-type(6), & td:nth-of-type(6)': {
                      minWidth: '140px',
                    },
                    '& th:nth-of-type(7), & td:nth-of-type(7)': {
                      minWidth: '140px',
                    },
                    '& th:nth-of-type(8), & td:nth-of-type(8)': {
                      minWidth: '72px',
                      width: '72px',
                    },
                  }}
                >
                  <thead>
                    <tr>
                      <th>
                        {t('finance.scenarioCreator.assets.headers.assetType')}
                      </th>
                      <th>{t('finance.scenarioCreator.fields.allocation')}</th>
                      <th>{t('finance.scenarioCreator.assets.headers.nia')}</th>
                      <th>
                        {t('finance.scenarioCreator.assets.headers.rent')}
                      </th>
                      <th>
                        {t('finance.scenarioCreator.assets.headers.vacancy')}
                      </th>
                      <th>
                        {t('finance.scenarioCreator.assets.headers.revenue')}
                      </th>
                      <th>
                        {t('finance.scenarioCreator.assets.headers.capex')}
                      </th>
                      <th>{t('finance.scenarioCreator.actions.remove')}</th>
                    </tr>
                  </thead>
                  <tbody>
                    {assets.map((asset) => (
                      <tr key={asset.id}>
                        <td>
                          <Input
                            value={asset.assetType}
                            onChange={(e) =>
                              handleAssetChange(
                                asset.id,
                                'assetType',
                                e.target.value,
                              )
                            }
                            placeholder="Type"
                            size="small"
                          />
                        </td>
                        <td>
                          <Input
                            value={asset.allocationPct}
                            onChange={(e) =>
                              handleAssetChange(
                                asset.id,
                                'allocationPct',
                                e.target.value,
                              )
                            }
                            type="number"
                            size="small"
                            endAdornment="%"
                          />
                        </td>
                        <td>
                          <Input
                            value={asset.niaSqm}
                            onChange={(e) =>
                              handleAssetChange(
                                asset.id,
                                'niaSqm',
                                e.target.value,
                              )
                            }
                            type="number"
                            size="small"
                          />
                        </td>
                        <td>
                          <Input
                            value={asset.rentPsmMonth}
                            onChange={(e) =>
                              handleAssetChange(
                                asset.id,
                                'rentPsmMonth',
                                e.target.value,
                              )
                            }
                            type="number"
                            size="small"
                            startAdornment="$"
                          />
                        </td>
                        <td>
                          <Input
                            value={asset.vacancyPct}
                            onChange={(e) =>
                              handleAssetChange(
                                asset.id,
                                'vacancyPct',
                                e.target.value,
                              )
                            }
                            type="number"
                            size="small"
                            endAdornment="%"
                          />
                        </td>
                        <td>
                          <Typography
                            variant="body2"
                            sx={{
                              fontFamily: 'var(--ob-font-family-mono)',
                              fontWeight: 600,
                            }}
                          >
                            ${Number(asset.estimatedRevenue).toLocaleString()}
                          </Typography>
                        </td>
                        <td>
                          <Input
                            value={asset.estimatedCapex}
                            onChange={(e) =>
                              handleAssetChange(
                                asset.id,
                                'estimatedCapex',
                                e.target.value,
                              )
                            }
                            type="number"
                            size="small"
                            startAdornment="$"
                          />
                        </td>
                        <td>
                          <IconButton
                            aria-label={t(
                              'finance.scenarioCreator.actions.remove',
                            )}
                            size="small"
                            onClick={() => handleRemoveAsset(asset.id)}
                            disabled={assets.length <= 1}
                            sx={{
                              borderRadius: 'var(--ob-radius-xs)',
                              border: 'var(--ob-border-fine)',
                            }}
                          >
                            <Close fontSize="small" />
                          </IconButton>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </Box>
              </Box>
            )}
            <Box
              sx={{
                p: 'var(--ob-space-100)',
                borderTop: 1,
                borderColor: 'divider',
              }}
            >
              <Button variant="ghost" size="sm" onClick={handleAddAsset}>
                {t('finance.scenarioCreator.actions.addAsset')}
              </Button>
            </Box>
          </Card>
        </Box>

        {/* RIGHT COLUMN: ALLOCATION CHART */}
        <Box sx={{ minWidth: 0 }}>
          <Card
            sx={{
              p: 'var(--ob-space-150)',
              height: '100%',
              display: 'flex',
              flexDirection: 'column',
            }}
          >
            <Typography
              variant="h6"
              sx={{
                fontWeight: 600,
                mb: 'var(--ob-space-150)',
                textTransform: 'uppercase',
                letterSpacing: 'var(--ob-letter-spacing-wider)',
                fontSize: 'var(--ob-font-size-xs)',
              }}
            >
              {t('finance.allocation.title', {
                defaultValue: 'ALLOCATION MIX',
              })}
            </Typography>

            <Box
              sx={{
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                flex: 1,
                gap: 'var(--ob-space-200)',
              }}
            >
              <Box
                sx={{
                  position: 'relative',
                  width: 'var(--ob-size-drop-zone)',
                  height: 'var(--ob-size-drop-zone)',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                }}
              >
                <AllocationRing
                  data={chartData}
                  totalAllocation={100 - unallocated}
                  size={160}
                />
                {/* Center text for unallocated like screenshot */}
                <Box
                  sx={{
                    position: 'absolute',
                    top: '50%',
                    left: '50%',
                    transform: 'translate(-50%, -50%)',
                    textAlign: 'center',
                  }}
                >
                  <Typography
                    variant="caption"
                    sx={{
                      color: 'text.secondary',
                      display: 'block',
                      lineHeight: 1,
                    }}
                  >
                    Pending
                  </Typography>
                  <Typography
                    variant="h6"
                    sx={{ fontWeight: 700, lineHeight: 1 }}
                  >
                    {unallocated}%
                  </Typography>
                </Box>
              </Box>

              {/* Legend */}
              <Box
                sx={{
                  display: 'flex',
                  flexDirection: 'column',
                  gap: 'var(--ob-space-050)',
                }}
              >
                {chartData
                  .filter((d) => d.name !== 'Pending')
                  .map((entry) => (
                    <Box
                      key={entry.name}
                      sx={{
                        display: 'flex',
                        alignItems: 'center',
                        gap: 'var(--ob-space-050)',
                      }}
                    >
                      <Box
                        sx={{
                          width: 'var(--ob-space-050)',
                          height: 'var(--ob-space-050)',
                          borderRadius: 'var(--ob-radius-pill)',
                          bgcolor: entry.color,
                        }}
                      />
                      <Typography
                        variant="body2"
                        sx={{ color: 'text.secondary', minWidth: 60 }}
                      >
                        {entry.name}
                      </Typography>
                      <Typography variant="body2" sx={{ fontWeight: 600 }}>
                        {entry.value}%
                      </Typography>
                    </Box>
                  ))}
              </Box>
            </Box>

            <Card
              sx={{
                mt: 'var(--ob-space-200)',
                p: 'var(--ob-space-100)',
                bgcolor: 'action.hover',
                border: 'none',
              }}
            >
              <Typography
                variant="caption"
                sx={{
                  color: 'text.secondary',
                  display: 'block',
                  mb: 'var(--ob-space-025)',
                }}
              >
                {t('finance.scenarioCreator.totalAnnualRevenue')}
              </Typography>
              <Typography variant="h4" sx={{ fontWeight: 700 }}>
                ${totalRevenue.toLocaleString()}
              </Typography>
            </Card>

            <Button
              type="submit"
              fullWidth
              variant="primary"
              size="lg"
              sx={{ mt: 'var(--ob-space-150)' }}
              endIcon={<ArrowForward fontSize="small" />}
              disabled={saving}
            >
              {saving
                ? t('finance.scenarioCreator.actions.saving')
                : t('finance.scenarioCreator.actions.submit')}
            </Button>
          </Card>
        </Box>
      </Box>
    </Box>
  )
}
export default FinanceScenarioCreator
