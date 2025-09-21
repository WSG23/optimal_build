import { useTranslation } from '../../i18n'
import { DetectionStatus } from './types'
import { computeNextLayers } from './layerToggle'

interface LayerTogglePanelProps {
  activeLayers: DetectionStatus[]
  onToggle: (status: DetectionStatus, next: DetectionStatus[]) => void
  disabled?: boolean
}

const ORDER: DetectionStatus[] = ['source', 'pending', 'approved', 'rejected']
const LABEL_KEYS: Record<DetectionStatus, string> = {
  source: 'controls.source',
  pending: 'controls.pending',
  approved: 'controls.approved',
  rejected: 'controls.rejected',
}

export function LayerTogglePanel({ activeLayers, onToggle, disabled = false }: LayerTogglePanelProps) {
  const { t } = useTranslation()

  const handleToggle = (status: DetectionStatus) => {
    if (disabled) {
      return
    }
    const next = computeNextLayers(activeLayers, status)
    onToggle(status, next)
  }

  return (
    <section className="cad-panel">
      <h3>{t('controls.showLayer')}</h3>
      <div className="cad-layer-toggle">
        {ORDER.map((status) => {
          const isActive = activeLayers.includes(status)
          return (
            <button
              key={status}
              type="button"
              className={`cad-layer-toggle__button${isActive ? ' cad-layer-toggle__button--active' : ''}`}
              onClick={() => handleToggle(status)}
              aria-pressed={isActive}
              disabled={disabled}
            >
              {t(LABEL_KEYS[status])}
            </button>
          )
        })}
      </div>
    </section>
  )
}

export default LayerTogglePanel
