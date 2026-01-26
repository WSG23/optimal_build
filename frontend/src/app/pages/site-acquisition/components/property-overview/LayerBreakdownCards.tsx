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
        marginTop: 'var(--ob-space-400)',
        border: '1px solid var(--ob-color-border-subtle)',
        borderRadius: 'var(--ob-radius-sm)',
        padding: 'var(--ob-space-300)',
        background: 'var(--ob-color-bg-default)',
        display: 'flex',
        flexDirection: 'column',
        gap: 'var(--ob-space-200)',
      }}
    >
      <div
        style={{
          display: 'flex',
          flexDirection: 'column',
          gap: 'var(--ob-space-50)',
        }}
      >
        <h4
          style={{
            margin: 0,
            fontSize: '1rem',
            fontWeight: 600,
            letterSpacing: '-0.01em',
            color: 'var(--ob-color-bg-inverse)',
          }}
        >
          Layer breakdown
        </h4>
        <p
          style={{
            margin: 0,
            fontSize: '0.9rem',
            color: 'var(--ob-color-text-secondary)',
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
          gap: 'var(--ob-space-200)',
        }}
      >
        {layers.map((layer) => (
          <article
            key={layer.id}
            style={{
              border: '1px solid var(--ob-color-border-subtle)',
              borderRadius: 'var(--ob-radius-sm)',
              padding: 'var(--ob-space-200)',
              display: 'flex',
              flexDirection: 'column',
              gap: 'var(--ob-space-150)',
              background: 'var(--ob-color-bg-muted)',
            }}
          >
            <div
              style={{
                display: 'flex',
                alignItems: 'center',
                gap: 'var(--ob-space-150)',
              }}
            >
              <span
                aria-hidden="true"
                style={{
                  width: '14px',
                  height: '14px',
                  borderRadius: 'var(--ob-radius-lg)',
                  background: layer.color,
                  boxShadow: '0 0 0 1px rgb(255 255 255 / 0.8)',
                }}
              />
              <div
                style={{
                  display: 'flex',
                  flexDirection: 'column',
                  gap: 'var(--ob-space-50)',
                }}
              >
                <span
                  style={{
                    fontWeight: 600,
                    letterSpacing: '-0.01em',
                    color: 'var(--ob-color-bg-inverse)',
                  }}
                >
                  {layer.label}
                </span>
                <span
                  style={{
                    fontSize: '0.85rem',
                    color: 'var(--ob-color-text-secondary)',
                  }}
                >
                  {layer.subtitle}
                </span>
              </div>
            </div>
            <dl
              style={{
                margin: 0,
                display: 'grid',
                gridTemplateColumns: 'repeat(auto-fit, minmax(120px, 1fr))',
                gap: 'var(--ob-space-100)',
              }}
            >
              {layer.metrics.map((metric) => (
                <div
                  key={`${layer.id}-${metric.label}`}
                  style={{
                    display: 'flex',
                    flexDirection: 'column',
                    gap: 'var(--ob-space-50)',
                  }}
                >
                  <dt
                    style={{
                      margin: 0,
                      fontSize: '0.7rem',
                      letterSpacing: '0.08em',
                      textTransform: 'uppercase',
                      color: 'var(--ob-color-text-tertiary)',
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
                  color: 'var(--ob-color-text-secondary)',
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
