/**
 * Property Overview Section Component
 *
 * Displays property overview cards in a responsive grid layout.
 * Receives pre-computed cards data and renders them consistently.
 */

// ============================================================================
// Types
// ============================================================================

export interface OverviewCard {
  title: string
  subtitle?: string | null
  items: Array<{ label: string; value: string }>
  tags?: string[]
  note?: string | null
}

export interface PropertyOverviewSectionProps {
  cards: OverviewCard[]
}

// ============================================================================
// Component
// ============================================================================

export function PropertyOverviewSection({
  cards,
}: PropertyOverviewSectionProps) {
  if (cards.length === 0) {
    return null
  }

  return (
    <div
      style={{
        display: 'grid',
        gap: '1.25rem',
        gridTemplateColumns: 'repeat(auto-fit, minmax(240px, 1fr))',
      }}
    >
      {cards.map((card, index) => (
        <article
          key={`${card.title}-${index}`}
          style={{
            border: '1px solid var(--ob-color-border-subtle)',
            borderRadius: 'var(--ob-radius-sm)',
            padding: '1.25rem',
            background: 'var(--ob-color-bg-surface-elevated)',
            display: 'flex',
            flexDirection: 'column',
            gap: '0.9rem',
            minHeight: '100%',
          }}
        >
          {/* Card header */}
          <div
            style={{ display: 'flex', flexDirection: 'column', gap: '0.25rem' }}
          >
            <span
              style={{
                fontSize: '0.75rem',
                letterSpacing: '0.08em',
                textTransform: 'uppercase',
                fontWeight: 600,
                color: 'var(--ob-color-text-muted)',
              }}
            >
              {card.title}
            </span>
            {card.subtitle && (
              <span
                style={{
                  fontSize: '1rem',
                  fontWeight: 600,
                  color: 'var(--ob-color-text-primary)',
                  letterSpacing: '-0.01em',
                }}
              >
                {card.subtitle}
              </span>
            )}
          </div>

          {/* Card items */}
          <dl
            style={{
              margin: 0,
              display: 'grid',
              gridTemplateColumns: 'repeat(auto-fit, minmax(160px, 1fr))',
              gap: '0.75rem',
            }}
          >
            {card.items.map((item) => (
              <div
                key={`${card.title}-${item.label}`}
                style={{
                  display: 'flex',
                  flexDirection: 'column',
                  gap: '0.2rem',
                }}
              >
                <dt
                  style={{
                    margin: 0,
                    fontSize: '0.75rem',
                    fontWeight: 600,
                    letterSpacing: '0.06em',
                    textTransform: 'uppercase',
                    color: 'var(--ob-color-text-muted)',
                  }}
                >
                  {item.label}
                </dt>
                <dd
                  style={{
                    margin: 0,
                    fontSize: '0.95rem',
                    fontWeight: 600,
                    color: 'var(--ob-color-text-primary)',
                  }}
                >
                  {item.value}
                </dd>
              </div>
            ))}
          </dl>

          {/* Tags */}
          {card.tags && card.tags.length > 0 && (
            <div
              style={{
                display: 'flex',
                flexWrap: 'wrap',
                gap: '0.4rem',
              }}
            >
              {card.tags.map((tag) => (
                <span
                  key={`${card.title}-${tag}`}
                  style={{
                    display: 'inline-flex',
                    alignItems: 'center',
                    padding: '0.25rem 0.6rem',
                    borderRadius: 'var(--ob-radius-pill)',
                    background: 'var(--ob-info-100)',
                    color: 'var(--ob-color-brand-primary)',
                    fontSize: '0.75rem',
                    fontWeight: 600,
                  }}
                >
                  {tag}
                </span>
              ))}
            </div>
          )}

          {/* Note */}
          {card.note && (
            <p
              style={{
                margin: 0,
                fontSize: '0.75rem',
                color: 'var(--ob-color-text-muted)',
              }}
            >
              {card.note}
            </p>
          )}
        </article>
      ))}
    </div>
  )
}
