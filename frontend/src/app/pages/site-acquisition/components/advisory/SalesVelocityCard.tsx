import { useMemo, useState } from 'react'
import {
  computeSalesVelocity,
  type SalesVelocityResponse,
} from '../../../../../api/advisory'

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
    } catch (err) {
      setError(
        err instanceof Error ? err.message : 'Unable to compute sales velocity',
      )
      setResult(null)
    } finally {
      setIsLoading(false)
    }
  }

  return (
    <section
      style={{
        background: 'white',
        border: '1px solid #e5e7eb',
        borderRadius: '4px',
        padding: '1.5rem',
        display: 'flex',
        flexDirection: 'column',
        gap: '1rem',
      }}
    >
      <div
        style={{
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'flex-start',
          gap: '1rem',
          flexWrap: 'wrap',
        }}
      >
        <div>
          <h3
            style={{
              margin: 0,
              fontSize: '1.1rem',
              fontWeight: 700,
              letterSpacing: '-0.01em',
            }}
          >
            Sales Velocity Model
          </h3>
          <p
            style={{
              margin: '0.25rem 0 0',
              color: '#6b7280',
              fontSize: '0.95rem',
            }}
          >
            Forecast launch cadence using market defaults and optional
            overrides.
          </p>
        </div>
        <button
          type="button"
          onClick={handleCompute}
          disabled={disabled}
          style={{
            padding: '0.65rem 1.4rem',
            borderRadius: '999px',
            border: 'none',
            background: disabled ? '#d1d5db' : '#111827',
            color: 'white',
            fontWeight: 600,
            cursor: disabled ? 'not-allowed' : 'pointer',
          }}
        >
          {disabled ? 'Computing…' : 'Run forecast'}
        </button>
      </div>

      <div
        style={{
          display: 'grid',
          gridTemplateColumns: 'repeat(auto-fit, minmax(180px, 1fr))',
          gap: '0.8rem',
        }}
      >
        <SelectField
          label="Jurisdiction"
          value={jurisdictionCode}
          onChange={() => {
            /* read-only; controlled externally */
          }}
          readOnly
          options={[
            { value: jurisdictionCode, label: jurisdictionCode || 'SG' },
          ]}
        />
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

      {error && (
        <div
          style={{
            background: '#fef2f2',
            border: '1px solid #fecdd3',
            color: '#b91c1c',
            padding: '0.9rem 1rem',
            borderRadius: '4px',
            fontSize: '0.95rem',
          }}
        >
          {error}
        </div>
      )}

      {result && (
        <div
          style={{ display: 'flex', flexDirection: 'column', gap: '0.8rem' }}
        >
          <div
            style={{
              display: 'grid',
              gridTemplateColumns: 'repeat(auto-fit, minmax(180px, 1fr))',
              gap: '0.8rem',
            }}
          >
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
            <div style={{ display: 'flex', gap: '0.5rem', flexWrap: 'wrap' }}>
              {result.risks.map((risk, idx) => (
                <span
                  key={idx}
                  style={{
                    padding: '0.35rem 0.75rem',
                    borderRadius: '999px',
                    border: '1px solid #e5e7eb',
                    background:
                      risk.level === 'high'
                        ? '#fef2f2'
                        : risk.level === 'medium'
                          ? '#fefce8'
                          : '#f1f5f9',
                    color:
                      risk.level === 'high'
                        ? '#b91c1c'
                        : risk.level === 'medium'
                          ? '#854d0e'
                          : '#1f2937',
                    fontSize: '0.85rem',
                    fontWeight: 600,
                  }}
                >
                  {risk.label} ({risk.level})
                </span>
              ))}
            </div>
          )}

          {result.recommendations.length > 0 && (
            <div>
              <h4
                style={{
                  margin: '0 0 0.35rem',
                  fontSize: '1rem',
                  fontWeight: 600,
                }}
              >
                Recommendations
              </h4>
              <ul
                style={{ margin: 0, paddingLeft: '1.25rem', color: '#4b5563' }}
              >
                {result.recommendations.map((rec, idx) => (
                  <li key={idx} style={{ marginBottom: '0.2rem' }}>
                    {rec}
                  </li>
                ))}
              </ul>
            </div>
          )}

          <div>
            <h4
              style={{
                margin: '0 0 0.35rem',
                fontSize: '1rem',
                fontWeight: 600,
              }}
            >
              Benchmarks
            </h4>
            <div
              style={{
                display: 'grid',
                gridTemplateColumns: 'repeat(auto-fit, minmax(160px, 1fr))',
                gap: '0.6rem',
              }}
            >
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
    <div style={{ display: 'flex', flexDirection: 'column', gap: '0.4rem' }}>
      <label style={{ fontSize: '0.85rem', color: '#374151' }}>{label}</label>
      <input
        type={type}
        value={value}
        onChange={(e) => onChange(e.target.value)}
        placeholder={placeholder}
        min={min}
        step={step}
        style={{
          width: '100%',
          padding: '0.75rem',
          borderRadius: '6px',
          border: '1px solid #d2d2d7',
        }}
      />
    </div>
  )
}

type SelectFieldProps = {
  label: string
  value: string
  onChange: (value: string) => void
  options: Array<{ value: string; label: string }>
  readOnly?: boolean
}

function SelectField({
  label,
  value,
  onChange,
  options,
  readOnly,
}: SelectFieldProps) {
  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '0.4rem' }}>
      <label style={{ fontSize: '0.85rem', color: '#374151' }}>{label}</label>
      <select
        value={value}
        onChange={(e) => onChange(e.target.value)}
        disabled={readOnly}
        style={{
          width: '100%',
          padding: '0.75rem',
          borderRadius: '6px',
          border: '1px solid #d2d2d7',
          background: readOnly ? '#f9fafb' : 'white',
        }}
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
    <div
      style={{ padding: '1rem', background: '#f5f5f7', borderRadius: '4px' }}
    >
      <div
        style={{
          fontSize: '0.875rem',
          color: '#6e6e73',
          marginBottom: '0.35rem',
        }}
      >
        {label}
      </div>
      <div style={{ fontSize: '1.35rem', fontWeight: 700 }}>{value}</div>
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
    <div
      style={{ padding: '0.9rem', background: '#f8fafc', borderRadius: '4px' }}
    >
      <div style={{ fontSize: '0.85rem', color: '#6e6e73' }}>{label}</div>
      <div style={{ fontWeight: 600 }}>{display}</div>
    </div>
  )
}
