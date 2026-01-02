import { useMemo, useState } from 'react'

import {
  computeSalesVelocity,
  type SalesVelocityResponse,
} from '../../../../../api/advisory'
import { Button } from '../../../../../components/canonical/Button'
import '../../../../../styles/advisory.css'

type Props = {
  jurisdictionCode: string
}

export function SalesVelocityCard({ jurisdictionCode }: Props) {
  const [assetType, setAssetType] = useState('mixed_use')
  const [priceBand, setPriceBand] = useState('1800-2200_psf')
  const [unitsPlanned, setUnitsPlanned] = useState<number | null>(200)
  const [launchWindow, setLaunchWindow] = useState('2025-Q2')
  const [inventoryMonths, setInventoryMonths] = useState('')
  const [recentAbsorption, setRecentAbsorption] = useState('')
  const [result, setResult] = useState<SalesVelocityResponse | null>(null)
  const [error, setError] = useState<string | null>(null)
  const [isLoading, setIsLoading] = useState(false)
  const [lastCalculated, setLastCalculated] = useState<Date | null>(null)

  const disabled = useMemo(() => isLoading, [isLoading])

  const parseNumber = (value: string): number | null => {
    const trimmed = value.trim()
    if (!trimmed) return null
    const parsed = Number(trimmed)
    return Number.isFinite(parsed) ? parsed : null
  }

  async function handleCompute() {
    setIsLoading(true)
    setError(null)
    try {
      const payload = {
        jurisdiction: jurisdictionCode || 'SG',
        asset_type: assetType,
        price_band: priceBand || null,
        units_planned: unitsPlanned,
        launch_window: launchWindow || null,
        inventory_months: parseNumber(inventoryMonths),
        recent_absorption: parseNumber(recentAbsorption),
      }
      const response = await computeSalesVelocity(payload)
      setResult(response)
      setLastCalculated(new Date())
    } catch (err) {
      setError(
        err instanceof Error ? err.message : 'Unable to compute sales velocity',
      )
      setResult(null)
    } finally {
      setIsLoading(false)
    }
  }

  // Format relative time for last calculated
  const formatLastCalculated = (date: Date): string => {
    const now = new Date()
    const diffMs = now.getTime() - date.getTime()
    const diffSecs = Math.floor(diffMs / 1000)
    const diffMins = Math.floor(diffSecs / 60)
    const diffHours = Math.floor(diffMins / 60)

    if (diffSecs < 60) return 'just now'
    if (diffMins < 60) return `${diffMins}m ago`
    if (diffHours < 24) return `${diffHours}h ago`
    return date.toLocaleDateString()
  }

  return (
    <section className="sales-velocity">
      {/* Context: Header outside card */}
      <div className="sales-velocity__header">
        <div>
          <h3 className="sales-velocity__title">Sales Velocity Model</h3>
          <p className="sales-velocity__subtitle">
            Forecast launch cadence using market defaults and optional
            overrides.
          </p>
        </div>
        <div className="sales-velocity__actions">
          {lastCalculated && (
            <span className="sales-velocity__status">
              <span className="sales-velocity__status-dot" />
              Updated {formatLastCalculated(lastCalculated)}
            </span>
          )}
          <Button
            variant="primary"
            size="sm"
            onClick={handleCompute}
            disabled={disabled}
          >
            {disabled ? 'Computing…' : 'Run forecast'}
          </Button>
        </div>
      </div>

      {/* Content: Inputs - seamless glass surface */}
      <div className="sales-velocity__surface ob-seamless-panel ob-seamless-panel--glass">
        <div className="sales-velocity__grid">
          <SelectField
            label="Asset type"
            value={assetType}
            onChange={(value) => setAssetType(value)}
            options={[
              { value: 'residential', label: 'Residential' },
              { value: 'office', label: 'Office' },
              { value: 'retail', label: 'Retail' },
              { value: 'mixed_use', label: 'Mixed-use' },
              { value: 'industrial', label: 'Industrial' },
            ]}
          />
          <InputField
            label="Price band"
            value={priceBand}
            onChange={setPriceBand}
            placeholder="1800-2200_psf"
          />
          <InputField
            label="Units planned"
            type="number"
            value={unitsPlanned === null ? '' : String(unitsPlanned)}
            onChange={(val) => setUnitsPlanned(val === '' ? null : Number(val))}
            min={0}
          />
          <InputField
            label="Launch window"
            value={launchWindow}
            onChange={setLaunchWindow}
            placeholder="2025-Q2"
          />
          <InputField
            label="Inventory (months, optional)"
            type="number"
            value={inventoryMonths}
            onChange={setInventoryMonths}
            min={0}
            step="0.1"
          />
          <InputField
            label="Recent absorption (units/mo, optional)"
            type="number"
            value={recentAbsorption}
            onChange={setRecentAbsorption}
            min={0}
            step="0.1"
          />
        </div>

        {error && <div className="sales-velocity__error">{error}</div>}

        {result && (
          <div className="sales-velocity__results">
            <div className="sales-velocity__grid">
              <StatCard
                label="Velocity"
                value={
                  result.forecast.velocity_units_per_month != null
                    ? `${result.forecast.velocity_units_per_month} units/mo`
                    : '—'
                }
              />
              <StatCard
                label="Absorption"
                value={
                  result.forecast.absorption_months != null
                    ? `${result.forecast.absorption_months} months`
                    : '—'
                }
              />
              <StatCard
                label="Confidence"
                value={`${(result.forecast.confidence * 100).toFixed(0)}%`}
              />
            </div>

            {result.risks.length > 0 && (
              <div className="sales-velocity__risks">
                {result.risks.map((risk, idx) => (
                  <span
                    key={idx}
                    className={`advisory__risk-tag advisory__risk-tag--${risk.level}`}
                  >
                    {risk.label} ({risk.level})
                  </span>
                ))}
              </div>
            )}

            {result.recommendations.length > 0 && (
              <div>
                <h4 className="sales-velocity__section-title">
                  Recommendations
                </h4>
                <ul className="sales-velocity__recommendations">
                  {result.recommendations.map((rec, idx) => (
                    <li key={idx}>{rec}</li>
                  ))}
                </ul>
              </div>
            )}

            <div>
              <h4 className="sales-velocity__section-title">Benchmarks</h4>
              <div className="sales-velocity__benchmarks">
                <Benchmark
                  label="Inventory"
                  value={result.benchmarks.inventory_months}
                  suffix="months"
                />
                <Benchmark
                  label="Velocity p25 / p50 / p75"
                  value={[
                    result.benchmarks.velocity_p25,
                    result.benchmarks.velocity_median,
                    result.benchmarks.velocity_p75,
                  ]
                    .map((v) => (v == null ? '—' : v))
                    .join(' / ')}
                  suffix="units/mo"
                />
                <Benchmark
                  label="Median PSF"
                  value={result.benchmarks.median_psf}
                />
              </div>
            </div>
          </div>
        )}
      </div>
    </section>
  )
}

type InputFieldProps = {
  label: string
  value: string
  onChange: (value: string) => void
  type?: string
  placeholder?: string
  min?: number
  step?: string
}

function InputField({
  label,
  value,
  onChange,
  type = 'text',
  placeholder,
  min,
  step,
}: InputFieldProps) {
  return (
    <div className="sales-velocity__field">
      <label className="sales-velocity__label">{label}</label>
      <input
        type={type}
        value={value}
        onChange={(e) => onChange(e.target.value)}
        placeholder={placeholder}
        min={min}
        step={step}
        className="sales-velocity__input"
      />
    </div>
  )
}

type SelectFieldProps = {
  label: string
  value: string
  onChange: (value: string) => void
  options: Array<{ value: string; label: string }>
}

function SelectField({ label, value, onChange, options }: SelectFieldProps) {
  return (
    <div className="sales-velocity__field">
      <label className="sales-velocity__label">{label}</label>
      <select
        value={value}
        onChange={(e) => onChange(e.target.value)}
        className="sales-velocity__select"
      >
        {options.map((option) => (
          <option key={option.value} value={option.value}>
            {option.label}
          </option>
        ))}
      </select>
    </div>
  )
}

type StatCardProps = { label: string; value: string }

function StatCard({ label, value }: StatCardProps) {
  return (
    <div className="sales-velocity__stat-card">
      <div className="sales-velocity__stat-label">{label}</div>
      <div className="sales-velocity__stat-value">{value}</div>
    </div>
  )
}

type BenchmarkProps = {
  label: string
  value: string | number | null
  suffix?: string
}

function Benchmark({ label, value, suffix }: BenchmarkProps) {
  const display =
    value == null || value === ''
      ? '—'
      : suffix
        ? `${value} ${suffix}`
        : String(value)
  return (
    <div className="sales-velocity__benchmark-card">
      <div className="sales-velocity__benchmark-label">{label}</div>
      <div className="sales-velocity__benchmark-value">{display}</div>
    </div>
  )
}
