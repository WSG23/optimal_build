import { FormEvent, useMemo, useState } from 'react'
import { Box, Typography, IconButton, useTheme, alpha } from '@mui/material'
import { ArrowForward, Close } from '@mui/icons-material'
import { PieChart, Pie, Cell, ResponsiveContainer, Tooltip } from 'recharts'

import { runFinanceFeasibility } from '../../../api/finance'
import type {
  FinanceScenarioSummary,
  FinanceFeasibilityRequest,
} from '../../../api/finance'
import { Button } from '../../../components/canonical/Button'
import { GlassCard } from '../../../components/canonical/GlassCard'
import { Input } from '../../../components/canonical/Input'
import { useTranslation } from '../../../i18n'

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

function createDefaultAssetRows(): AssetFormRow[] {
  const timestamp = Date.now()
  return DEFAULT_ASSET_ROWS.map((row, index) => ({
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

interface FinanceScenarioCreatorProps {
  projectId: string | number
  projectName: string
  onCreated: (summary: FinanceScenarioSummary) => void
  onError: (message: string) => void
  onRefresh: () => void
}

export function FinanceScenarioCreator({
  projectId,
  projectName,
  onCreated,
  onError,
  onRefresh,
}: FinanceScenarioCreatorProps) {
  const { t } = useTranslation()
  const theme = useTheme()
  const [scenarioName, setScenarioName] = useState('Phase 2C Base Case')
  const [assets, setAssets] = useState<AssetFormRow[]>(() =>
    createDefaultAssetRows(),
  )
  const [saving, setSaving] = useState(false)

  const totalAllocation = useMemo(() => {
    return assets.reduce(
      (acc, asset) => acc + Number(asset.allocationPct || 0),
      0,
    )
  }, [assets])

  const chartData = useMemo(() => {
    const data = assets
      .filter((a) => Number(a.allocationPct) > 0)
      .map((asset, index) => ({
        name: asset.assetType || `Asset ${index + 1}`,
        value: Number(asset.allocationPct),
        color:
          index % 2 === 0
            ? theme.palette.primary.main
            : theme.palette.info.light, // Using theme colors
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
  }, [assets, theme])

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
    setScenarioName('Phase 2C Base Case')
    setAssets(createDefaultAssetRows())
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
          ...BASE_FINANCE_REQUEST,
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
          <GlassCard
            sx={{ p: 'var(--ob-space-100)', mb: 'var(--ob-space-100)' }}
          >
            <Input
              label={t('finance.scenarioCreator.fields.name')}
              value={scenarioName}
              onChange={(event) => setScenarioName(event.target.value)}
              placeholder={t('finance.scenarioCreator.placeholders.name')}
            />
          </GlassCard>

          <GlassCard sx={{ overflow: 'hidden' }}>
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

            <Box sx={{ overflowX: 'auto' }}>
              <Box
                component="table"
                sx={{
                  width: '100%',
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
                    borderColor: 'divider', // or 'var(--ob-color-border-subtle)'
                    verticalAlign: 'middle',
                  },
                  '& tr:last-child td': {
                    borderBottom: 'none',
                  },
                  '& thead th:first-of-type': {
                    minWidth: 'var(--ob-size-drop-zone)',
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
                    <th>{t('finance.scenarioCreator.assets.headers.rent')}</th>
                    <th>
                      {t('finance.scenarioCreator.assets.headers.vacancy')}
                    </th>
                    <th>
                      {t('finance.scenarioCreator.assets.headers.revenue')}
                    </th>
                    <th>{t('finance.scenarioCreator.assets.headers.capex')}</th>
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
                          startAdornment={
                            <Box
                              sx={{
                                width: 'var(--ob-space-050)',
                                height: 'var(--ob-space-050)',
                                borderRadius: 'var(--ob-radius-pill)',
                                bgcolor: 'primary.main',
                              }}
                            />
                          }
                          sx={{
                            '& .MuiInputBase-root': {
                              boxShadow: 'none',
                              border: 'none',
                              bgcolor: 'transparent',
                            },
                            '& fieldset': { border: 'none !important' },
                          }}
                          // Using simplified input for cleaner look in table as per screenshot
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
          </GlassCard>
        </Box>

        {/* RIGHT COLUMN: ALLOCATION CHART */}
        <Box sx={{ minWidth: 0 }}>
          <GlassCard
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
                }}
              >
                <ResponsiveContainer width="100%" height="100%">
                  <PieChart>
                    <Pie
                      data={chartData}
                      innerRadius={44}
                      outerRadius={58}
                      paddingAngle={2}
                      dataKey="value"
                      stroke="none"
                    >
                      {chartData.map((entry, index) => (
                        <Cell key={`cell-${index}`} fill={entry.color} />
                      ))}
                    </Pie>
                    <Tooltip
                      contentStyle={{
                        borderRadius: 'var(--ob-radius-sm)',
                        border: 'none',
                        boxShadow: 'var(--ob-shadow-md)',
                        backgroundColor: theme.palette.background.paper,
                      }}
                    />
                  </PieChart>
                </ResponsiveContainer>
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

            <GlassCard
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
            </GlassCard>

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
          </GlassCard>
        </Box>
      </Box>
    </Box>
  )
}
export default FinanceScenarioCreator
