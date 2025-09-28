import { useTranslation } from '../../i18n'

interface ZoneLockControlsProps {
  locked: boolean
  onToggle: (next: boolean) => void
}

export function ZoneLockControls({ locked, onToggle }: ZoneLockControlsProps) {
  const { t } = useTranslation()
  const label = locked ? t('controls.unlockZone') : t('controls.lockZone')

  return (
    <section className="cad-panel">
      <h3>{t('controls.locked')}</h3>
      <button
        type="button"
        onClick={() => {
          onToggle(!locked)
        }}
      >
        {label}
      </button>
      {locked && <p className="cad-panel__hint">{t('detection.locked')}</p>}
    </section>
  )
}

export default ZoneLockControls
