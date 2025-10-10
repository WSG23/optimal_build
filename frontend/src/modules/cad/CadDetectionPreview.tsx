import { useMemo, useState } from 'react'

import type { ChangeEvent, FormEvent } from 'react'

import { useTranslation } from '../../i18n'
import { DetectedUnit } from './types'

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
  activeSeverities: OverlaySummary['severity'][]
  onToggleSeverity: SeverityToggleHandler
  onResetSeverity: SeverityResetHandler
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
  severityPercentages,
  hiddenSeverityCounts,
  activeSeverities,
  onToggleSeverity,
  onResetSeverity,
  isSeverityFiltered,
  hiddenPendingCount,
  severityFilterSummary,
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
  const infoOnly = overlays.length > 0 && overlays.every((item) => item.severity === 'none')

  const beginEditing = (unit: DetectedUnit) => {
    if (!unit.missingMetricKey) {
      return
    }
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
    if (!onProvideMetric || !unit.missingMetricKey) {
      return
    }
    const value = Number.parseFloat(inputValue)
    if (!Number.isFinite(value) || value <= 0) {
      window.alert(t('common.errors.generic'))
      return
    }
    const result = await onProvideMetric(unit.missingMetricKey, value)
    if (result !== false) {
      cancelEditing()
    }
  }

  return (
    <section className="cad-preview">
      <header className="cad-preview__header">
        <div>
          <h2>{t('detection.title')}</h2>
          <p>{t('detection.subtitle')}</p>
        </div>
        <div className="cad-preview__summary">
          <span>{t('detection.summary.floors', { count: floors.length })}</span>
          <span>{t('detection.summary.units', { count: units.length })}</span>
          {zoneCode && (
            <span>{t('detection.summary.zone', { code: zoneCode })}</span>
          )}
          {hiddenPendingCount > 0 && (
            <button
              type="button"
              className="cad-preview__summary-warning"
              onClick={onResetSeverity}
              title={t('detection.severitySummary.hiddenPendingTooltip')}
            >
              {t('detection.severitySummary.hiddenPending', {
                count: hiddenPendingCount,
              })}
            </button>
          )}
        </div>
      </header>

      <div className="cad-preview__grid">
        <div className="cad-preview__panel">
          <h3>{t('detection.overlays')}</h3>
          {overlays.length === 0 ? (
            <p>{fallbackDash}</p>
          ) : (
            <>
              <div className="cad-overlay-summary">
                <div className="cad-overlay-summary__heading">
                  <span>{t('detection.severitySummary.heading')}</span>
                  <span className="cad-overlay-summary__filters">
                    {severityFilterSummary}
                  </span>
                  <button
                    type="button"
                    className="cad-overlay-summary__reset"
                    onClick={onResetSeverity}
                    disabled={!isSeverityFiltered}
                  >
                    {t('detection.severitySummary.reset')}
                  </button>
                </div>
                <div
                  className="cad-overlay-summary__badges"
                  role="group"
                  aria-label={t('detection.severitySummary.heading')}
                >
                  {severityOrder.map((severityKey) => {
                    const label =
                      severityKey === 'none'
                        ? t('detection.severitySummary.info')
                        : t(`detection.severitySummary.${severityKey}`)
                    const count = severitySummary[severityKey]
                    const percent = severityPercentages[severityKey]
                    const hiddenCount = hiddenSeverityCounts[severityKey]
                    const isActive = activeSeverities.includes(severityKey)
                    const badgeClass = [
                      'cad-overlay-summary__badge',
                      `cad-overlay-summary__badge--${severityKey}`,
                      isActive
                        ? 'cad-overlay-summary__badge--active'
                        : 'cad-overlay-summary__badge--inactive',
                    ].join(' ')
                    const formattedPercent = new Intl.NumberFormat(undefined, {
                      minimumFractionDigits: percent % 1 === 0 ? 0 : 1,
                      maximumFractionDigits: 1,
                    }).format(percent)
                    const tooltipText = hiddenCount > 0
                      ? t('detection.severitySummary.tooltipHidden', {
                          label,
                          count: hiddenCount,
                        })
                      : t('detection.severitySummary.tooltip', {
                          label,
                          count,
                          percent: formattedPercent,
                        })
                    return (
                      <button
                        type="button"
                        key={severityKey}
                        className={badgeClass}
                        onClick={() => {
                          onToggleSeverity(severityKey)
                        }}
                        aria-pressed={isActive}
                        title={tooltipText}
                      >
                        {label} <strong>{count}</strong>
                      </button>
                    )
                  })}
                </div>
              </div>
              {!isSeverityFiltered && hiddenPendingCount === 0 && (
                <p className="cad-overlay-summary__helper">
                  {t('detection.severitySummary.helperAllVisible')}
                </p>
              )}
              {infoOnly && (
                <div className="cad-overlay-info-banner">
                  <span>{t('detection.severitySummary.infoOnly')}</span>
                  {isSeverityFiltered && (
                    <button
                      type="button"
                      className="cad-overlay-info-banner__action"
                      onClick={onResetSeverity}
                    >
                      {t('detection.severitySummary.infoOnlyAction')}
                    </button>
                  )}
                </div>
              )}
              <ul className="cad-overlay-list">
                {overlays.map((overlay) => (
                  <li key={overlay.key} className="cad-overlay-item">
                    <div className="cad-overlay-item__header">
                      <span className="cad-overlay-item__title">
                        {overlay.title}
                      </span>
                      <span
                        className={`cad-overlay-item__severity cad-overlay-item__severity--${overlay.severity}`}
                      >
                        {overlay.severityLabel}
                      </span>
                    </div>
                    <div className="cad-overlay-item__meta">
                      {overlay.count > 1 && (
                        <span className="cad-overlay-item__count">
                          {t('detection.countSuffix', { count: overlay.count })}
                        </span>
                      )}
                      <span className="cad-overlay-item__status">
                        {overlay.statusLabel}
                      </span>
                    </div>
                  </li>
                ))}
              </ul>
            </>
          )}
        </div>
        <div className="cad-preview__panel">
          <h3>{t('detection.advisory')}</h3>
          {hints.length === 0 ? (
            <p>{fallbackDash}</p>
          ) : (
            <ul>
              {hints.map((hint) => (
                <li key={hint.key}>{hint.text}</li>
              ))}
            </ul>
          )}
        </div>
      </div>

      {locked && (
        <p className="cad-preview__lock-indicator">{t('detection.locked')}</p>
      )}

      <table className="cad-preview__table">
        <caption>{t('detection.tableHeading')}</caption>
        <thead>
          <tr>
            <th>{t('detection.unit')}</th>
            <th>{t('detection.floor')}</th>
            <th>{t('detection.area')}</th>
            <th>{t('detection.status')}</th>
          </tr>
        </thead>
        <tbody>
          {units.length === 0 ? (
            <tr>
              <td colSpan={4}>{t('detection.empty')}</td>
            </tr>
          ) : (
            units.map((unit) => {
              const isEditing = editingUnitId === unit.id
              const canEdit = Boolean(unit.missingMetricKey && onProvideMetric)
              const inputId = `cad-metric-${unit.id}`
              const severityLabel =
                unit.severity && unit.severity !== 'none'
                  ? t(`detection.severity.${unit.severity}`)
                  : unit.severity === 'none'
                    ? t('detection.severity.none')
                    : null

              return (
                <tr key={unit.id}>
                  <td>
                    <span className="cad-unit-label">
                      {unit.unitLabel}
                    </span>
                    {severityLabel && (
                      <span
                        className={`cad-unit-severity cad-unit-severity--${unit.severity}`}
                        title={severityLabel}
                      >
                        {severityLabel}
                      </span>
                    )}
                  </td>
                  <td>{unit.floor}</td>
                  <td>{unit.areaSqm.toFixed(1)}</td>
                  <td className={`cad-status cad-status--${unit.status}`}>
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
                          <label
                            htmlFor={inputId}
                            className="cad-metric-editor__label"
                          >
                            {unit.metricLabel ?? unit.missingMetricKey}
                          </label>
                          <input
                            type="number"
                            step="any"
                            id={inputId}
                            value={inputValue}
                            placeholder={
                              unit.metricLabel ?? unit.missingMetricKey ?? ''
                            }
                            onChange={handleInputChange}
                            disabled={provideMetricDisabled}
                          />
                          <div className="cad-metric-editor__actions">
                            <button
                              type="submit"
                              disabled={provideMetricDisabled}
                            >
                              {t('common.actions.save')}
                            </button>
                            <button
                              type="button"
                              disabled={provideMetricDisabled}
                              onClick={cancelEditing}
                            >
                              {t('common.actions.cancel')}
                            </button>
                          </div>
                        </form>
                      ) : (
                        <button
                          type="button"
                          className="cad-preview__metric-button"
                          disabled={provideMetricDisabled}
                          onClick={() => {
                            beginEditing(unit)
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
    </section>
  )
}

export default CadDetectionPreview
