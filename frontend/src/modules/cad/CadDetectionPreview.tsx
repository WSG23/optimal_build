import { useMemo } from 'react'

import { useTranslation } from '../../i18n'
import { DetectedUnit } from './types'

interface CadDetectionPreviewProps {
  units: DetectedUnit[]
  overlays: string[]
  hints: string[]
  zoneCode?: string | null
  locked?: boolean
  onProvideMetric?: (metricKey: string, currentValue?: number | null) => void
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
            units.map((unit) => (
              <tr key={unit.id}>
                <td>{unit.unitLabel}</td>
                <td>{unit.floor}</td>
                <td>{unit.areaSqm.toFixed(1)}</td>
                <td className={`cad-status cad-status--${unit.status}`}>
                  {t(STATUS_LABEL_KEYS[unit.status])}
                  {unit.missingMetricKey && onProvideMetric && (
                    <button
                      type="button"
                      className="cad-preview__metric-button"
                      disabled={provideMetricDisabled}
                      onClick={() => {
                        onProvideMetric(unit.missingMetricKey!, unit.overrideValue)
                      }}
                    >
                      {unit.overrideValue != null
                        ? t('detection.override.edit')
                        : t('detection.override.add')}
                    </button>
                  )}
                </td>
              </tr>
            ))
          )}
        </tbody>
      </table>
    </section>
  )
}

export default CadDetectionPreview
