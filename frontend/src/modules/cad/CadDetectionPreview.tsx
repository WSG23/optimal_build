import { DetectedUnit } from './types'
import { useLocale } from '../../i18n/LocaleContext'

interface CadDetectionPreviewProps {
  units: DetectedUnit[]
  overlays: string[]
  hints: string[]
  zoneCode?: string | null
  locked?: boolean
}

const STATUS_LABELS: Record<DetectedUnit['status'], string> = {
  source: 'source',
  pending: 'pending',
  approved: 'approved',
  rejected: 'rejected',
}

export function CadDetectionPreview({
  units,
  overlays,
  hints,
  zoneCode,
  locked = false,
}: CadDetectionPreviewProps) {
  const { strings } = useLocale()
  const floors = Array.from(new Set(units.map((unit) => unit.floor))).sort((a, b) => a - b)

  return (
    <section className="cad-preview">
      <header className="cad-preview__header">
        <div>
          <h2>{strings.detection.title}</h2>
          <p>{strings.detection.subtitle}</p>
        </div>
        <div className="cad-preview__summary">
          <span>{floors.length} floors</span>
          <span>{units.length} units</span>
          {zoneCode && <span>Zone {zoneCode}</span>}
        </div>
      </header>

      <div className="cad-preview__grid">
        <div className="cad-preview__panel">
          <h3>{strings.detection.overlays}</h3>
          {overlays.length === 0 ? <p>—</p> : (
            <ul>
              {overlays.map((overlay) => (
                <li key={overlay}>{overlay}</li>
              ))}
            </ul>
          )}
        </div>
        <div className="cad-preview__panel">
          <h3>{strings.detection.advisory}</h3>
          {hints.length === 0 ? <p>—</p> : (
            <ul>
              {hints.map((hint) => (
                <li key={hint}>{hint}</li>
              ))}
            </ul>
          )}
        </div>
      </div>

      {locked && <p className="cad-preview__lock-indicator">{strings.detection.locked}</p>}

      <table className="cad-preview__table">
        <caption>{strings.detection.tableHeading}</caption>
        <thead>
          <tr>
            <th>{strings.detection.unit}</th>
            <th>{strings.detection.floor}</th>
            <th>{strings.detection.area}</th>
            <th>{strings.detection.status}</th>
          </tr>
        </thead>
        <tbody>
          {units.length === 0 ? (
            <tr>
              <td colSpan={4}>{strings.detection.empty}</td>
            </tr>
          ) : (
            units.map((unit) => (
              <tr key={unit.id}>
                <td>{unit.unitLabel}</td>
                <td>{unit.floor}</td>
                <td>{unit.areaSqm.toFixed(1)}</td>
                <td className={`cad-status cad-status--${unit.status}`}>
                  {strings.controls[STATUS_LABELS[unit.status] as keyof typeof strings.controls]}
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
