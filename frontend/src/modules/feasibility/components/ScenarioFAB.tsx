import { AutoAwesome } from '@mui/icons-material'

interface ScenarioFABProps {
  label: string
  onClick: () => void
  disabled?: boolean
  loading?: boolean
}

export function ScenarioFAB({ label, onClick, disabled, loading }: ScenarioFABProps) {
  return (
    <div className="scenario-fab-container">
      <button
        type="button"
        className="scenario-fab"
        onClick={onClick}
        disabled={disabled || loading}
        data-testid="compute-button"
      >
        <span className="scenario-fab__icon">
          {loading ? <span className="scenario-fab__spinner" /> : <AutoAwesome />}
        </span>
        <span className="scenario-fab__label">{label}</span>
      </button>
    </div>
  )
}
