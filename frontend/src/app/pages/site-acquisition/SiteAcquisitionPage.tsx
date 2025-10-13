import { useState } from 'react'
import {
  capturePropertyForDevelopment,
  type DevelopmentScenario,
  type SiteAcquisitionResult,
} from '../../../api/siteAcquisition'

const SCENARIO_OPTIONS: Array<{
  value: DevelopmentScenario
  label: string
  description: string
  icon: string
}> = [
  {
    value: 'raw_land',
    label: 'New Construction',
    description: 'Raw land development with ground-up construction',
    icon: '🏗️',
  },
  {
    value: 'existing_building',
    label: 'Renovation',
    description: 'Existing building renovation and modernization',
    icon: '🔨',
  },
  {
    value: 'heritage_property',
    label: 'Heritage Integration',
    description: 'Heritage-protected property with conservation requirements',
    icon: '🏛️',
  },
  {
    value: 'underused_asset',
    label: 'Adaptive Reuse',
    description: 'Underutilized asset repositioning and value-add',
    icon: '♻️',
  },
]

export function SiteAcquisitionPage() {
  const [latitude, setLatitude] = useState('1.3000')
  const [longitude, setLongitude] = useState('103.8500')
  const [selectedScenarios, setSelectedScenarios] = useState<DevelopmentScenario[]>([])
  const [isCapturing, setIsCapturing] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [capturedProperty, setCapturedProperty] = useState<SiteAcquisitionResult | null>(null)

  function toggleScenario(scenario: DevelopmentScenario) {
    setSelectedScenarios((prev) =>
      prev.includes(scenario)
        ? prev.filter((s) => s !== scenario)
        : [...prev, scenario]
    )
  }

  async function handleCapture(e: React.FormEvent) {
    e.preventDefault()
    const lat = parseFloat(latitude)
    const lon = parseFloat(longitude)

    if (isNaN(lat) || isNaN(lon)) {
      setError('Please enter valid coordinates')
      return
    }

    if (selectedScenarios.length === 0) {
      setError('Please select at least one development scenario')
      return
    }

    setIsCapturing(true)
    setError(null)

    try {
      const result = await capturePropertyForDevelopment({
        latitude: lat,
        longitude: lon,
        developmentScenarios: selectedScenarios,
      })

      setCapturedProperty(result)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to capture property')
    } finally {
      setIsCapturing(false)
    }
  }

  return (
    <div
      style={{
        padding: '3rem 2rem',
        maxWidth: '1200px',
        margin: '0 auto',
        fontFamily: '-apple-system, BlinkMacSystemFont, "SF Pro Display", "SF Pro Text", system-ui, sans-serif',
        color: '#1d1d1f',
      }}
    >
      {/* Header */}
      <header style={{ marginBottom: '3rem' }}>
        <h1
          style={{
            fontSize: '3rem',
            fontWeight: 700,
            letterSpacing: '-0.015em',
            margin: '0 0 0.5rem',
            lineHeight: 1.1,
          }}
        >
          Site Acquisition
        </h1>
        <p
          style={{
            fontSize: '1.25rem',
            color: '#6e6e73',
            margin: 0,
            lineHeight: 1.5,
            letterSpacing: '-0.005em',
          }}
        >
          Comprehensive property capture and development feasibility analysis for developers
        </p>
      </header>

      {/* Property Capture Form */}
      <section
        style={{
          background: 'white',
          border: '1px solid #d2d2d7',
          borderRadius: '18px',
          padding: '2rem',
          marginBottom: '2rem',
        }}
      >
        <h2
          style={{
            fontSize: '1.5rem',
            fontWeight: 600,
            marginBottom: '1.5rem',
            letterSpacing: '-0.01em',
          }}
        >
          Property Coordinates
        </h2>

        <form onSubmit={handleCapture}>
          <div
            style={{
              display: 'grid',
              gridTemplateColumns: 'repeat(2, 1fr)',
              gap: '1rem',
              marginBottom: '2rem',
            }}
          >
            <div>
              <label
                htmlFor="latitude"
                style={{
                  display: 'block',
                  fontSize: '0.9375rem',
                  fontWeight: 500,
                  marginBottom: '0.5rem',
                  color: '#1d1d1f',
                }}
              >
                Latitude
              </label>
              <input
                id="latitude"
                type="text"
                value={latitude}
                onChange={(e) => setLatitude(e.target.value)}
                style={{
                  width: '100%',
                  padding: '0.875rem 1rem',
                  fontSize: '1rem',
                  border: '1px solid #d2d2d7',
                  borderRadius: '12px',
                  outline: 'none',
                  fontFamily: 'ui-monospace, SFMono-Regular, Menlo, Monaco, monospace',
                  transition: 'all 0.2s ease',
                }}
                onFocus={(e) => {
                  e.currentTarget.style.borderColor = '#1d1d1f'
                  e.currentTarget.style.boxShadow = '0 0 0 4px rgba(0, 0, 0, 0.04)'
                }}
                onBlur={(e) => {
                  e.currentTarget.style.borderColor = '#d2d2d7'
                  e.currentTarget.style.boxShadow = 'none'
                }}
              />
            </div>

            <div>
              <label
                htmlFor="longitude"
                style={{
                  display: 'block',
                  fontSize: '0.9375rem',
                  fontWeight: 500,
                  marginBottom: '0.5rem',
                  color: '#1d1d1f',
                }}
              >
                Longitude
              </label>
              <input
                id="longitude"
                type="text"
                value={longitude}
                onChange={(e) => setLongitude(e.target.value)}
                style={{
                  width: '100%',
                  padding: '0.875rem 1rem',
                  fontSize: '1rem',
                  border: '1px solid #d2d2d7',
                  borderRadius: '12px',
                  outline: 'none',
                  fontFamily: 'ui-monospace, SFMono-Regular, Menlo, Monaco, monospace',
                  transition: 'all 0.2s ease',
                }}
                onFocus={(e) => {
                  e.currentTarget.style.borderColor = '#1d1d1f'
                  e.currentTarget.style.boxShadow = '0 0 0 4px rgba(0, 0, 0, 0.04)'
                }}
                onBlur={(e) => {
                  e.currentTarget.style.borderColor = '#d2d2d7'
                  e.currentTarget.style.boxShadow = 'none'
                }}
              />
            </div>
          </div>

          <h3
            style={{
              fontSize: '1.125rem',
              fontWeight: 600,
              marginBottom: '1rem',
              letterSpacing: '-0.01em',
            }}
          >
            Development Scenarios
          </h3>

          <div
            style={{
              display: 'grid',
              gridTemplateColumns: 'repeat(2, 1fr)',
              gap: '1rem',
              marginBottom: '2rem',
            }}
          >
            {SCENARIO_OPTIONS.map((scenario) => {
              const isSelected = selectedScenarios.includes(scenario.value)
              return (
                <button
                  key={scenario.value}
                  type="button"
                  onClick={() => toggleScenario(scenario.value)}
                  style={{
                    background: isSelected ? '#f5f5f7' : 'white',
                    border: `1px solid ${isSelected ? '#1d1d1f' : '#d2d2d7'}`,
                    borderRadius: '12px',
                    padding: '1.25rem',
                    cursor: 'pointer',
                    textAlign: 'left',
                    transition: 'all 0.2s ease',
                    position: 'relative',
                  }}
                  onMouseEnter={(e) => {
                    e.currentTarget.style.transform = 'translateY(-2px)'
                    e.currentTarget.style.boxShadow = '0 8px 16px rgba(0, 0, 0, 0.08)'
                  }}
                  onMouseLeave={(e) => {
                    e.currentTarget.style.transform = 'translateY(0)'
                    e.currentTarget.style.boxShadow = 'none'
                  }}
                >
                  {isSelected && (
                    <div
                      style={{
                        position: 'absolute',
                        top: '1rem',
                        right: '1rem',
                        width: '20px',
                        height: '20px',
                        borderRadius: '50%',
                        background: '#1d1d1f',
                        display: 'flex',
                        alignItems: 'center',
                        justifyContent: 'center',
                        fontSize: '12px',
                        color: 'white',
                      }}
                    >
                      ✓
                    </div>
                  )}
                  <div
                    style={{
                      display: 'flex',
                      alignItems: 'center',
                      gap: '0.75rem',
                      marginBottom: '0.5rem',
                    }}
                  >
                    <span style={{ fontSize: '1.5rem' }}>{scenario.icon}</span>
                    <div
                      style={{
                        fontSize: '1.0625rem',
                        fontWeight: 600,
                        color: '#1d1d1f',
                        letterSpacing: '-0.005em',
                      }}
                    >
                      {scenario.label}
                    </div>
                  </div>
                  <div
                    style={{
                      fontSize: '0.875rem',
                      color: '#6e6e73',
                      lineHeight: 1.4,
                      letterSpacing: '-0.005em',
                    }}
                  >
                    {scenario.description}
                  </div>
                </button>
              )
            })}
          </div>

          <button
            type="submit"
            disabled={isCapturing || selectedScenarios.length === 0}
            style={{
              width: '100%',
              padding: '0.875rem 2rem',
              fontSize: '1.0625rem',
              fontWeight: 500,
              color: 'white',
              background:
                isCapturing || selectedScenarios.length === 0 ? '#d2d2d7' : '#1d1d1f',
              border: 'none',
              borderRadius: '12px',
              cursor:
                isCapturing || selectedScenarios.length === 0 ? 'not-allowed' : 'pointer',
              transition: 'all 0.2s ease',
              letterSpacing: '-0.005em',
            }}
            onMouseEnter={(e) => {
              if (!isCapturing && selectedScenarios.length > 0) {
                e.currentTarget.style.background = '#424245'
              }
            }}
            onMouseLeave={(e) => {
              if (!isCapturing && selectedScenarios.length > 0) {
                e.currentTarget.style.background = '#1d1d1f'
              }
            }}
          >
            {isCapturing ? 'Capturing Property...' : 'Capture Property'}
          </button>

          {error && (
            <div
              style={{
                marginTop: '1rem',
                padding: '1rem',
                background: '#fff5f5',
                border: '1px solid #fed7d7',
                borderRadius: '12px',
                color: '#c53030',
                fontSize: '0.9375rem',
              }}
            >
              {error}
            </div>
          )}

          {capturedProperty && (
            <div
              style={{
                marginTop: '1rem',
                padding: '1rem',
                background: '#f0fdf4',
                border: '1px solid #bbf7d0',
                borderRadius: '12px',
                color: '#15803d',
                fontSize: '0.9375rem',
              }}
            >
              <strong>Property captured successfully</strong>
              <div style={{ marginTop: '0.5rem', fontSize: '0.875rem' }}>
                {capturedProperty.address.fullAddress} • {capturedProperty.address.district}
              </div>
            </div>
          )}
        </form>
      </section>

      {/* Placeholder sections */}
      <section
        style={{
          background: 'white',
          border: '1px solid #d2d2d7',
          borderRadius: '18px',
          padding: '2rem',
          marginBottom: '2rem',
        }}
      >
        <h2
          style={{
            fontSize: '1.5rem',
            fontWeight: 600,
            marginBottom: '1rem',
            letterSpacing: '-0.01em',
          }}
        >
          Due Diligence Checklist
        </h2>
        <div
          style={{
            padding: '3rem 2rem',
            textAlign: 'center',
            color: '#6e6e73',
            background: '#f5f5f7',
            borderRadius: '12px',
          }}
        >
          <div style={{ fontSize: '3rem', marginBottom: '1rem' }}>📋</div>
          <p style={{ margin: 0, fontSize: '1.0625rem' }}>
            Capture a property to view the comprehensive due diligence checklist
          </p>
          <p style={{ margin: '0.5rem 0 0', fontSize: '0.9375rem' }}>
            Automatically generated based on selected development scenarios
          </p>
        </div>
      </section>

      <section
        style={{
          background: 'white',
          border: '1px solid #d2d2d7',
          borderRadius: '18px',
          padding: '2rem',
          marginBottom: '2rem',
        }}
      >
        <h2
          style={{
            fontSize: '1.5rem',
            fontWeight: 600,
            marginBottom: '1rem',
            letterSpacing: '-0.01em',
          }}
        >
          Multi-Scenario Comparison
        </h2>
        <div
          style={{
            padding: '3rem 2rem',
            textAlign: 'center',
            color: '#6e6e73',
            background: '#f5f5f7',
            borderRadius: '12px',
          }}
        >
          <div style={{ fontSize: '3rem', marginBottom: '1rem' }}>📊</div>
          <p style={{ margin: 0, fontSize: '1.0625rem' }}>
            Side-by-side scenario comparison will appear here
          </p>
          <p style={{ margin: '0.5rem 0 0', fontSize: '0.9375rem' }}>
            Cost analysis, timeline, ROI/IRR, and risk assessment matrix
          </p>
        </div>
      </section>

      <section
        style={{
          background: 'white',
          border: '1px solid #d2d2d7',
          borderRadius: '18px',
          padding: '2rem',
        }}
      >
        <h2
          style={{
            fontSize: '1.5rem',
            fontWeight: 600,
            marginBottom: '1rem',
            letterSpacing: '-0.01em',
          }}
        >
          Property Condition Assessment
        </h2>
        <div
          style={{
            padding: '3rem 2rem',
            textAlign: 'center',
            color: '#6e6e73',
            background: '#f5f5f7',
            borderRadius: '12px',
          }}
        >
          <div style={{ fontSize: '3rem', marginBottom: '1rem' }}>🏢</div>
          <p style={{ margin: 0, fontSize: '1.0625rem' }}>
            Detailed property condition analysis coming soon
          </p>
          <p style={{ margin: '0.5rem 0 0', fontSize: '0.9375rem' }}>
            Building scoring, renovation costs, structural and M&E systems evaluation
          </p>
        </div>
      </section>
    </div>
  )
}
