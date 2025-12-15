import { useState } from 'react'

interface EngineeringLayersPanelProps {
  jurisdiction: string
}

interface LayerConfig {
  key: keyof LayerState
  label: string
  icon: string
}

interface LayerState {
  structural: boolean
  mep: boolean
  plenum: boolean
  civil: boolean
  facade: boolean
}

const LAYERS: LayerConfig[] = [
  {
    key: 'structural',
    label: 'Structural Grid',
    icon: '◼',
  },
  {
    key: 'mep',
    label: 'MEP Trunks & Risers',
    icon: '⚡',
  },
  {
    key: 'plenum',
    label: 'Plenum Depth Validation',
    icon: '≋',
  },
  {
    key: 'facade',
    label: 'Façade Layers',
    icon: '◈',
  },
]

export function EngineeringLayersPanel({
  jurisdiction,
}: EngineeringLayersPanelProps) {
  const [layers, setLayers] = useState<LayerState>({
    structural: true,
    mep: false,
    plenum: false,
    civil: false,
    facade: true,
  })

  const toggleLayer = (key: keyof LayerState) => {
    setLayers((prev) => ({ ...prev, [key]: !prev[key] }))
  }

  return (
    <div className="engineering-layers">
      <div className="engineering-layers__header">
        <h3 className="engineering-layers__title">
          <span>☰</span>
          Engineering Layers ({jurisdiction})
        </h3>
      </div>
      <div className="engineering-layers__content">
        {LAYERS.map((layer) => (
          <div key={layer.key} className="engineering-layers__row">
            <div className="engineering-layers__label-group">
              <span className="engineering-layers__icon" data-layer={layer.key}>
                {layer.icon}
              </span>
              <label
                htmlFor={`${layer.key}-layer`}
                className="engineering-layers__label"
              >
                {layer.label}
              </label>
            </div>
            <label className="toggle-switch">
              <input
                type="checkbox"
                id={`${layer.key}-layer`}
                className="toggle-switch__input"
                checked={layers[layer.key]}
                onChange={() => toggleLayer(layer.key)}
              />
              <span
                className={`toggle-switch__track ${layers[layer.key] ? 'toggle-switch__track--active' : ''}`}
              >
                <span
                  className={`toggle-switch__knob ${layers[layer.key] ? 'toggle-switch__knob--active' : ''}`}
                />
              </span>
            </label>
          </div>
        ))}
      </div>
    </div>
  )
}
