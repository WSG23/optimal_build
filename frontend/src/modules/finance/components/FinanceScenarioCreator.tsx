import { FormEvent, useCallback, useEffect, useMemo, useState } from 'react'
import { Box, useTheme, useMediaQuery } from '@mui/material'

import { runFinanceFeasibility } from '../../../api/finance'
import type {
  FinanceScenarioSummary,
  FinanceFeasibilityRequest,
} from '../../../api/finance'
import { useTranslation } from '../../../i18n'
import {
  type AssetFormRow,
  DEFAULT_ASSET_ROWS,
  SG_FINANCE_TEMPLATES,
  createAssetRows,
  cloneScenarioDefaults,
  BASE_FINANCE_REQUEST,
  type FinanceScenarioDefaults,
} from './financeScenarioConstants'
import { TemplateSelectorCard } from './TemplateSelectorCard'
import { AssetMixTable } from './AssetMixTable'
import { AllocationSummaryPanel } from './AllocationSummaryPanel'

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
          <TemplateSelectorCard
            selectedTemplateId={selectedTemplateId}
            scenarioName={scenarioName}
            onApplyTemplate={applyTemplate}
            onScenarioNameChange={setScenarioName}
          />
          <AssetMixTable
            assets={assets}
            isCompactLayout={isCompactLayout}
            onAssetChange={handleAssetChange}
            onAddAsset={handleAddAsset}
            onRemoveAsset={handleRemoveAsset}
            onReset={handleReset}
          />
        </Box>

        {/* RIGHT COLUMN: ALLOCATION CHART */}
        <AllocationSummaryPanel
          chartData={chartData}
          unallocated={unallocated}
          totalRevenue={totalRevenue}
          saving={saving}
        />
      </Box>
    </Box>
  )
}
export default FinanceScenarioCreator
