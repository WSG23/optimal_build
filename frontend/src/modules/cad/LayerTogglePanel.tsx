import { DetectionStatus } from './types'
import { computeNextLayers } from './layerToggle'
import { useLocale } from '../../i18n/LocaleContext'

interface LayerTogglePanelProps {
  activeLayers: DetectionStatus[]
  onToggle: (status: DetectionStatus, next: DetectionStatus[]) => void
  disabled?: boolean
}

const ORDER: DetectionStatus[] = ['source', 'pending', 'approved', 'rejected']

export function LayerTogglePanel({ activeLayers, onToggle, disabled = false }: LayerTogglePanelProps) {
  const { strings } = useLocale()

  const handleToggle = (status: DetectionStatus) => {
    if (disabled) {
      return
    }
    const next = computeNextLayers(activeLayers, status)
    onToggle(status, next)
  }

  const labels: Record<DetectionStatus, string> = {
    source: strings.controls.source,
    pending: strings.controls.pending,
    approved: strings.controls.approved,
    rejected: strings.controls.rejected,
  }

  return (
    <section className="cad-panel">
      <h3>{strings.controls.showLayer}</h3>
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
              {labels[status]}
            </button>
          )
        })}
      </div>
    </section>
  )
}

export default LayerTogglePanel
