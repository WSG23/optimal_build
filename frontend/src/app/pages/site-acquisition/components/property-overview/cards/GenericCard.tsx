/**
 * Generic/Default Card - for cards without specific layouts
 * Simple uniform layout for less common card types
 */

import { Box, Typography } from '@mui/material'
import { CardHeader, CardNote } from '../helpers'
import { getCardIcon } from '../utils'
import type { OverviewCard } from '../utils'
import { Card } from '../../../../../../components/canonical/Card'

export function GenericCard({ card }: { card: OverviewCard }) {
  const Icon = getCardIcon(card.title)

  return (
    <Card
      sx={{
        p: 'var(--ob-space-125)',
        display: 'flex',
        flexDirection: 'column',
        height: '100%',
      }}
    >
      <CardHeader title={card.title} icon={Icon} />

      {/* Subtitle if present */}
      {card.subtitle && (
        <Typography
          sx={{
            fontSize: 'var(--ob-font-size-sm)',
            fontWeight: 'var(--ob-font-weight-semibold)',
            color: 'info.main',
            mb: 'var(--ob-space-075)',
          }}
        >
          {card.subtitle}
        </Typography>
      )}

      <Box
        sx={{
          display: 'flex',
          flexDirection: 'column',
          gap: 'var(--ob-space-075)',
          flex: 1,
        }}
      >
        {card.items.map((item) => (
          <Box
            key={item.label}
            sx={{
              display: 'flex',
              justifyContent: 'space-between',
              alignItems: 'flex-start',
              gap: 'var(--ob-space-050)',
            }}
          >
            <Typography
              sx={{
                fontSize: 'var(--ob-font-size-2xs)',
                fontWeight: 'var(--ob-font-weight-medium)',
                letterSpacing: '0.05em',
                textTransform: 'uppercase',
                color: 'text.secondary',
                flexShrink: 0,
              }}
            >
              {item.label}
            </Typography>
            <Typography
              sx={{
                fontSize: 'var(--ob-font-size-sm)',
                fontWeight: 'var(--ob-font-weight-semibold)',
                color: 'text.primary',
                textAlign: 'right',
              }}
            >
              {item.value}
            </Typography>
          </Box>
        ))}

        {/* Tags */}
        {card.tags && card.tags.length > 0 && (
          <Box
            sx={{
              display: 'flex',
              flexWrap: 'wrap',
              gap: 'var(--ob-space-050)',
              mt: 'var(--ob-space-050)',
            }}
          >
            {card.tags.map((tag) => (
              <Box
                key={tag}
                sx={{
                  px: 'var(--ob-space-050)',
                  py: 'var(--ob-space-025)',
                  bgcolor:
                    'color-mix(in srgb, var(--ob-info-500) 10%, transparent)',
                  color: 'info.main',
                  borderRadius: 'var(--ob-radius-xs)',
                  fontSize: 'var(--ob-font-size-2xs)',
                  fontWeight: 'var(--ob-font-weight-semibold)',
                  textTransform: 'uppercase',
                }}
              >
                {tag}
              </Box>
            ))}
          </Box>
        )}
      </Box>

      {/* Note */}
      {card.note && <CardNote>{card.note}</CardNote>}
    </Card>
  )
}
