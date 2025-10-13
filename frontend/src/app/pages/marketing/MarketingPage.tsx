import { useMemo, useState } from 'react'
import type { ProfessionalPackType } from '../../../api/agents'
import { useMarketingPacks } from './hooks/useMarketingPacks'

const PACK_TYPES: Array<{
  type: ProfessionalPackType
  label: string
  description: string
}> = [
  {
    type: 'universal',
    label: 'Universal Site Pack',
    description: 'Comprehensive analysis with all development scenarios',
  },
  {
    type: 'investment',
    label: 'Investment Memorandum',
    description: 'Financial analysis for institutional investors',
  },
  {
    type: 'sales',
    label: 'Sales Brief',
    description: 'Professional marketing material for property sales',
  },
  {
    type: 'lease',
    label: 'Lease Brochure',
    description: 'Leasing collateral with amenity documentation',
  },
]

export function MarketingPage() {
  const {
    packs,
    isGenerating,
    generatingType,
    error,
    generatePack,
    clearError,
  } = useMarketingPacks()
  const [propertyId, setPropertyId] = useState('')
  const [selectedPackType, setSelectedPackType] =
    useState<ProfessionalPackType>('universal')
  const [notice, setNotice] = useState<string | null>(null)

  const formattedDate = useMemo(
    () => new Date().toLocaleString(undefined, { dateStyle: 'medium' }),
    [],
  )

  const selectedPackInfo = PACK_TYPES.find((p) => p.type === selectedPackType)

  async function handleGenerate() {
    if (!propertyId.trim()) {
      return
    }
    try {
      const summary = await generatePack(propertyId.trim(), selectedPackType)
      setNotice(summary.warning ?? null)
      setPropertyId('')
      clearError()
    } catch {
      setNotice(null)
    }
  }

  function handleDownload(downloadUrl: string) {
    window.open(downloadUrl, '_blank')
  }

  return (
    <div style={{
      padding: '3rem 2rem',
      maxWidth: '980px',
      margin: '0 auto',
      fontFamily: '-apple-system, BlinkMacSystemFont, "SF Pro Display", "SF Pro Text", system-ui, sans-serif',
      color: '#1d1d1f',
    }}>
      {/* Header */}
      <header style={{ marginBottom: '3rem' }}>
        <h1 style={{
          fontSize: '3rem',
          fontWeight: 700,
          letterSpacing: '-0.015em',
          margin: '0 0 0.5rem',
          lineHeight: 1.1,
        }}>
          Marketing Packs
        </h1>
        <p style={{
          fontSize: '1.25rem',
          color: '#6e6e73',
          fontWeight: 400,
          margin: 0,
          letterSpacing: '-0.01em',
        }}>
          Professional materials for investors and stakeholders
        </p>
      </header>

      {/* Pack Type Selector */}
      <section style={{ marginBottom: '3rem' }}>
        <h2 style={{
          fontSize: '1.75rem',
          fontWeight: 600,
          letterSpacing: '-0.01em',
          margin: '0 0 1.5rem',
        }}>
          Choose a template
        </h2>
        <div style={{
          display: 'grid',
          gridTemplateColumns: 'repeat(2, 1fr)',
          gap: '1rem',
        }}>
          {PACK_TYPES.map((pack) => {
            const isSelected = selectedPackType === pack.type
            return (
              <button
                key={pack.type}
                type="button"
                onClick={() => setSelectedPackType(pack.type)}
                disabled={isGenerating}
                style={{
                  background: isSelected ? '#f5f5f7' : 'white',
                  border: `1px solid ${isSelected ? '#1d1d1f' : '#d2d2d7'}`,
                  borderRadius: '18px',
                  padding: '1.5rem',
                  cursor: isGenerating ? 'not-allowed' : 'pointer',
                  textAlign: 'left',
                  transition: 'all 0.3s cubic-bezier(0.4, 0, 0.2, 1)',
                  opacity: isGenerating ? 0.4 : 1,
                  position: 'relative',
                  overflow: 'hidden',
                }}
                onMouseEnter={(e) => {
                  if (!isGenerating) {
                    e.currentTarget.style.transform = 'translateY(-2px)'
                    e.currentTarget.style.boxShadow = '0 8px 24px rgba(0, 0, 0, 0.08)'
                  }
                }}
                onMouseLeave={(e) => {
                  e.currentTarget.style.transform = 'translateY(0)'
                  e.currentTarget.style.boxShadow = 'none'
                }}
              >
                {isSelected && (
                  <div style={{
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
                  }}>
                    ✓
                  </div>
                )}
                <div style={{
                  fontSize: '1.125rem',
                  fontWeight: 600,
                  color: '#1d1d1f',
                  marginBottom: '0.5rem',
                  letterSpacing: '-0.01em',
                }}>
                  {pack.label}
                </div>
                <div style={{
                  fontSize: '0.9375rem',
                  color: '#6e6e73',
                  lineHeight: 1.5,
                  letterSpacing: '-0.005em',
                }}>
                  {pack.description}
                </div>
              </button>
            )
          })}
        </div>
      </section>

      {/* Generation Form */}
      <section style={{
        background: 'white',
        border: '1px solid #d2d2d7',
        borderRadius: '18px',
        padding: '2rem',
        marginBottom: '3rem',
      }}>
        <h3 style={{
          fontSize: '1.25rem',
          fontWeight: 600,
          margin: '0 0 1.5rem',
          letterSpacing: '-0.01em',
        }}>
          Generate {selectedPackInfo?.label}
        </h3>

        <div style={{ marginBottom: '1.5rem' }}>
          <label
            htmlFor="property-id"
            style={{
              display: 'block',
              fontSize: '0.875rem',
              fontWeight: 500,
              color: '#1d1d1f',
              marginBottom: '0.5rem',
              letterSpacing: '-0.005em',
            }}
          >
            Property ID
          </label>
          <input
            id="property-id"
            type="text"
            placeholder="Enter property identifier"
            value={propertyId}
            onChange={(event) => setPropertyId(event.target.value)}
            disabled={isGenerating}
            style={{
              width: '100%',
              padding: '0.875rem 1rem',
              fontSize: '1rem',
              border: '1px solid #d2d2d7',
              borderRadius: '12px',
              outline: 'none',
              transition: 'border-color 0.2s ease, box-shadow 0.2s ease',
              background: isGenerating ? '#f5f5f7' : 'white',
              fontFamily: 'ui-monospace, SFMono-Regular, Menlo, Monaco, monospace',
              letterSpacing: '-0.005em',
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

        <button
          type="button"
          onClick={handleGenerate}
          disabled={isGenerating || propertyId.trim() === ''}
          style={{
            width: '100%',
            padding: '0.875rem 1.5rem',
            fontSize: '1.0625rem',
            fontWeight: 500,
            color: 'white',
            background: isGenerating || !propertyId.trim() ? '#d2d2d7' : '#1d1d1f',
            border: 'none',
            borderRadius: '12px',
            cursor: isGenerating || !propertyId.trim() ? 'not-allowed' : 'pointer',
            transition: 'all 0.2s ease',
            letterSpacing: '-0.005em',
          }}
          onMouseEnter={(e) => {
            if (!isGenerating && propertyId.trim()) {
              e.currentTarget.style.background = '#424245'
            }
          }}
          onMouseLeave={(e) => {
            if (!isGenerating && propertyId.trim()) {
              e.currentTarget.style.background = '#1d1d1f'
            }
          }}
        >
          {isGenerating ? 'Generating...' : 'Generate'}
        </button>

        {error && (
          <div style={{
            marginTop: '1rem',
            padding: '0.875rem 1rem',
            background: '#fff5f5',
            border: '1px solid #ffe0e0',
            borderRadius: '12px',
            color: '#d70015',
            fontSize: '0.9375rem',
            letterSpacing: '-0.005em',
          }}>
            {error}
          </div>
        )}
        {notice && (
          <div style={{
            marginTop: '1rem',
            padding: '0.875rem 1rem',
            background: '#fff9e6',
            border: '1px solid #ffe8b3',
            borderRadius: '12px',
            color: '#996600',
            fontSize: '0.9375rem',
            letterSpacing: '-0.005em',
          }}>
            {notice}
          </div>
        )}
      </section>

      {/* Generated Packs List */}
      <section>
        <div style={{
          display: 'flex',
          alignItems: 'baseline',
          justifyContent: 'space-between',
          marginBottom: '1.5rem',
        }}>
          <h2 style={{
            fontSize: '1.75rem',
            fontWeight: 600,
            letterSpacing: '-0.01em',
            margin: 0,
          }}>
            Library
          </h2>
          <span style={{
            fontSize: '0.9375rem',
            color: '#6e6e73',
            fontWeight: 400,
          }}>
            {packs.length} {packs.length === 1 ? 'pack' : 'packs'}
          </span>
        </div>

        {packs.length === 0 ? (
          <div style={{
            padding: '4rem 2rem',
            textAlign: 'center',
            background: 'white',
            border: '1px solid #d2d2d7',
            borderRadius: '18px',
          }}>
            <div style={{
              width: '60px',
              height: '60px',
              margin: '0 auto 1.5rem',
              background: '#f5f5f7',
              borderRadius: '50%',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              fontSize: '1.5rem',
            }}>
              📄
            </div>
            <p style={{
              fontSize: '1.125rem',
              fontWeight: 500,
              color: '#1d1d1f',
              marginBottom: '0.5rem',
              letterSpacing: '-0.01em',
            }}>
              No packs yet
            </p>
            <p style={{
              fontSize: '0.9375rem',
              color: '#6e6e73',
              margin: 0,
              letterSpacing: '-0.005em',
            }}>
              Generated materials will appear here
            </p>
          </div>
        ) : (
          <div style={{ display: 'flex', flexDirection: 'column', gap: '0.5rem' }}>
            {packs.map((pack, index) => (
              <div
                key={`${pack.propertyId}-${pack.packType}-${pack.generatedAt}-${index}`}
                style={{
                  display: 'flex',
                  alignItems: 'center',
                  gap: '1.5rem',
                  padding: '1.25rem 1.5rem',
                  background: 'white',
                  border: '1px solid #d2d2d7',
                  borderRadius: '16px',
                  transition: 'all 0.2s ease',
                }}
                onMouseEnter={(e) => {
                  e.currentTarget.style.background = '#f5f5f7'
                  e.currentTarget.style.borderColor = '#b8b8bd'
                }}
                onMouseLeave={(e) => {
                  e.currentTarget.style.background = 'white'
                  e.currentTarget.style.borderColor = '#d2d2d7'
                }}
              >
                {/* Info */}
                <div style={{ flex: 1, minWidth: 0 }}>
                  <div style={{
                    fontSize: '1.0625rem',
                    fontWeight: 500,
                    color: '#1d1d1f',
                    marginBottom: '0.25rem',
                    letterSpacing: '-0.005em',
                  }}>
                    {formatPackLabel(pack.packType)}
                  </div>
                  <div style={{
                    fontSize: '0.875rem',
                    color: '#6e6e73',
                    display: 'flex',
                    alignItems: 'center',
                    gap: '0.75rem',
                    letterSpacing: '-0.005em',
                  }}>
                    <span style={{
                      fontFamily: 'ui-monospace, SFMono-Regular, Menlo, Monaco, monospace',
                      fontSize: '0.8125rem',
                    }}>
                      {pack.propertyId.length > 20
                        ? `${pack.propertyId.substring(0, 20)}...`
                        : pack.propertyId}
                    </span>
                    <span style={{ color: '#d2d2d7' }}>·</span>
                    <span>{formatSize(pack.sizeBytes)}</span>
                  </div>
                </div>

                {/* Action */}
                <div style={{ flexShrink: 0 }}>
                  {pack.downloadUrl ? (
                    <button
                      type="button"
                      onClick={() => handleDownload(pack.downloadUrl!)}
                      style={{
                        padding: '0.5rem 1.25rem',
                        fontSize: '0.9375rem',
                        fontWeight: 500,
                        color: '#1d1d1f',
                        background: 'transparent',
                        border: '1px solid #d2d2d7',
                        borderRadius: '10px',
                        cursor: 'pointer',
                        transition: 'all 0.2s ease',
                        whiteSpace: 'nowrap',
                        letterSpacing: '-0.005em',
                      }}
                      onMouseEnter={(e) => {
                        e.currentTarget.style.background = '#1d1d1f'
                        e.currentTarget.style.color = 'white'
                        e.currentTarget.style.borderColor = '#1d1d1f'
                      }}
                      onMouseLeave={(e) => {
                        e.currentTarget.style.background = 'transparent'
                        e.currentTarget.style.color = '#1d1d1f'
                        e.currentTarget.style.borderColor = '#d2d2d7'
                      }}
                    >
                      Download
                    </button>
                  ) : (
                    <span
                      style={{
                        padding: '0.5rem 1.25rem',
                        fontSize: '0.9375rem',
                        color: '#86868b',
                        letterSpacing: '-0.005em',
                      }}
                    >
                      {pack.isFallback ? 'Preview' : 'Processing'}
                    </span>
                  )}
                </div>
              </div>
            ))}
          </div>
        )}
      </section>
    </div>
  )
}

function formatPackLabel(type: ProfessionalPackType) {
  switch (type) {
    case 'universal':
      return 'Universal Site Pack'
    case 'investment':
      return 'Investment Memorandum'
    case 'sales':
      return 'Sales Brief'
    case 'lease':
      return 'Lease Brochure'
    default:
      return type
  }
}

function formatSize(value: number | null) {
  if (!value || Number.isNaN(value)) {
    return '—'
  }
  if (value < 1024) {
    return `${value} B`
  }
  if (value < 1024 * 1024) {
    return `${(value / 1024).toFixed(1)} KB`
  }
  return `${(value / (1024 * 1024)).toFixed(1)} MB`
}
