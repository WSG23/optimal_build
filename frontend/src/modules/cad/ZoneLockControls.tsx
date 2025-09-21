import { useLocale } from '../../i18n/LocaleContext'

interface ZoneLockControlsProps {
  locked: boolean
  onToggle: (next: boolean) => void
}

export function ZoneLockControls({ locked, onToggle }: ZoneLockControlsProps) {
  const { strings } = useLocale()
  const label = locked ? strings.controls.unlockZone : strings.controls.lockZone

  return (
    <section className="cad-panel">
      <h3>{strings.controls.locked}</h3>
      <button type="button" onClick={() => onToggle(!locked)}>
        {label}
      </button>
      {locked && <p className="cad-panel__hint">{strings.detection.locked}</p>}
    </section>
  )
}

export default ZoneLockControls
