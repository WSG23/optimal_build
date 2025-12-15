import type { ChangeEvent, FormEvent } from 'react'
import { Search, AutoAwesome } from '@mui/icons-material'
import { Fade } from '@mui/material'

interface SmartIntelligenceFieldProps {
  value: string
  siteArea?: number
  zoning?: string
  onChange: (event: ChangeEvent<HTMLInputElement>) => void
  onSubmit: (event: FormEvent<HTMLFormElement>) => void
  onSuggestionSelect?: (suggestion: {
    address: string
    siteArea: number
    zoning: string
  }) => void
  placeholder?: string
  loading?: boolean
  error?: string | null
}

export function SmartIntelligenceField({
  value,
  siteArea,
  zoning,
  onChange,
  onSubmit,
  onSuggestionSelect,
  placeholder = 'Enter site address...',
  loading = false,
  error,
}: SmartIntelligenceFieldProps) {
  // Mock suggestions for visual demo "As user types"
  const showSuggestions =
    value.length > 2 && !loading && !error && onSuggestionSelect && !siteArea

  const handleSelect = (index: number) => {
    if (!onSuggestionSelect) return
    // Simulation logic
    const isCommercial = index === 0
    onSuggestionSelect({
      address: `${value} ${isCommercial ? 'Street' : 'Avenue'}`,
      siteArea: isCommercial ? 1200 : 850,
      zoning: isCommercial ? 'Commercial' : 'Residential',
    })
  }

  // Derived state to show badges
  const hasAutoData = !!siteArea && !!zoning

  return (
    <div
      className="smart-search-wrapper"
      style={{ position: 'relative', width: '100%' }}
    >
      <form
        className="smart-search"
        onSubmit={onSubmit}
        style={{
          display: 'flex',
          alignItems: 'center',
          background: 'rgba(255, 255, 255, 0.95)',
          backdropFilter: 'blur(var(--ob-blur-md))',
          borderRadius: '6px', // Input shape
          padding: '8px 16px',
          boxShadow: '0 8px 32px rgba(0, 0, 0, 0.12)',
          border: '1px solid rgba(255, 255, 255, 0.2)',
          transition: 'all 0.3s ease',
          width: '100%',
          position: 'relative',
        }}
      >
        <Search
          className="smart-search__icon"
          sx={{ color: 'var(--ob-color-text-muted)', marginRight: '12px' }}
        />

        <div
          style={{
            flex: 1,
            position: 'relative',
            display: 'flex',
            alignItems: 'center',
          }}
        >
          <input
            type="text"
            className="smart-search__input"
            value={value}
            onChange={onChange}
            placeholder={placeholder}
            aria-invalid={!!error}
            disabled={loading}
            data-testid="address-input"
            style={{
              border: 'none',
              background: 'transparent',
              fontSize: '1rem',
              width: '100%',
              outline: 'none',
              color: 'var(--ob-color-text-body)',
              height: '32px',
              paddingRight: hasAutoData ? '200px' : '0', // Make space for badges
            }}
          />

          {/* Shiny Auto-Detected Badges */}
          <Fade in={hasAutoData}>
            <div
              style={{
                position: 'absolute',
                right: 0,
                top: '50%',
                transform: 'translateY(-50%)',
                display: 'flex',
                alignItems: 'center',
                gap: '4px',
                pointerEvents: 'none', // Click through to input? Or make interactive?
              }}
            >
              <div
                style={{
                  display: 'flex',
                  alignItems: 'center',
                  gap: '4px',
                  background: 'linear-gradient(135deg, #e0f2fe, #dbeafe)',
                  color: '#0284c7',
                  padding: '4px 8px',
                  borderRadius: '4px',
                  fontSize: '0.75rem',
                  fontWeight: 700,
                  border: '1px solid #bfdbfe',
                  boxShadow: '0 2px 4px rgba(0,0,0,0.05)',
                }}
              >
                <AutoAwesome sx={{ fontSize: 12 }} />
                {siteArea} m²
              </div>
              <div
                style={{
                  background: '#f3f4f6',
                  color: '#4b5563',
                  padding: '4px 8px',
                  borderRadius: '4px',
                  fontSize: '0.75rem',
                  fontWeight: 600,
                  border: '1px solid #e5e7eb',
                }}
              >
                {zoning}
              </div>
            </div>
          </Fade>
        </div>

        {loading ? (
          <div
            className="smart-search__loader"
            style={{
              width: '20px',
              height: '20px',
              border: '2px solid var(--ob-color-brand-primary)',
              borderTopColor: 'transparent',
              borderRadius: '50%',
              animation: 'spin 1s linear infinite',
              marginLeft: '8px',
            }}
          />
        ) : null}
      </form>
      {error && (
        <div
          className="smart-search__error"
          style={{
            position: 'absolute',
            top: '100%',
            left: '24px',
            marginTop: '8px',
            background: '#fee2e2',
            color: '#dc2626',
            padding: '4px 12px',
            borderRadius: '6px',
            fontSize: '0.875rem',
            fontWeight: 500,
          }}
        >
          {error}
        </div>
      )}

      {/* Mock Autocomplete Results */}
      {showSuggestions && (
        <div
          className="smart-search__suggestions"
          style={{
            position: 'absolute',
            top: '100%',
            left: 0,
            right: 0,
            marginTop: '8px',
            background: 'white',
            borderRadius: '4px',
            boxShadow: '0 10px 40px rgba(0,0,0,0.1)',
            padding: '8px',
            zIndex: 100,
            overflow: 'hidden',
          }}
        >
          <div
            style={{
              padding: '8px 12px',
              fontSize: '0.75rem',
              fontWeight: 700,
              color: 'var(--ob-color-text-muted)',
              textTransform: 'uppercase',
              letterSpacing: '0.05em',
            }}
          >
            Suggestions
          </div>
          {['Simulated Result 1', 'Simulated Result 2'].map((_, i) => (
            <div
              key={i}
              style={{
                padding: '12px',
                borderRadius: '4px',
                cursor: 'pointer',
                display: 'flex',
                justifyContent: 'space-between',
                alignItems: 'center',
                transition: 'background 0.2s',
              }}
              className="suggestion-item"
              onClick={() => handleSelect(i)}
            >
              <div
                style={{ display: 'flex', alignItems: 'center', gap: '12px' }}
              >
                <span style={{ fontSize: '1.2rem' }}>📍</span>
                <div>
                  <div
                    style={{
                      fontWeight: 600,
                      color: 'var(--ob-color-text-body)',
                    }}
                  >
                    {value} {i === 0 ? 'Street' : 'Avenue'}
                  </div>
                  <div
                    style={{
                      fontSize: '0.8rem',
                      color: 'var(--ob-color-text-muted)',
                    }}
                  >
                    Singapore, District {9 + i}
                  </div>
                </div>
              </div>
              <span
                style={{
                  fontSize: '0.7rem',
                  fontWeight: 700,
                  padding: '2px 8px',
                  borderRadius: '4px',
                  background: i === 0 ? '#e0f2fe' : '#fef3c7',
                  color: i === 0 ? '#0284c7' : '#d97706',
                }}
              >
                {i === 0 ? 'COMMERCIAL' : 'RESIDENTIAL'}
              </span>
            </div>
          ))}
        </div>
      )}
    </div>
  )
}
