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
        marginTop: 'var(--ob-space-200)',
        border: '1px solid var(--ob-color-border-subtle, #e5e7eb)',
        borderRadius: 'var(--ob-radius-sm)',
        padding: 'var(--ob-space-150)',
        background: 'var(--ob-color-bg-surface, #ffffff)',
        display: 'flex',
        flexDirection: 'column',
        gap: 'var(--ob-space-125)',
      }}
    >
      <div
        style={{
          display: 'flex',
          flexDirection: 'column',
          gap: 'var(--ob-space-035)',
        }}
      >
        <h4
          style={{
            margin: 0,
            fontSize: 'var(--ob-font-size-base)',
            fontWeight: 'var(--ob-font-weight-semibold)',
            letterSpacing: '-0.01em',
            color: 'var(--ob-color-text-primary, #111827)',
          }}
        >
          Layer breakdown
        </h4>
        <p
          style={{
            margin: 0,
            fontSize: 'var(--ob-font-size-sm)',
            color: 'var(--ob-color-text-secondary, #4b5563)',
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
          gap: 'var(--ob-space-100)',
        }}
      >
        {layers.map((layer) => (
          <article
            key={layer.id}
            style={{
              border: '1px solid var(--ob-color-border-subtle, #e5e7eb)',
              borderRadius: 'var(--ob-radius-sm)',
              padding: 'var(--ob-space-100)',
              display: 'flex',
              flexDirection: 'column',
              gap: 'var(--ob-space-075)',
              background: 'var(--ob-color-bg-surface, #f9fafb)',
            }}
          >
            <div
              style={{
                display: 'flex',
                alignItems: 'center',
                gap: 'var(--ob-space-065)',
              }}
            >
              <span
                aria-hidden="true"
                style={{
                  width: '14px',
                  height: '14px',
                  borderRadius: 'var(--ob-radius-pill)',
                  background: layer.color,
                  boxShadow: '0 0 0 1px rgb(255 255 255 / 0.8)',
                }}
              />
              <div
                style={{
                  display: 'flex',
                  flexDirection: 'column',
                  gap: 'var(--ob-space-025)',
                }}
              >
                <span
                  style={{
                    fontWeight: 'var(--ob-font-weight-semibold)',
                    letterSpacing: '-0.01em',
                    color: 'var(--ob-color-text-primary, #111827)',
                  }}
                >
                  {layer.label}
                </span>
                <span
                  style={{
                    fontSize: 'var(--ob-font-size-sm)',
                    color: 'var(--ob-color-text-muted, #6b7280)',
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
                gap: 'var(--ob-space-050)',
              }}
            >
              {layer.metrics.map((metric) => (
                <div
                  key={`${layer.id}-${metric.label}`}
                  style={{
                    display: 'flex',
                    flexDirection: 'column',
                    gap: 'var(--ob-space-025)',
                  }}
                >
                  <dt
                    style={{
                      margin: 0,
                      fontSize: 'var(--ob-font-size-2xs)',
                      letterSpacing: '0.08em',
                      textTransform: 'uppercase',
                      color: 'var(--ob-color-text-muted, #9ca3af)',
                      fontWeight: 'var(--ob-font-weight-semibold)',
                    }}
                  >
                    {metric.label}
                  </dt>
                  <dd
                    style={{
                      margin: 0,
                      fontWeight: 'var(--ob-font-weight-semibold)',
                      color: 'var(--ob-color-text-primary, #1f2937)',
                      fontSize: 'var(--ob-font-size-md)',
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
                  fontSize: 'var(--ob-font-size-sm-minus)',
                  color: 'var(--ob-color-text-secondary, #4b5563)',
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
