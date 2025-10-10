import { useMemo, useState } from 'react'

import type { ChangeEvent, FormEvent } from 'react'

import { useTranslation } from '../../i18n'
import { DetectedUnit } from './types'

interface CadDetectionPreviewProps {
  units: DetectedUnit[]
  overlays: string[]
  hints: string[]
  zoneCode?: string | null
  locked?: boolean
  onProvideMetric?: (metricKey: string, value: number) => boolean | Promise<boolean>
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
        </div>
      </header>

      <div className="cad-preview__grid">
        <div className="cad-preview__panel">
          <h3>{t('detection.overlays')}</h3>
          {overlays.length === 0 ? (
            <p>{fallbackDash}</p>
          ) : (
            <ul>
              {overlays.map((overlay) => (
                <li key={overlay}>{overlay}</li>
              ))}
            </ul>
          )}
        </div>
        <div className="cad-preview__panel">
          <h3>{t('detection.advisory')}</h3>
          {hints.length === 0 ? (
            <p>{fallbackDash}</p>
          ) : (
            <ul>
              {hints.map((hint) => (
                <li key={hint}>{hint}</li>
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

              return (
                <tr key={unit.id}>
                  <td>{unit.unitLabel}</td>
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
                    {canEdit && (
                      isEditing ? (
                        <form
                          className="cad-metric-editor"
                          onSubmit={(event) => {
                            void handleSubmit(event, unit)
                          }}
                        >
                          <label htmlFor={inputId} className="cad-metric-editor__label">
                            {unit.metricLabel ?? unit.missingMetricKey}
                          </label>
                          <input
                            type="number"
                            step="any"
                            id={inputId}
                            value={inputValue}
                            placeholder={unit.metricLabel ?? unit.missingMetricKey ?? ''}
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
                      )
                    )}
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
