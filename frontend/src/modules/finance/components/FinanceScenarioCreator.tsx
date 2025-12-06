import { FormEvent, useMemo, useState } from 'react'
import { Cell, Pie, PieChart, ResponsiveContainer, Tooltip } from 'recharts'


import {
  runFinanceFeasibility,
  type FinanceScenarioSummary,
  type FinanceFeasibilityRequest,
} from '../../../api/finance'
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
    assetType: 'office',
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
    assetType: 'retail',
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
    { parameter: 'Interest Rate (delta %)', low: '1.50', base: '0', high: '-0.75' },
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
  const [scenarioName, setScenarioName] = useState('Phase 2C Base Case')
  const [assets, setAssets] = useState<AssetFormRow[]>(() =>
    createDefaultAssetRows(),
  )
  const [saving, setSaving] = useState(false)

  const totalAllocation = useMemo(() => {
    return assets.reduce((acc, asset) => acc + Number(asset.allocationPct || 0), 0)
  }, [assets])

  const chartData = useMemo(() => {
    const data = assets
      .filter(a => Number(a.allocationPct) > 0)
      .map((asset, index) => ({
        name: asset.assetType || `Asset ${index + 1}`,
        value: Number(asset.allocationPct),
        color: index % 2 === 0 ? 'var(--ob-color-brand-primary)' : 'var(--ob-color-brand-primary-emphasis)' // Basic alternation
      }))

    const allocated = data.reduce((acc, item) => acc + item.value, 0)
    const unallocated = Math.max(0, 100 - allocated)

    if (unallocated > 0) {
        data.push({
            name: 'Unallocated',
            value: unallocated,
            color: 'var(--ob-color-warning-soft)' // Use warning color/soft
        })
    }
    return data
  }, [assets])

  const unallocated = Math.max(0, 100 - totalAllocation)

  const handleAssetChange = (
    id: string,
    key: keyof AssetFormRow,
    value: string,
  ) => {
    setAssets((prev) =>
      prev.map((asset) => (asset.id === id ? { ...asset, [key]: value } : asset)),
    )
  }

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
      onError(t('finance.scenarioCreator.errors.nameRequired'))
      return
    }
    const filteredAssets = assets.filter((asset) => asset.assetType.trim())
    if (filteredAssets.length === 0) {
      onError(t('finance.scenarioCreator.errors.assetRequired'))
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
      setAssets(createDefaultAssetRows())
      setScenarioName('Phase 2C Base Case')
    } catch (error) {
      const message =
        error instanceof Error
          ? error.message
          : t('finance.scenarioCreator.errors.generic')
      onError(message)
    } finally {
      setSaving(false)
    }
  }

  return (
    <section className="finance-scenario-creator">
      <header className="finance-scenario-creator__header">
        <div>
          <h2>{t('finance.scenarioCreator.title')}</h2>
          <p>{t('finance.scenarioCreator.description')}</p>
        </div>
        <div className="finance-scenario-creator__metrics">
          <div className="finance-scenario-creator__chart-container">
            <div style={{ width: 120, height: 120 }}>
                <ResponsiveContainer width="100%" height="100%">
                    <PieChart>
                        <Pie
                            data={chartData}
                            dataKey="value"
                            innerRadius={40}
                            outerRadius={60}
                            paddingAngle={2}
                            stroke="none"
                        >
                            {chartData.map((entry) => (
                                <Cell key={entry.name} fill={entry.color} />
                            ))}
                        </Pie>
                        <Tooltip
                            formatter={(value: number) => `${value.toFixed(1)}%`}
                            contentStyle={{ borderRadius: '8px', border: 'none', boxShadow: '0 4px 6px rgba(0,0,0,0.1)' }}
                        />
                    </PieChart>
                </ResponsiveContainer>
            </div>
            <div className="finance-scenario-creator__chart-legend">
                 <div className="finance-scenario-creator__total-allocation">
                    {t('finance.scenarioCreator.allocationTotal', {
                        value: totalAllocation.toFixed(1),
                    })}
                 </div>
                 {unallocated > 0 && (
                     <div className="finance-scenario-creator__chart-legend-item" style={{ color: 'var(--ob-color-warning-strong)' }}>
                        <span className="finance-scenario-creator__legend-color" style={{ background: 'var(--ob-color-warning-strong)' }} />
                        {t('finance.scenarioCreator.unallocated', { defaultValue: 'Unallocated' })} {unallocated.toFixed(1)}%
                     </div>
                 )}
            </div>
          </div>
        </div>
      </header>
      <form className="finance-scenario-creator__form" onSubmit={handleSubmit}>
        <div className="finance-scenario-creator__grid">
          <label className="finance-scenario-creator__field">
            <span>{t('finance.scenarioCreator.fields.name')}</span>
            <input
              type="text"
              value={scenarioName}
              onChange={(event) => setScenarioName(event.target.value)}
              placeholder={t('finance.scenarioCreator.placeholders.name')}
            />
          </label>
          <label className="finance-scenario-creator__field">
            <span>{t('finance.scenarioCreator.fields.projectId')}</span>
            <input value={projectId} readOnly />
          </label>
          {projectName ? (
            <label className="finance-scenario-creator__field">
              <span>{t('finance.scenarioCreator.fields.projectName')}</span>
              <input value={projectName} readOnly />
            </label>
          ) : null}
        </div>

        <div className="finance-scenario-creator__assets">
          <table className="finance-scenario-creator__table">
            <caption>{t('finance.scenarioCreator.assets.caption')}</caption>
            <thead>
              <tr>
                <th>{t('finance.scenarioCreator.assets.headers.assetType')}</th>
                <th className="numeric">{t('finance.scenarioCreator.fields.allocation')}</th>
                <th className="numeric">{t('finance.scenarioCreator.assets.headers.nia')}</th>
                <th className="numeric">{t('finance.scenarioCreator.assets.headers.rent')}</th>
                <th className="numeric">{t('finance.scenarioCreator.assets.headers.vacancy')}</th>
                <th className="numeric">{t('finance.scenarioCreator.assets.headers.opex')}</th>
                <th className="numeric">{t('finance.scenarioCreator.assets.headers.revenue')}</th>
                <th className="numeric">{t('finance.scenarioCreator.assets.headers.capex')}</th>
                <th className="numeric">{t('finance.scenarioCreator.assets.headers.absorption')}</th>
                <th>{t('finance.scenarioCreator.assets.headers.risk')}</th>
                <th>{t('finance.scenarioCreator.assets.headers.notes')}</th>
                <th aria-hidden />
              </tr>
            </thead>
            <tbody>
              {assets.map((asset) => (
                <tr key={asset.id}>
                  <td>
                    <input
                      type="text"
                      value={asset.assetType}
                      onChange={(event) =>
                        handleAssetChange(asset.id, 'assetType', event.target.value)
                      }
                      placeholder="office"
                    />
                  </td>
                  <td className="numeric">
                    <input
                      type="number"
                      step="0.1"
                      value={asset.allocationPct}
                      onChange={(event) =>
                        handleAssetChange(asset.id, 'allocationPct', event.target.value)
                      }
                    />
                  </td>
                  <td className="numeric">
                    <input
                      type="number"
                      step="0.01"
                      value={asset.niaSqm}
                      onChange={(event) =>
                        handleAssetChange(asset.id, 'niaSqm', event.target.value)
                      }
                    />
                  </td>
                  <td className="numeric">
                    <input
                      type="number"
                      step="0.01"
                      value={asset.rentPsmMonth}
                      onChange={(event) =>
                        handleAssetChange(asset.id, 'rentPsmMonth', event.target.value)
                      }
                    />
                  </td>
                  <td className="numeric">
                    <input
                      type="number"
                      step="0.1"
                      value={asset.vacancyPct}
                      onChange={(event) =>
                        handleAssetChange(asset.id, 'vacancyPct', event.target.value)
                      }
                    />
                  </td>
                  <td className="numeric">
                    <input
                      type="number"
                      step="0.1"
                      value={asset.opexPct}
                      onChange={(event) =>
                        handleAssetChange(asset.id, 'opexPct', event.target.value)
                      }
                    />
                  </td>
                  <td className="numeric">
                    <input
                      type="number"
                      step="0.01"
                      value={asset.estimatedRevenue}
                      onChange={(event) =>
                        handleAssetChange(asset.id, 'estimatedRevenue', event.target.value)
                      }
                    />
                  </td>
                  <td className="numeric">
                    <input
                      type="number"
                      step="0.01"
                      value={asset.estimatedCapex}
                      onChange={(event) =>
                        handleAssetChange(asset.id, 'estimatedCapex', event.target.value)
                      }
                    />
                  </td>
                  <td className="numeric">
                    <input
                      type="number"
                      step="0.1"
                      value={asset.absorptionMonths}
                      onChange={(event) =>
                        handleAssetChange(asset.id, 'absorptionMonths', event.target.value)
                      }
                    />
                  </td>
                  <td>
                    <input
                      type="text"
                      value={asset.riskLevel}
                      onChange={(event) =>
                        handleAssetChange(asset.id, 'riskLevel', event.target.value)
                      }
                    />
                  </td>
                  <td>
                    <input
                      type="text"
                      value={asset.notes}
                      onChange={(event) =>
                        handleAssetChange(asset.id, 'notes', event.target.value)
                      }
                    />
                  </td>
                  <td>
                    <button
                      type="button"
                      className="finance-scenario-creator__remove"
                      onClick={() => handleRemoveAsset(asset.id)}
                      disabled={assets.length <= 1}
                    >
                      {t('finance.scenarioCreator.actions.remove')}
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
          <button
            type="button"
            className="finance-scenario-creator__add"
            onClick={handleAddAsset}
          >
            {t('finance.scenarioCreator.actions.addAsset')}
          </button>
        </div>

        <div className="finance-scenario-creator__actions">
          <button
            type="button"
            className="finance-scenario-creator__reset"
            onClick={handleReset}
            disabled={saving}
          >
            {t('finance.scenarioCreator.actions.reset')}
          </button>
          <button
            type="submit"
            className="finance-scenario-creator__submit"
            disabled={saving}
          >
            {saving
              ? t('finance.scenarioCreator.actions.saving')
              : t('finance.scenarioCreator.actions.submit')}
          </button>
        </div>
      </form>
    </section>
  )
}

export default FinanceScenarioCreator
