/**
 * Property Overview Section Component
 *
 * Displays property overview cards in a responsive grid layout.
 * Receives pre-computed cards data and renders them consistently.
 */

import '../../../../../styles/site-acquisition.css'

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
    <div className="property-overview">
      {cards.map((card, index) => (
        <article
          key={`${card.title}-${index}`}
          className="property-overview__card"
        >
          {/* Card header */}
          <div className="property-overview__header">
            <span className="property-overview__title">{card.title}</span>
            {card.subtitle && (
              <span className="property-overview__subtitle">
                {card.subtitle}
              </span>
            )}
          </div>

          {/* Card items */}
          <dl className="property-overview__items">
            {card.items.map((item) => (
              <div
                key={`${card.title}-${item.label}`}
                className="property-overview__item"
              >
                <dt className="property-overview__item-label">{item.label}</dt>
                <dd className="property-overview__item-value">{item.value}</dd>
              </div>
            ))}
          </dl>

          {/* Tags */}
          {card.tags && card.tags.length > 0 && (
            <div className="property-overview__tags">
              {card.tags.map((tag) => (
                <span
                  key={`${card.title}-${tag}`}
                  className="property-overview__tag"
                >
                  {tag}
                </span>
              ))}
            </div>
          )}

          {/* Note */}
          {card.note && <p className="property-overview__note">{card.note}</p>}
        </article>
      ))}
    </div>
  )
}
