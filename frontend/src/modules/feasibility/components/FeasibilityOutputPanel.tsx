import { Box, Typography } from '@mui/material'
import {
  Bar,
  BarChart,
  CartesianGrid,
  Cell,
  Pie,
  PieChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from 'recharts'
import {
  AccountBalance as HeritageIcon,
  Gavel as ZoningIcon,
} from '@mui/icons-material'
import { useMemo, useState } from 'react'

import type { SiteAcquisitionResult } from '../../../api/siteAcquisition'
import type { FeasibilityAssessmentResponse } from '../../../api/feasibility'
import { Card } from '../../../components/canonical/Card'
import { MetricTile } from '../../../components/canonical/MetricTile'
import { AlertBlock } from '../../../components/canonical/AlertBlock'
import { Preview3DViewer } from '../../../app/components/site-acquisition/Preview3DViewer'
import type { BuildableSummary, WizardStatus } from '../types'

type AssetMixDatum = {
  assetType: string
  label: string
  allocationPct: number
  gfaSqm: number | null
  niaSqm: number | null
  color: string
}

interface FeasibilityOutputPanelProps {
  status: WizardStatus
  assessment: FeasibilityAssessmentResponse | null
  result: BuildableSummary | null
  captureResult: SiteAcquisitionResult | null
  activeSiteLabel: string
  numberFormatter: Intl.NumberFormat
  oneDecimalFormatter: Intl.NumberFormat
  /** Active visualization layers */
  activeLayers?: string[]
}

function toTitleCase(value: string): string {
  return value
    .replace(/[_-]/g, ' ')
    .replace(/\s+/g, ' ')
    .trim()
    .split(' ')
    .map((part) => part.charAt(0).toUpperCase() + part.slice(1).toLowerCase())
    .join(' ')
}

function normalizeAssetType(value: string): string {
  return value
    .trim()
    .toLowerCase()
    .replace(/[_\s]+/g, '-')
}

function formatCurrency(
  value: number | null | undefined,
  numberFormatter: Intl.NumberFormat,
  scale = 1_000_000,
): string {
  if (value == null || Number.isNaN(value)) {
    return '—'
  }
  const scaled = value / scale
  return `$${numberFormatter.format(scaled)}M`
}

function formatPercent(value: number | null | undefined): string {
  if (value == null || Number.isNaN(value)) {
    return '—'
  }
  return `${value.toFixed(1)}%`
}

function sumMetric(
  items: Array<Record<string, unknown>>,
  key: string,
): number | null {
  let total = 0
  let hasValue = false
  items.forEach((item) => {
    const value = item[key]
    if (typeof value !== 'number' || Number.isNaN(value)) {
      return
    }
    total += value
    hasValue = true
  })
  return hasValue ? total : null
}

export function FeasibilityOutputPanel({
  status,
  assessment,
  result,
  captureResult,
  activeSiteLabel: _activeSiteLabel,
  numberFormatter,
  oneDecimalFormatter,
  activeLayers = ['zoning'],
}: FeasibilityOutputPanelProps) {
  const shouldRenderCharts = import.meta.env?.MODE !== 'test'

  // 3D Massing preview URLs from capture result
  const previewUrl = captureResult?.visualization?.conceptMeshUrl ?? null
  const metadataUrl = captureResult?.visualization?.previewMetadataUrl ?? null
  const thumbnailUrl = captureResult?.visualization?.thumbnailUrl ?? null
  const previewStatus = captureResult?.visualization?.status ?? 'pending'
  const has3DPreview = Boolean(previewUrl)

  // Layer visibility state for 3D viewer (derived from activeLayers prop)
  const [focusLayerId, setFocusLayerId] = useState<string | null>(null)
  const layerVisibility = useMemo(() => {
    // Map activeLayers to layer visibility for the 3D viewer
    // The 3D viewer uses layer IDs from the GLTF model
    // For now, show all layers - the activeLayers prop controls CSS overlays
    return undefined // Show all layers in the 3D model
  }, [])

  const assetLegend = new Map<string, string>()
  captureResult?.visualization?.colorLegend?.forEach((entry) => {
    if (entry.assetType && entry.color) {
      assetLegend.set(normalizeAssetType(entry.assetType), entry.color)
    }
  })

  const assetMixSource = assessment?.assetOptimizations?.length
    ? assessment.assetOptimizations
    : captureResult?.optimizations?.length
      ? captureResult.optimizations
      : []

  const palette: Record<string, string> = {
    residential: 'var(--ob-feasibility-asset-residential)',
    commercial: 'var(--ob-feasibility-asset-commercial)',
    office: 'var(--ob-feasibility-asset-office)',
    retail: 'var(--ob-feasibility-asset-retail)',
    industrial: 'var(--ob-feasibility-asset-industrial)',
    'mixed-use': 'var(--ob-feasibility-asset-mixed)',
    hospitality: 'var(--ob-feasibility-asset-hospitality)',
  }

  const assetMixData: AssetMixDatum[] = assetMixSource
    .filter((entry) => entry.assetType)
    .map((entry) => {
      const normalized = normalizeAssetType(entry.assetType)
      let gfaSqm = entry.allocatedGfaSqm != null ? entry.allocatedGfaSqm : null
      // niaSqm only exists on AssetOptimizationRecommendation, not DeveloperAssetOptimization
      const entryNiaSqm =
        'niaSqm' in entry ? (entry.niaSqm as number | null) : null
      let niaSqm =
        entryNiaSqm != null
          ? entryNiaSqm
          : gfaSqm != null && entry.niaEfficiency != null
            ? gfaSqm * entry.niaEfficiency
            : null
      if (
        gfaSqm == null &&
        niaSqm != null &&
        entry.niaEfficiency != null &&
        entry.niaEfficiency > 0
      ) {
        gfaSqm = niaSqm / entry.niaEfficiency
      }
      const color =
        assetLegend.get(normalized) ??
        palette[normalized] ??
        'var(--ob-feasibility-asset-default)'

      return {
        assetType: normalized,
        label: toTitleCase(entry.assetType),
        allocationPct: Number.isFinite(entry.allocationPct)
          ? entry.allocationPct
          : 0,
        gfaSqm,
        niaSqm,
        color,
      }
    })
    .filter((entry) => entry.allocationPct > 0)

  const hasAssetMix = assetMixData.length > 0
  const assetMixSummary = assessment?.assetMixSummary ?? null
  const optimizationFinancialSource = assessment?.assetOptimizations?.length
    ? assessment.assetOptimizations
    : (captureResult?.optimizations ?? [])
  const estimatedRevenue =
    assetMixSummary?.totalEstimatedRevenueSgd ??
    sumMetric(optimizationFinancialSource, 'estimatedRevenueSgd') ??
    captureResult?.financialSummary?.totalEstimatedRevenueSgd ??
    null
  const estimatedCapex =
    assetMixSummary?.totalEstimatedCapexSgd ??
    sumMetric(optimizationFinancialSource, 'estimatedCapexSgd') ??
    captureResult?.financialSummary?.totalEstimatedCapexSgd ??
    null
  const estimatedProfit =
    estimatedRevenue != null && estimatedCapex != null
      ? estimatedRevenue - estimatedCapex
      : null
  const returnOnCost =
    estimatedProfit != null && estimatedCapex && estimatedCapex > 0
      ? (estimatedProfit / estimatedCapex) * 100
      : null

  const assetMixNiaTotal = assetMixData.reduce(
    (acc, item) => acc + (item.niaSqm ?? 0),
    0,
  )
  const assessmentNiaTotal = assessment?.assetOptimizations?.length
    ? assessment.assetOptimizations.reduce((acc, item) => {
        if (item.niaSqm != null) {
          return acc + item.niaSqm
        }
        if (item.allocatedGfaSqm != null && item.niaEfficiency != null) {
          return acc + item.allocatedGfaSqm * item.niaEfficiency
        }
        return acc
      }, 0)
    : 0
  const totalNia =
    (assessmentNiaTotal > 0 ? assessmentNiaTotal : null) ??
    (assetMixNiaTotal > 0 ? assetMixNiaTotal : null) ??
    result?.metrics?.nsaEstM2 ??
    null
  const projectYield = assessment?.summary?.estimatedUnitCount ?? null

  const summaryAchievable =
    assessment?.summary?.estimatedAchievableGfaSqm ?? null
  const summaryMax = assessment?.summary?.maxPermissibleGfaSqm ?? null
  const summaryGfa = summaryAchievable ?? summaryMax ?? null
  const summaryLabel =
    summaryAchievable != null
      ? 'Achievable'
      : summaryMax != null
        ? 'Max Permissible'
        : 'Total'
  const gfaChartData =
    assetMixData.length > 0
      ? assetMixData.map((entry) => ({
          name: entry.label,
          gfa: entry.gfaSqm ?? 0,
          nia: entry.niaSqm ?? 0,
        }))
      : summaryGfa != null && totalNia != null
        ? [
            {
              name: summaryLabel,
              gfa: summaryGfa,
              nia: totalNia,
            },
          ]
        : []
  const hasGfaChart = gfaChartData.length > 0

  const constraints =
    assessment?.constraintLog?.length && assessment.constraintLog.length > 0
      ? assessment.constraintLog.map((item, index) => ({
          id: `${item.constraintType}-${index}`,
          severity: item.severity ?? 'info',
          message: item.message,
        }))
      : (captureResult?.heritageContext?.constraints?.map((message, index) => ({
          id: `heritage-${index}`,
          severity: 'warning',
          message,
        })) ?? [])

  const heritageOverlay = captureResult?.heritageContext?.overlay?.name ?? null
  const recommendation =
    assessment?.recommendations?.[0] ??
    captureResult?.financialSummary?.notes?.[0] ??
    null

  return (
    <section className="feasibility-output" aria-live="polite">
      <div className="feasibility-output__kpis">
        <MetricTile
          label="Est. Profit"
          value={formatCurrency(estimatedProfit, numberFormatter)}
          loading={status === 'loading'}
        />
        <MetricTile
          label="Return on Cost"
          value={formatPercent(returnOnCost)}
          loading={status === 'loading'}
        />
        <MetricTile
          label="Total NIA"
          value={
            totalNia != null
              ? `${numberFormatter.format(Math.round(totalNia))} m²`
              : '—'
          }
          loading={status === 'loading'}
        />
        <MetricTile
          label="Project Yield"
          value={
            projectYield != null
              ? `${numberFormatter.format(projectYield)} units`
              : '—'
          }
          loading={status === 'loading'}
        />
      </div>

      <div className="feasibility-output__grid">
        <Card
          variant="glass"
          className="feasibility-output__card feasibility-output__card--span-8"
        >
          <div className="feasibility-output__card-header">
            <Typography variant="h6">3D Massing Visualization</Typography>
            <div className="feasibility-output__card-actions">
              {focusLayerId && (
                <button
                  type="button"
                  className="feasibility-output__toggle feasibility-output__toggle--active"
                  onClick={() => setFocusLayerId(null)}
                >
                  Reset View
                </button>
              )}
            </div>
          </div>
          {has3DPreview ? (
            <Box className="feasibility-canvas feasibility-canvas--3d">
              <Preview3DViewer
                previewUrl={previewUrl}
                metadataUrl={metadataUrl}
                status={previewStatus}
                thumbnailUrl={thumbnailUrl}
                layerVisibility={layerVisibility}
                focusLayerId={focusLayerId}
              />
            </Box>
          ) : (
            <div className="feasibility-canvas">
              <div className="feasibility-canvas__grid" aria-hidden />
              <div className="feasibility-canvas__model" aria-hidden />
              <div className="feasibility-canvas__halo" aria-hidden />
              {/* Layer overlays - CSS placeholder when no 3D model */}
              {activeLayers.includes('zoning') && (
                <div
                  className="feasibility-canvas__layer feasibility-canvas__layer--zoning"
                  aria-label="Zoning envelope overlay"
                />
              )}
              {activeLayers.includes('structure') && (
                <div
                  className="feasibility-canvas__layer feasibility-canvas__layer--structure"
                  aria-label="Structural grid overlay"
                />
              )}
              {activeLayers.includes('mep') && (
                <div
                  className="feasibility-canvas__layer feasibility-canvas__layer--mep"
                  aria-label="MEP risers overlay"
                />
              )}
              <div className="feasibility-canvas__empty">
                {status === 'loading'
                  ? 'Generating 3D massing preview...'
                  : 'Run simulation to generate the 3D massing preview.'}
              </div>
            </div>
          )}
          {hasAssetMix && (
            <div className="feasibility-canvas__legend">
              {assetMixData.slice(0, 4).map((entry) => (
                <div
                  key={entry.assetType}
                  className="feasibility-canvas__legend-item"
                  onClick={() => setFocusLayerId(entry.assetType)}
                  onKeyDown={(e) => {
                    if (e.key === 'Enter' || e.key === ' ') {
                      setFocusLayerId(entry.assetType)
                    }
                  }}
                  role="button"
                  tabIndex={0}
                  style={{ cursor: 'pointer' }}
                >
                  <span
                    className="feasibility-canvas__legend-dot"
                    style={{ background: entry.color }}
                  />
                  <span>{entry.label}</span>
                  <span className="feasibility-canvas__legend-value">
                    {oneDecimalFormatter.format(entry.allocationPct)}%
                  </span>
                </div>
              ))}
            </div>
          )}
        </Card>

        <Card
          variant="glass"
          className="feasibility-output__card feasibility-output__card--span-4"
        >
          <div className="feasibility-output__card-header">
            <Typography variant="h6">Asset Mix</Typography>
          </div>
          {hasAssetMix && shouldRenderCharts ? (
            <Box className="feasibility-chart">
              <ResponsiveContainer width="100%" height="100%">
                <PieChart>
                  <Pie
                    data={assetMixData}
                    dataKey="allocationPct"
                    nameKey="label"
                    innerRadius={48}
                    outerRadius={70}
                    paddingAngle={2}
                    stroke="none"
                  >
                    {assetMixData.map((entry) => (
                      <Cell key={entry.assetType} fill={entry.color} />
                    ))}
                  </Pie>
                  <Tooltip
                    formatter={(value: number) => `${value}%`}
                    contentStyle={{ borderRadius: 'var(--ob-radius-sm)' }}
                  />
                </PieChart>
              </ResponsiveContainer>
              <div className="feasibility-chart__legend">
                {assetMixData.map((entry) => (
                  <div
                    key={entry.assetType}
                    className="feasibility-chart__legend-item"
                  >
                    <span
                      className="feasibility-chart__legend-dot"
                      style={{ background: entry.color }}
                    />
                    <span>{entry.label}</span>
                    <span className="feasibility-chart__legend-value">
                      {oneDecimalFormatter.format(entry.allocationPct)}%
                    </span>
                  </div>
                ))}
              </div>
            </Box>
          ) : (
            <div className="feasibility-output__empty">
              Asset mix appears after simulation.
            </div>
          )}
        </Card>

        <Card
          variant="glass"
          className="feasibility-output__card feasibility-output__card--span-8"
        >
          <div className="feasibility-output__card-header">
            <Typography variant="h6">NIA vs GFA Distribution</Typography>
          </div>
          {hasGfaChart && shouldRenderCharts ? (
            <Box className="feasibility-chart">
              <ResponsiveContainer width="100%" height="100%">
                <BarChart data={gfaChartData}>
                  <CartesianGrid
                    strokeDasharray="3 3"
                    stroke="var(--ob-color-border-subtle)"
                  />
                  <XAxis
                    dataKey="name"
                    tick={{
                      fill: 'var(--ob-color-text-secondary)',
                      fontSize: 12,
                    }}
                  />
                  <YAxis
                    tick={{
                      fill: 'var(--ob-color-text-secondary)',
                      fontSize: 12,
                    }}
                  />
                  <Tooltip
                    contentStyle={{ borderRadius: 'var(--ob-radius-sm)' }}
                    formatter={(value: number) =>
                      `${numberFormatter.format(Math.round(value))} m²`
                    }
                  />
                  <Bar
                    dataKey="gfa"
                    fill="var(--ob-feasibility-chart-gfa)"
                    radius={[2, 2, 0, 0]}
                  />
                  <Bar
                    dataKey="nia"
                    fill="var(--ob-feasibility-chart-nia)"
                    radius={[2, 2, 0, 0]}
                  />
                </BarChart>
              </ResponsiveContainer>
            </Box>
          ) : (
            <div className="feasibility-output__empty">
              NIA vs GFA distribution will appear after simulation.
            </div>
          )}
        </Card>

        <Card
          variant="glass"
          className="feasibility-output__card feasibility-output__card--span-4"
        >
          <div className="feasibility-output__card-header">
            <Typography variant="h6">Heritage & Constraints</Typography>
          </div>
          <Box
            sx={{
              display: 'flex',
              flexDirection: 'column',
              gap: 'var(--ob-space-075)',
            }}
          >
            {heritageOverlay ? (
              <AlertBlock
                type="warning"
                title="Heritage Overlay"
                icon={<HeritageIcon />}
              >
                {heritageOverlay}
              </AlertBlock>
            ) : (
              <AlertBlock
                type="info"
                title="Heritage Status"
                icon={<HeritageIcon />}
                variant="outlined"
              >
                No heritage overlay flagged for this site.
              </AlertBlock>
            )}
            {constraints.length > 0 ? (
              constraints.slice(0, 4).map((item) => {
                const alertType =
                  item.severity === 'critical'
                    ? 'error'
                    : item.severity === 'important' ||
                        item.severity === 'warning'
                      ? 'warning'
                      : 'info'
                return (
                  <AlertBlock
                    key={item.id}
                    type={alertType}
                    icon={<ZoningIcon />}
                    variant="outlined"
                  >
                    {item.message}
                  </AlertBlock>
                )
              })
            ) : (
              <Box
                sx={{
                  fontSize: 'var(--ob-font-size-sm)',
                  color: 'var(--ob-color-text-muted)',
                  py: 'var(--ob-space-050)',
                }}
              >
                Zoning constraints appear after simulation.
              </Box>
            )}
          </Box>
        </Card>

        <Card
          variant="glass"
          className="feasibility-output__card feasibility-output__card--span-12"
        >
          <div className="feasibility-output__card-header">
            <Typography variant="h6">AI Optimizer</Typography>
          </div>
          <div className="feasibility-ai">
            <div className="feasibility-ai__highlight">
              {recommendation ??
                'Run simulation to generate a tailored optimization summary.'}
            </div>
            <div className="feasibility-ai__meta">
              {assetMixSummary?.notes?.[0] ??
                'Confidence updates after analysis.'}
            </div>
          </div>
        </Card>
      </div>
    </section>
  )
}
