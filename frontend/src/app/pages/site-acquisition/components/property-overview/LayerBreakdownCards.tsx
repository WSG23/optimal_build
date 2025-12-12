/**
 * Layer Breakdown Cards Component
 *
 * Displays detailed optimiser output per massing layer
 * (allocation, GFA, NIA, and height metrics).
 */

import type { LayerBreakdownItem } from '../../types'

// ============================================================================
// Types
// ============================================================================

export interface LayerBreakdownCardsProps {
  /** Pre-computed layer breakdown items */
  layers: LayerBreakdownItem[]
}

// ============================================================================
// Component
// ============================================================================

export function LayerBreakdownCards({ layers }: LayerBreakdownCardsProps) {
  if (layers.length === 0) {
    return null
  }

  return (
    <section
      style={{
        marginTop: '2rem',
        border: '1px solid #e5e7eb',
        borderRadius: '4px',
        padding: '1.5rem',
        background: '#ffffff',
        display: 'flex',
        flexDirection: 'column',
        gap: '1.25rem',
      }}
    >
      <div
        style={{
          display: 'flex',
          flexDirection: 'column',
          gap: '0.35rem',
        }}
      >
        <h4
          style={{
            margin: 0,
            fontSize: '1rem',
            fontWeight: 600,
            letterSpacing: '-0.01em',
            color: '#111827',
          }}
        >
          Layer breakdown
        </h4>
        <p
          style={{
            margin: 0,
            fontSize: '0.9rem',
            color: '#4b5563',
          }}
        >
          Detailed optimiser output per massing layer (allocation, GFA, NIA, and
          height).
        </p>
      </div>
      <div
        style={{
          display: 'grid',
          gridTemplateColumns: 'repeat(auto-fit, minmax(220px, 1fr))',
          gap: '1rem',
        }}
      >
        {layers.map((layer) => (
          <article
            key={layer.id}
            style={{
              border: '1px solid #e5e7eb',
              borderRadius: '4px',
              padding: '1rem',
              display: 'flex',
              flexDirection: 'column',
              gap: '0.75rem',
              background: '#f9fafb',
            }}
          >
            <div
              style={{ display: 'flex', alignItems: 'center', gap: '0.65rem' }}
            >
              <span
                aria-hidden="true"
                style={{
                  width: '14px',
                  height: '14px',
                  borderRadius: '9999px',
                  background: layer.color,
                  boxShadow: '0 0 0 1px rgb(255 255 255 / 0.8)',
                }}
              />
              <div
                style={{
                  display: 'flex',
                  flexDirection: 'column',
                  gap: '0.15rem',
                }}
              >
                <span
                  style={{
                    fontWeight: 600,
                    letterSpacing: '-0.01em',
                    color: '#111827',
                  }}
                >
                  {layer.label}
                </span>
                <span style={{ fontSize: '0.85rem', color: '#6b7280' }}>
                  {layer.subtitle}
                </span>
              </div>
            </div>
            <dl
              style={{
                margin: 0,
                display: 'grid',
                gridTemplateColumns: 'repeat(auto-fit, minmax(120px, 1fr))',
                gap: '0.5rem',
              }}
            >
              {layer.metrics.map((metric) => (
                <div
                  key={`${layer.id}-${metric.label}`}
                  style={{
                    display: 'flex',
                    flexDirection: 'column',
                    gap: '0.15rem',
                  }}
                >
                  <dt
                    style={{
                      margin: 0,
                      fontSize: '0.7rem',
                      letterSpacing: '0.08em',
                      textTransform: 'uppercase',
                      color: '#9ca3af',
                      fontWeight: 600,
                    }}
                  >
                    {metric.label}
                  </dt>
                  <dd
                    style={{
                      margin: 0,
                      fontWeight: 600,
                      color: '#1f2937',
                      fontSize: '0.95rem',
                    }}
                  >
                    {metric.value}
                  </dd>
                </div>
              ))}
            </dl>
            {layer.description && (
              <p
                style={{
                  margin: 0,
                  fontSize: '0.8rem',
                  color: '#4b5563',
                }}
              >
                {layer.description}
              </p>
            )}
          </article>
        ))}
      </div>
    </section>
  )
}
