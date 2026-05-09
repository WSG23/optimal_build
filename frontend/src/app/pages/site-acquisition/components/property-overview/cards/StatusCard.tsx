/**
 * Status Card - for analysis and preview states
 * - Accent subtitle with optional status pill
 * - Two-column detail grid
 * - Left-aligned wrapped values
 */

import { Box, Typography } from '@mui/material'
import { CardHeader, ItemLabel, CardNote } from '../helpers'
import { getCardIcon } from '../utils'
import type { OverviewCard } from '../utils'
import { Card } from '../../../../../../components/canonical/Card'

export function StatusCard({ card }: { card: OverviewCard }) {
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

      {(card.subtitle || (card.tags && card.tags.length > 0)) && (
        <Box
          sx={{
            display: 'flex',
            alignItems: 'flex-start',
            justifyContent: 'space-between',
            gap: 'var(--ob-space-075)',
            mb: 'var(--ob-space-075)',
          }}
        >
          {card.subtitle && (
            <Typography
              sx={{
                fontSize: 'var(--ob-font-size-sm)',
                fontWeight: 'var(--ob-font-weight-bold)',
                color: 'info.main',
                lineHeight: 'var(--ob-line-height-snug)',
              }}
            >
              {card.subtitle}
            </Typography>
          )}
          {card.tags && card.tags.length > 0 && (
            <Box
              component="span"
              sx={{
                px: 'var(--ob-space-050)',
                py: 'var(--ob-space-025)',
                borderRadius: 'var(--ob-radius-xs)',
                bgcolor:
                  'color-mix(in srgb, var(--ob-success-500) 12%, transparent)',
                color: 'success.main',
                fontSize: 'var(--ob-font-size-2xs)',
                fontWeight: 'var(--ob-font-weight-bold)',
                textTransform: 'uppercase',
                flexShrink: 0,
              }}
            >
              {card.tags[0]}
            </Box>
          )}
        </Box>
      )}

      <Box
        sx={{
          display: 'grid',
          gridTemplateColumns: {
            xs: '1fr',
            sm: 'repeat(2, minmax(0, 1fr))',
          },
          gap: 'var(--ob-space-075)',
          flex: 1,
        }}
      >
        {card.items.map((item) => (
          <Box
            key={item.label}
            sx={{
              p: 'var(--ob-space-050)',
              borderRadius: 'var(--ob-radius-xs)',
              bgcolor: 'var(--ob-surface-glass-subtle)',
              minWidth: 0,
            }}
          >
            <ItemLabel>{item.label}</ItemLabel>
            <Typography
              sx={{
                mt: 'var(--ob-space-025)',
                fontSize: 'var(--ob-font-size-sm)',
                fontWeight: 'var(--ob-font-weight-semibold)',
                color: 'text.primary',
                lineHeight: 'var(--ob-line-height-snug)',
                whiteSpace: 'pre-wrap',
                wordBreak: 'break-word',
              }}
            >
              {item.value}
            </Typography>
          </Box>
        ))}
      </Box>

      {card.note && <CardNote>{card.note}</CardNote>}
    </Card>
  )
}
