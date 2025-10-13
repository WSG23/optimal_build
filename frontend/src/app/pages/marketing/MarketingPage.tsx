import { useMemo, useState } from 'react'
import type { ProfessionalPackType } from '../../../api/agents'
import { useMarketingPacks } from './hooks/useMarketingPacks'

const PACK_TYPES: Array<{
  type: ProfessionalPackType
  label: string
  description: string
  icon: string
  color: string
}> = [
  {
    type: 'universal',
    label: 'Universal Site Pack',
    description: 'Comprehensive 11-page analysis with all scenarios',
    icon: '📊',
    color: '#2563eb',
  },
  {
    type: 'investment',
    label: 'Investment Memorandum',
    description: 'Financial analysis for investors',
    icon: '💼',
    color: '#16a34a',
  },
  {
    type: 'sales',
    label: 'Sales Brief',
    description: 'Marketing material for property sales',
    icon: '🏢',
    color: '#dc2626',
  },
  {
    type: 'lease',
    label: 'Lease Brochure',
    description: 'Leasing collateral with amenities',
    icon: '📋',
    color: '#9333ea',
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
      setPropertyId('') // Clear form after successful generation
      clearError()
    } catch {
      setNotice(null)
    }
  }

  function handleDownload(downloadUrl: string) {
    window.open(downloadUrl, '_blank')
  }

  return (
    <div style={{ padding: '2rem', maxWidth: '1400px', margin: '0 auto' }}>
      {/* Hero Section */}
      <div style={{
        background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
        borderRadius: '1rem',
        padding: '2.5rem',
        marginBottom: '2rem',
        color: 'white',
        boxShadow: '0 20px 25px -5px rgba(0, 0, 0, 0.1), 0 10px 10px -5px rgba(0, 0, 0, 0.04)',
      }}>
        <h1 style={{ fontSize: '2.5rem', fontWeight: 700, marginBottom: '0.5rem', margin: 0 }}>
          Marketing Packs
        </h1>
        <p style={{ fontSize: '1.125rem', opacity: 0.95, margin: '0.5rem 0 0' }}>
          Generate professional PDF materials for investors, buyers, and tenants
        </p>
        <div style={{ marginTop: '1rem', fontSize: '0.875rem', opacity: 0.9 }}>
          {formattedDate} • {packs.length} packs generated
        </div>
      </div>

      {/* Pack Type Selector - Card Grid */}
      <div style={{ marginBottom: '2rem' }}>
        <h2 style={{ fontSize: '1.5rem', fontWeight: 600, marginBottom: '1rem', color: '#0f172a' }}>
          Choose Pack Type
        </h2>
        <div style={{
          display: 'grid',
          gridTemplateColumns: 'repeat(auto-fit, minmax(250px, 1fr))',
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
                  background: isSelected ? 'white' : '#f8fafc',
                  border: `2px solid ${isSelected ? pack.color : '#e2e8f0'}`,
                  borderRadius: '0.75rem',
                  padding: '1.25rem',
                  cursor: isGenerating ? 'not-allowed' : 'pointer',
                  textAlign: 'left',
                  transition: 'all 0.2s ease',
                  boxShadow: isSelected
                    ? `0 4px 6px -1px ${pack.color}33, 0 2px 4px -1px ${pack.color}22`
                    : '0 1px 3px 0 rgba(0, 0, 0, 0.1)',
                  opacity: isGenerating ? 0.6 : 1,
                  transform: isSelected ? 'scale(1.02)' : 'scale(1)',
                }}
                onMouseEnter={(e) => {
                  if (!isGenerating && !isSelected) {
                    e.currentTarget.style.borderColor = pack.color
                    e.currentTarget.style.transform = 'scale(1.02)'
                  }
                }}
                onMouseLeave={(e) => {
                  if (!isSelected) {
                    e.currentTarget.style.borderColor = '#e2e8f0'
                    e.currentTarget.style.transform = 'scale(1)'
                  }
                }}
              >
                <div style={{
                  fontSize: '2.5rem',
                  marginBottom: '0.75rem',
                  filter: isSelected ? 'none' : 'grayscale(0.5)',
                }}>
                  {pack.icon}
                </div>
                <div style={{
                  fontSize: '1.125rem',
                  fontWeight: 600,
                  color: isSelected ? pack.color : '#0f172a',
                  marginBottom: '0.5rem',
                }}>
                  {pack.label}
                </div>
                <div style={{
                  fontSize: '0.875rem',
                  color: '#64748b',
                  lineHeight: 1.5,
                }}>
                  {pack.description}
                </div>
              </button>
            )
          })}
        </div>
      </div>

      {/* Generation Form */}
      <div style={{
        background: 'white',
        borderRadius: '1rem',
        padding: '2rem',
        marginBottom: '2rem',
        boxShadow: '0 1px 3px 0 rgba(0, 0, 0, 0.1), 0 1px 2px 0 rgba(0, 0, 0, 0.06)',
      }}>
        <h2 style={{ fontSize: '1.25rem', fontWeight: 600, marginBottom: '1.5rem', color: '#0f172a' }}>
          Generate {selectedPackInfo?.label}
        </h2>

        <div style={{ marginBottom: '1.5rem' }}>
          <label
            htmlFor="property-id"
            style={{
              display: 'block',
              fontSize: '0.875rem',
              fontWeight: 600,
              color: '#374151',
              marginBottom: '0.5rem',
            }}
          >
            Property ID <span style={{ color: '#dc2626' }}>*</span>
          </label>
          <input
            id="property-id"
            type="text"
            placeholder="e.g. 4b7c0f9e-a1b2-c3d4-e5f6-1234567890ab"
            value={propertyId}
            onChange={(event) => setPropertyId(event.target.value)}
            disabled={isGenerating}
            style={{
              width: '100%',
              padding: '0.75rem 1rem',
              fontSize: '1rem',
              border: '2px solid #e2e8f0',
              borderRadius: '0.5rem',
              outline: 'none',
              transition: 'border-color 0.2s ease',
              background: isGenerating ? '#f8fafc' : 'white',
            }}
            onFocus={(e) => {
              e.currentTarget.style.borderColor = selectedPackInfo?.color || '#2563eb'
            }}
            onBlur={(e) => {
              e.currentTarget.style.borderColor = '#e2e8f0'
            }}
          />
        </div>

        <button
          type="button"
          onClick={handleGenerate}
          disabled={isGenerating || propertyId.trim() === ''}
          style={{
            width: '100%',
            padding: '1rem 2rem',
            fontSize: '1rem',
            fontWeight: 600,
            color: 'white',
            background: isGenerating || !propertyId.trim()
              ? '#94a3b8'
              : selectedPackInfo?.color || '#2563eb',
            border: 'none',
            borderRadius: '0.5rem',
            cursor: isGenerating || !propertyId.trim() ? 'not-allowed' : 'pointer',
            transition: 'all 0.2s ease',
            boxShadow: '0 4px 6px -1px rgba(0, 0, 0, 0.1), 0 2px 4px -1px rgba(0, 0, 0, 0.06)',
          }}
          onMouseEnter={(e) => {
            if (!isGenerating && propertyId.trim()) {
              e.currentTarget.style.transform = 'translateY(-2px)'
              e.currentTarget.style.boxShadow = '0 10px 15px -3px rgba(0, 0, 0, 0.1), 0 4px 6px -2px rgba(0, 0, 0, 0.05)'
            }
          }}
          onMouseLeave={(e) => {
            e.currentTarget.style.transform = 'translateY(0)'
            e.currentTarget.style.boxShadow = '0 4px 6px -1px rgba(0, 0, 0, 0.1), 0 2px 4px -1px rgba(0, 0, 0, 0.06)'
          }}
        >
          {isGenerating
            ? `⏳ Generating ${formatPackLabel(generatingType || selectedPackType)}...`
            : `🚀 Generate ${selectedPackInfo?.label}`}
        </button>

        {error && (
          <div style={{
            marginTop: '1rem',
            padding: '1rem',
            background: '#fee2e2',
            border: '1px solid #fecaca',
            borderRadius: '0.5rem',
            color: '#991b1b',
            fontSize: '0.875rem',
          }}>
            <strong>Error:</strong> {error}
          </div>
        )}
        {notice && (
          <div style={{
            marginTop: '1rem',
            padding: '1rem',
            background: '#fef3c7',
            border: '1px solid #fde68a',
            borderRadius: '0.5rem',
            color: '#92400e',
            fontSize: '0.875rem',
          }}>
            <strong>Notice:</strong> {notice}
          </div>
        )}
      </div>

      {/* Generated Packs List */}
      <div style={{
        background: 'white',
        borderRadius: '1rem',
        padding: '2rem',
        boxShadow: '0 1px 3px 0 rgba(0, 0, 0, 0.1), 0 1px 2px 0 rgba(0, 0, 0, 0.06)',
      }}>
        <h2 style={{
          fontSize: '1.5rem',
          fontWeight: 600,
          marginBottom: '1.5rem',
          color: '#0f172a',
          display: 'flex',
          alignItems: 'center',
          gap: '0.75rem',
        }}>
          Generated Packs
          <span style={{
            background: '#e0f2fe',
            color: '#0369a1',
            fontSize: '0.875rem',
            fontWeight: 600,
            padding: '0.25rem 0.75rem',
            borderRadius: '999px',
          }}>
            {packs.length}
          </span>
        </h2>

        {packs.length === 0 ? (
          <div style={{
            padding: '3rem 2rem',
            textAlign: 'center',
            background: '#f8fafc',
            borderRadius: '0.75rem',
            border: '2px dashed #cbd5e1',
          }}>
            <div style={{ fontSize: '3rem', marginBottom: '1rem' }}>📄</div>
            <p style={{
              fontSize: '1.125rem',
              fontWeight: 500,
              color: '#475569',
              marginBottom: '0.5rem',
            }}>
              No packs generated yet
            </p>
            <p style={{ fontSize: '0.875rem', color: '#94a3b8', margin: 0 }}>
              Select a pack type and property ID above to generate your first marketing material
            </p>
          </div>
        ) : (
          <div style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
            {packs.map((pack, index) => {
              const packInfo = PACK_TYPES.find((p) => p.type === pack.packType)
              return (
                <div
                  key={`${pack.propertyId}-${pack.packType}-${pack.generatedAt}-${index}`}
                  style={{
                    display: 'flex',
                    alignItems: 'center',
                    gap: '1.5rem',
                    padding: '1.25rem',
                    background: '#f8fafc',
                    border: '1px solid #e2e8f0',
                    borderRadius: '0.75rem',
                    transition: 'all 0.2s ease',
                  }}
                  onMouseEnter={(e) => {
                    e.currentTarget.style.background = '#f1f5f9'
                    e.currentTarget.style.borderColor = packInfo?.color || '#cbd5e1'
                  }}
                  onMouseLeave={(e) => {
                    e.currentTarget.style.background = '#f8fafc'
                    e.currentTarget.style.borderColor = '#e2e8f0'
                  }}
                >
                  {/* Icon */}
                  <div style={{
                    fontSize: '2.5rem',
                    flexShrink: 0,
                  }}>
                    {packInfo?.icon || '📄'}
                  </div>

                  {/* Info */}
                  <div style={{ flex: 1, minWidth: 0 }}>
                    <div style={{
                      fontSize: '1.125rem',
                      fontWeight: 600,
                      color: '#0f172a',
                      marginBottom: '0.25rem',
                    }}>
                      {formatPackLabel(pack.packType)}
                    </div>
                    <div style={{
                      fontSize: '0.875rem',
                      color: '#64748b',
                      display: 'flex',
                      alignItems: 'center',
                      gap: '1rem',
                      flexWrap: 'wrap',
                    }}>
                      <span style={{
                        fontFamily: 'monospace',
                        background: '#e2e8f0',
                        padding: '0.125rem 0.5rem',
                        borderRadius: '0.25rem',
                      }}>
                        {pack.propertyId.length > 16
                          ? `${pack.propertyId.substring(0, 16)}...`
                          : pack.propertyId}
                      </span>
                      <span>•</span>
                      <span>{new Date(pack.generatedAt).toLocaleString()}</span>
                      <span>•</span>
                      <span style={{ fontWeight: 500 }}>{formatSize(pack.sizeBytes)}</span>
                    </div>
                  </div>

                  {/* Action */}
                  <div style={{ flexShrink: 0 }}>
                    {pack.downloadUrl ? (
                      <button
                        type="button"
                        onClick={() => handleDownload(pack.downloadUrl!)}
                        style={{
                          padding: '0.75rem 1.5rem',
                          fontSize: '0.875rem',
                          fontWeight: 600,
                          color: 'white',
                          background: packInfo?.color || '#2563eb',
                          border: 'none',
                          borderRadius: '0.5rem',
                          cursor: 'pointer',
                          transition: 'all 0.2s ease',
                          whiteSpace: 'nowrap',
                        }}
                        onMouseEnter={(e) => {
                          e.currentTarget.style.transform = 'translateY(-2px)'
                          e.currentTarget.style.boxShadow = '0 4px 6px -1px rgba(0, 0, 0, 0.1)'
                        }}
                        onMouseLeave={(e) => {
                          e.currentTarget.style.transform = 'translateY(0)'
                          e.currentTarget.style.boxShadow = 'none'
                        }}
                      >
                        ⬇️ Download PDF
                      </button>
                    ) : pack.isFallback ? (
                      <span
                        style={{
                          padding: '0.75rem 1.5rem',
                          fontSize: '0.875rem',
                          color: '#94a3b8',
                          background: '#f1f5f9',
                          borderRadius: '0.5rem',
                          display: 'inline-block',
                        }}
                        title={pack.warning ?? 'Preview pack generated offline'}
                      >
                        Preview Only
                      </span>
                    ) : (
                      <span
                        style={{
                          padding: '0.75rem 1.5rem',
                          fontSize: '0.875rem',
                          color: '#94a3b8',
                          background: '#f1f5f9',
                          borderRadius: '0.5rem',
                          display: 'inline-block',
                        }}
                      >
                        Pending...
                      </span>
                    )}
                  </div>
                </div>
              )
            })}
          </div>
        )}
      </div>
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
