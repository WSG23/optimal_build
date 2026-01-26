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
    siteArea?: number
    zoning?: string
  }) => void
  suggestions?: Array<{
    address: string
    siteArea?: number
    zoning?: string
    subtitle?: string
    badgeLabel?: string
    badgeVariant?: 'info' | 'warning'
  }>
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
  suggestions,
  placeholder = 'Enter site address...',
  loading = false,
  error,
}: SmartIntelligenceFieldProps) {
  const showSuggestions =
    (suggestions?.length ?? 0) > 0 &&
    !loading &&
    !error &&
    onSuggestionSelect &&
    !siteArea

  // Derived state to show badges
  const hasAutoData = !!siteArea && !!zoning

  return (
    <div
      className="smart-search-wrapper"
      style={{ position: 'relative', width: '100%' }}
    >
      <form className="smart-search" onSubmit={onSubmit}>
        <Search
          className="smart-search__icon"
          sx={{ color: 'var(--ob-color-text-muted)' }}
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
                gap: 'var(--ob-space-50)',
                pointerEvents: 'none', // Click through to input? Or make interactive?
              }}
            >
              <div
                style={{
                  display: 'flex',
                  alignItems: 'center',
                  gap: 'var(--ob-space-50)',
                  background: 'var(--ob-color-info-soft)',
                  color: 'var(--ob-info-600)',
                  padding: '4px 8px',
                  borderRadius: 'var(--ob-radius-xs)',
                  fontSize: '0.75rem',
                  fontWeight: 700,
                  border: '1px solid var(--ob-color-border-subtle)',
                  boxShadow: 'var(--ob-shadow-sm)',
                }}
              >
                <AutoAwesome sx={{ fontSize: 12 }} />
                {siteArea} m²
              </div>
              <div
                style={{
                  background: 'var(--ob-color-bg-surface-elevated)',
                  color: 'var(--ob-color-text-secondary)',
                  padding: '4px 8px',
                  borderRadius: 'var(--ob-radius-xs)',
                  fontSize: '0.75rem',
                  fontWeight: 600,
                  border: '1px solid var(--ob-color-border-subtle)',
                }}
              >
                {zoning}
              </div>
            </div>
          </Fade>
        </div>

        {loading ? <div className="smart-search__loader" /> : null}
      </form>
      {error && <div className="smart-search__error">{error}</div>}

      {/* Autocomplete Results */}
      {showSuggestions && suggestions ? (
        <div className="smart-search__suggestions">
          <div className="smart-search__suggestions-header">Suggestions</div>
          {suggestions.map((suggestion, i) => (
            <div
              key={i}
              className="smart-search__suggestion-item"
              onClick={() => onSuggestionSelect?.(suggestion)}
            >
              <div className="smart-search__suggestion-left">
                <span className="smart-search__suggestion-pin">📍</span>
                <div>
                  <div className="smart-search__suggestion-title">
                    {suggestion.address}
                  </div>
                  {suggestion.subtitle ? (
                    <div className="smart-search__suggestion-subtitle">
                      {suggestion.subtitle}
                    </div>
                  ) : null}
                </div>
              </div>
              <span
                className={`smart-search__suggestion-badge ${
                  suggestion.badgeVariant === 'warning'
                    ? 'smart-search__suggestion-badge--warning'
                    : 'smart-search__suggestion-badge--info'
                }`}
              >
                {suggestion.badgeLabel ?? suggestion.zoning}
              </span>
            </div>
          ))}
        </div>
      ) : null}
    </div>
  )
}
