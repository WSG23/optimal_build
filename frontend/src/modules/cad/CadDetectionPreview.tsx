import { useMemo, useState } from 'react'

import type { ChangeEvent, FormEvent } from 'react'
import {
  Box,
  IconButton,
  Paper,
  Tooltip,
  Chip,
  Typography,
} from '@mui/material'
import {
  Visibility,
  WarningAmber,
  InfoOutlined,
  CheckCircleOutline,
  ErrorOutline,
  RestartAlt,
  Map as MapIcon,
  Circle,
} from '@mui/icons-material'

import '../../styles/cad.css'

import { useTranslation } from '../../i18n'
import { DetectedUnit, DetectionStatus } from './types'
import { useFeasibilityLoop } from './useFeasibilityLoop'
import { RoiSummary } from './RoiSummary'
import { InteractiveFloorplate } from './InteractiveFloorplate'

type OverlaySummary = {
  key: string
  title: string
  count: number
  statusLabel: string
  severity: 'high' | 'medium' | 'low' | 'none'
  severityLabel: string
}

type SeveritySummary = {
  high: number
  medium: number
  low: number
  none: number
}

type SeverityToggleHandler = (severity: OverlaySummary['severity']) => void
type SeverityResetHandler = () => void

interface CadDetectionPreviewProps {
  units: DetectedUnit[]
  overlays: OverlaySummary[]
  hints: Array<{ key: string; text: string }>
  severitySummary: SeveritySummary
  severityPercentages: SeveritySummary
  hiddenSeverityCounts: SeveritySummary
  statusCounts: Record<DetectedUnit['status'], number>
  hiddenStatusCounts: Record<DetectedUnit['status'], number>
  activeStatuses: DetectionStatus[]
  activeSeverities: OverlaySummary['severity'][]
  onToggleSeverity: SeverityToggleHandler
  onResetSeverity: SeverityResetHandler
  onSaveSeverityPreset: () => void
  onApplySeverityPreset: () => void
  hasSeverityPreset: boolean
  canApplySeverityPreset: boolean
  isSeverityFiltered: boolean
  hiddenPendingCount: number
  severityFilterSummary: string
  zoneCode?: string | null
  locked?: boolean
  onProvideMetric?: (
    metricKey: string,
    value: number,
  ) => boolean | Promise<boolean>
  provideMetricDisabled?: boolean
}

const STATUS_LABEL_KEYS: Record<DetectedUnit['status'], string> = {
  source: 'controls.source',
  pending: 'controls.pending',
  approved: 'controls.approved',
  rejected: 'controls.rejected',
}

export function CadDetectionPreview({
  units,
  overlays,
  hints,
  severitySummary,
  severityPercentages: _severityPercentages,
  hiddenSeverityCounts: _hiddenSeverityCounts,
  statusCounts: _statusCounts,
  hiddenStatusCounts: _hiddenStatusCounts,
  activeStatuses: _activeStatuses,
  activeSeverities,
  onToggleSeverity,
  onResetSeverity,
  onSaveSeverityPreset: _onSaveSeverityPreset,
  onApplySeverityPreset: _onApplySeverityPreset,
  hasSeverityPreset: _hasSeverityPreset,
  canApplySeverityPreset: _canApplySeverityPreset,
  isSeverityFiltered,
  hiddenPendingCount,
  severityFilterSummary: _severityFilterSummary,
  zoneCode,
  locked = false,
  onProvideMetric,
  provideMetricDisabled = false,
}: CadDetectionPreviewProps) {
  const { t } = useTranslation()
  const floors = useMemo(
    () =>
      Array.from(new Set(units.map((unit) => unit.floor))).sort(
        (a, b) => a - b,
      ),
    [units],
  )
  const fallbackDash = t('common.fallback.dash')
  const [editingUnitId, setEditingUnitId] = useState<string | null>(null)
  const [inputValue, setInputValue] = useState<string>('')
  const severityOrder: OverlaySummary['severity'][] = [
    'high',
    'medium',
    'low',
    'none',
  ]

  const beginEditing = (unit: DetectedUnit) => {
    if (!unit.missingMetricKey) return
    setEditingUnitId(unit.id)
    setInputValue(
      unit.overrideValue != null ? unit.overrideValue.toString() : '',
    )
  }

  const cancelEditing = () => {
    setEditingUnitId(null)
    setInputValue('')
  }

  const handleInputChange = (event: ChangeEvent<HTMLInputElement>) => {
    setInputValue(event.target.value)
  }

  const handleSubmit = async (
    event: FormEvent<HTMLFormElement>,
    unit: DetectedUnit,
  ) => {
    event.preventDefault()
    if (!onProvideMetric || !unit.missingMetricKey) return
    const value = Number.parseFloat(inputValue)
    if (!Number.isFinite(value) || value <= 0) {
      window.alert(t('common.errors.generic'))
      return
    }
    const result = await onProvideMetric(unit.missingMetricKey, value)
    if (result) {
      cancelEditing()
    }
  }

  const { metrics: liveMetrics, loading: loopLoading } = useFeasibilityLoop(
    units,
    zoneCode || null,
  )

  const displayMetrics = liveMetrics || {
    automationScore: 0.72,
    savingsPercent: 15,
    reviewHoursSaved: 8,
    paybackWeeks: 6,
  }

  // Icons mapping for Floating Control
  const getSeverityIcon = (sev: OverlaySummary['severity']) => {
    switch (sev) {
      case 'high':
        return <ErrorOutline sx={{ color: 'var(--ob-error-500)' }} />
      case 'medium':
        return <WarningAmber sx={{ color: 'var(--ob-warning-500)' }} />
      case 'low':
        return <InfoOutlined sx={{ color: 'var(--ob-brand-500)' }} />
      case 'none':
        return <CheckCircleOutline sx={{ color: 'var(--ob-success-500)' }} />
    }
  }

  return (
    <section
      className="cad-preview"
      style={{
        display: 'flex',
        flexDirection: 'column',
        gap: 'var(--ob-spacing-500)',
      }}
    >
      {/* 1. HERO SECTION (Map + HUD) */}
      <Box
        sx={{
          position: 'relative',
          width: '100%',
          borderRadius: 'var(--ob-radius-sm)',
          overflow: 'hidden',
          boxShadow: 'var(--ob-shadow-xl)',
          background: 'var(--ob-neutral-950)',
          display: 'flex',
          flexDirection: 'column',
        }}
      >
        {/* Top Header Bar with Zone, Title, and ROI Stats */}
        <Box
          sx={{
            display: 'flex',
            justifyContent: 'space-between',
            alignItems: 'flex-start',
            p: 3,
            pb: 2,
            borderBottom: '1px solid var(--ob-border-fine)',
            flexWrap: 'wrap',
            gap: 2,
          }}
        >
          {/* Left Side: Zone & Title */}
          <Box sx={{ display: 'flex', flexDirection: 'column', gap: 1 }}>
            <Chip
              icon={
                <MapIcon
                  sx={{
                    fontSize: '16px !important',
                    color: 'var(--ob-color-text-inverse) !important',
                  }}
                />
              }
              label={zoneCode ? `ZONE ${zoneCode}` : 'NO ZONE DETECTED'}
              sx={{
                background: 'rgba(0,0,0,0.6)',
                backdropFilter: 'blur(10px)',
                color: 'var(--ob-color-text-inverse)',
                fontWeight: 700,
                border: '1px solid var(--ob-border-fine)',
                maxWidth: 'fit-content',
              }}
            />
            <Typography
              variant="h5"
              sx={{
                color: 'var(--ob-color-text-inverse)',
                fontWeight: 800,
                textShadow: '0 2px 10px rgba(0,0,0,0.5)',
                letterSpacing: '-0.02em',
              }}
            >
              {t('detection.title')}
            </Typography>
            <Typography variant="body2" sx={{ color: 'var(--ob-neutral-400)' }}>
              {t('detection.summary.floors', { count: floors.length })} •{' '}
              {t('detection.summary.units', { count: units.length })}
            </Typography>
          </Box>

          {/* Right Side: ROI Summary */}
          <Box sx={{ flexShrink: 0 }}>
            <RoiSummary
              metrics={displayMetrics}
              loading={loopLoading}
              isLive={true}
              variant="glass"
            />
          </Box>
        </Box>

        {/* A. The Interactive Viewer - Now below the header */}
        <Box sx={{ height: '450px', minHeight: '450px', position: 'relative' }}>
          <InteractiveFloorplate units={units} loading={loopLoading} />

          {/* D. Floating Layout Controls ("The Cockpit") */}
          <Box
            sx={{
              position: 'absolute',
              bottom: 32,
              left: '50%',
              transform: 'translateX(-50%)',
              zIndex: 30,
            }}
          >
            <Paper
              elevation={10}
              sx={{
                display: 'flex',
                alignItems: 'center',
                gap: 1,
                p: 1,
                pl: 2,
                pr: 2,
                borderRadius: '999px',
                background: 'var(--ob-surface-glass-1)',
                backdropFilter: 'blur(16px)',
                border: '1px solid var(--ob-border-fine)',
                boxShadow: 'var(--ob-shadow-lg)',
              }}
            >
              <Box sx={{ display: 'flex', alignItems: 'center' }}>
                <Typography
                  variant="caption"
                  sx={{
                    color: 'var(--ob-neutral-400)',
                    fontWeight: 600,
                    mr: 1,
                    textTransform: 'uppercase',
                  }}
                >
                  Visual Filters
                </Typography>
                {hiddenPendingCount > 0 && (
                  <Tooltip
                    title={t('detection.severitySummary.hiddenPending', {
                      count: hiddenPendingCount,
                    })}
                  >
                    <Circle
                      sx={{
                        width: 8,
                        height: 8,
                        color: 'var(--ob-error-500)',
                        mr: 1,
                        animation: 'pulse 2s infinite',
                      }}
                    />
                  </Tooltip>
                )}
              </Box>

              {severityOrder.map((severityKey) => {
                const isActive = activeSeverities.includes(severityKey)
                const count = severitySummary[severityKey]

                // Get top 3 overlays for this severity for the tooltip
                const severityOverlays = overlays
                  .filter((o) => o.severity === severityKey)
                  .slice(0, 3)
                const tooltipContent = (
                  <Box sx={{ p: 0.5 }}>
                    <Typography
                      variant="subtitle2"
                      component="div"
                      sx={{ fontWeight: 700, mb: 0.5 }}
                    >
                      {severityKey.toUpperCase()} ({count})
                    </Typography>
                    {severityOverlays.length > 0 ? (
                      <ul style={{ margin: 0, paddingLeft: 16 }}>
                        {severityOverlays.map((o) => (
                          <li key={o.key}>
                            <Typography variant="caption" component="span">
                              {o.title}
                            </Typography>
                          </li>
                        ))}
                        {count > 3 && (
                          <li>
                            <Typography variant="caption" component="span">
                              ...and {count - 3} more
                            </Typography>
                          </li>
                        )}
                      </ul>
                    ) : (
                      <Typography variant="caption" color="text.secondary">
                        No issues detected
                      </Typography>
                    )}
                  </Box>
                )

                return (
                  <Tooltip
                    key={severityKey}
                    title={tooltipContent}
                    arrow
                    placement="top"
                  >
                    <IconButton
                      onClick={() => {
                        onToggleSeverity(severityKey)
                      }}
                      size="small"
                      sx={{
                        transition: 'all 0.2s',
                        background: isActive
                          ? 'rgba(255,255,255,0.15)'
                          : 'transparent',
                        border: isActive
                          ? '1px solid rgba(255,255,255,0.3)'
                          : '1px solid transparent',
                        '&:hover': { background: 'rgba(255,255,255,0.2)' },
                      }}
                    >
                      {getSeverityIcon(severityKey)}
                    </IconButton>
                  </Tooltip>
                )
              })}

              <Box
                sx={{
                  width: 1,
                  height: 24,
                  background: 'var(--ob-border-fine)',
                  mx: 1,
                }}
              />

              <Tooltip title="Reset Filters">
                <IconButton
                  onClick={onResetSeverity}
                  size="small"
                  disabled={!isSeverityFiltered}
                >
                  <RestartAlt
                    sx={{
                      color: isSeverityFiltered
                        ? 'var(--ob-color-text-inverse)'
                        : 'var(--ob-neutral-600)',
                    }}
                  />
                </IconButton>
              </Tooltip>
              <Tooltip title="Show All Overlays">
                <IconButton
                  size="small"
                  onClick={onResetSeverity}
                  disabled={!isSeverityFiltered}
                >
                  <Visibility sx={{ color: 'var(--ob-color-text-inverse)' }} />
                </IconButton>
              </Tooltip>
            </Paper>
          </Box>
        </Box>
      </Box>

      {/* 2. DETAILS SECTION (Table & Hints) - Below Fold */}
      <Box sx={{ display: 'grid', gridTemplateColumns: '1fr 300px', gap: 3 }}>
        {/* Unit Table */}
        <Paper
          variant="outlined"
          sx={{
            p: 0,
            overflow: 'hidden',
            borderRadius: 'var(--ob-radius-sm)',
          }}
        >
          <table
            className="cad-preview__table"
            style={{ width: '100%', borderCollapse: 'collapse' }}
          >
            <caption
              style={{
                textAlign: 'left',
                padding: 'var(--ob-spacing-200)',
                fontWeight: 700,
                borderBottom: '1px solid var(--ob-color-border-subtle)',
              }}
            >
              {t('detection.tableHeading')}
            </caption>
            <thead style={{ background: 'var(--ob-neutral-50)' }}>
              <tr>
                <th
                  style={{
                    padding: 'var(--ob-spacing-150) var(--ob-spacing-200)',
                    textAlign: 'left',
                    fontSize: 'var(--ob-font-size-xs)',
                    textTransform: 'uppercase',
                    color: 'var(--ob-color-text-secondary)',
                  }}
                >
                  {t('detection.unit')}
                </th>
                <th
                  style={{
                    padding: 'var(--ob-spacing-150) var(--ob-spacing-200)',
                    textAlign: 'left',
                    fontSize: 'var(--ob-font-size-xs)',
                    textTransform: 'uppercase',
                    color: 'var(--ob-color-text-secondary)',
                  }}
                >
                  {t('detection.floor')}
                </th>
                <th
                  style={{
                    padding: 'var(--ob-spacing-150) var(--ob-spacing-200)',
                    textAlign: 'left',
                    fontSize: 'var(--ob-font-size-xs)',
                    textTransform: 'uppercase',
                    color: 'var(--ob-color-text-secondary)',
                  }}
                >
                  {t('detection.area')}
                </th>
                <th
                  style={{
                    padding: 'var(--ob-spacing-150) var(--ob-spacing-200)',
                    textAlign: 'left',
                    fontSize: 'var(--ob-font-size-xs)',
                    textTransform: 'uppercase',
                    color: 'var(--ob-color-text-secondary)',
                  }}
                >
                  {t('detection.status')}
                </th>
              </tr>
            </thead>
            <tbody>
              {units.length === 0 ? (
                <tr>
                  <td
                    colSpan={4}
                    style={{
                      padding: 'var(--ob-spacing-300)',
                      textAlign: 'center',
                      color: 'var(--ob-neutral-400)',
                    }}
                  >
                    {t('detection.empty')}
                  </td>
                </tr>
              ) : (
                units.map((unit) => {
                  const isEditing = editingUnitId === unit.id
                  const canEdit = Boolean(
                    unit.missingMetricKey && onProvideMetric,
                  )
                  const inputId = `cad-metric-${unit.id}`
                  const severityLabel =
                    unit.severity && unit.severity !== 'none'
                      ? t(`detection.severity.${unit.severity}`)
                      : null

                  return (
                    <tr
                      key={unit.id}
                      style={{
                        borderTop: '1px solid var(--ob-color-border-subtle)',
                      }}
                    >
                      <td
                        style={{
                          padding:
                            'var(--ob-spacing-150) var(--ob-spacing-200)',
                        }}
                      >
                        <div
                          style={{
                            display: 'flex',
                            alignItems: 'center',
                            gap: '8px',
                          }}
                        >
                          <span className="cad-unit-label">
                            {unit.unitLabel}
                          </span>
                          {severityLabel && (
                            <Chip
                              label={severityLabel}
                              size="small"
                              color={
                                unit.severity === 'high'
                                  ? 'error'
                                  : unit.severity === 'medium'
                                    ? 'warning'
                                    : 'primary'
                              }
                              variant="outlined"
                              sx={{
                                height: 20,
                                fontSize: 'var(--ob-font-size-xs)',
                              }}
                            />
                          )}
                        </div>
                      </td>
                      <td
                        style={{
                          padding:
                            'var(--ob-spacing-150) var(--ob-spacing-200)',
                        }}
                      >
                        {unit.floor}
                      </td>
                      <td
                        style={{
                          padding:
                            'var(--ob-spacing-150) var(--ob-spacing-200)',
                        }}
                      >
                        {unit.areaSqm.toFixed(1)}
                      </td>
                      <td
                        style={{
                          padding:
                            'var(--ob-spacing-150) var(--ob-spacing-200)',
                        }}
                        className={`cad-status cad-status--${unit.status}`}
                      >
                        <div className="cad-status__label">
                          {t(STATUS_LABEL_KEYS[unit.status])}
                          {!isEditing && unit.overrideDisplay && (
                            <span className="cad-status__override">
                              {unit.overrideDisplay}
                            </span>
                          )}
                        </div>
                        {canEdit &&
                          (isEditing ? (
                            <form
                              className="cad-metric-editor"
                              onSubmit={(event) => {
                                void handleSubmit(event, unit)
                              }}
                            >
                              <input
                                type="number"
                                step="any"
                                id={inputId}
                                value={inputValue}
                                placeholder={
                                  unit.metricLabel ??
                                  unit.missingMetricKey ??
                                  ''
                                }
                                onChange={handleInputChange}
                                disabled={provideMetricDisabled}
                                style={{
                                  width: '80px',
                                  padding: 'var(--ob-spacing-100)',
                                  border:
                                    '1px solid var(--ob-color-border-subtle)',
                                  borderRadius: 'var(--ob-radius-sm)',
                                }}
                              />
                              <button
                                type="submit"
                                disabled={provideMetricDisabled}
                                style={{ marginLeft: '4px', cursor: 'pointer' }}
                              >
                                ✓
                              </button>
                              <button
                                type="button"
                                disabled={provideMetricDisabled}
                                onClick={cancelEditing}
                                style={{ marginLeft: '4px', cursor: 'pointer' }}
                              >
                                ✕
                              </button>
                            </form>
                          ) : (
                            <button
                              type="button"
                              className="cad-preview__metric-button"
                              disabled={provideMetricDisabled}
                              onClick={() => {
                                beginEditing(unit)
                              }}
                              style={{
                                marginLeft: 'var(--ob-spacing-100)',
                                fontSize: 'var(--ob-font-size-xs)',
                                color: 'var(--ob-brand-500)',
                                background: 'none',
                                border: 'none',
                                cursor: 'pointer',
                                textDecoration: 'underline',
                              }}
                            >
                              {unit.overrideValue != null
                                ? t('detection.override.edit')
                                : t('detection.override.add')}
                            </button>
                          ))}
                      </td>
                    </tr>
                  )
                })
              )}
            </tbody>
          </table>
        </Paper>

        {/* Advisory / Hints Panel */}
        <Paper
          variant="outlined"
          sx={{ p: 3, borderRadius: '4px', height: 'fit-content' }}
        >
          <Typography variant="h6" gutterBottom>
            {t('detection.advisory')}
          </Typography>
          {hints.length === 0 ? (
            <Typography variant="body2" color="text.secondary">
              {fallbackDash}
            </Typography>
          ) : (
            <ul style={{ paddingLeft: '20px', margin: 0 }}>
              {hints.map((hint) => (
                <li
                  key={hint.key}
                  style={{
                    marginBottom: '8px',
                    fontSize: 'var(--ob-font-size-sm)',
                    color: 'var(--ob-neutral-600)',
                  }}
                >
                  {hint.text}
                </li>
              ))}
            </ul>
          )}
        </Paper>
      </Box>

      {/* Legacy Lock Indicator (if relevant) */}
      {locked && (
        <Typography color="error" align="center">
          {t('detection.locked')}
        </Typography>
      )}
    </section>
  )
}

export default CadDetectionPreview
