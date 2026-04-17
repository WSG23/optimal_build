/**
 * Zoning Card - AI Studio layout (Site Metrics style)
 * - Bottom divider rows for each metric
 * - Tags at bottom
 */

import { Box, Typography } from '@mui/material'
import RulerIcon from '@mui/icons-material/Straighten'
import { CardHeader } from '../helpers'
import type { OverviewCard } from '../utils'
import { Card } from '../../../../../../components/canonical/Card'

import { memo } from 'react'

export const ZoningCard = memo(function ZoningCard({
  card,
}: {
  card: OverviewCard
}) {
  return (
    <Card
      sx={{
        p: 'var(--ob-space-125)',
        display: 'flex',
        flexDirection: 'column',
        height: '100%',
      }}
    >
      <CardHeader title={card.title} icon={RulerIcon} />

      <Box
        sx={{
          display: 'flex',
          flexDirection: 'column',
          gap: 'var(--ob-space-075)',
          flex: 1,
        }}
      >
        {/* Metrics with bottom dividers */}
        {card.items.map((item, index) => (
          <Box
            key={item.label}
            sx={{
              display: 'flex',
              justifyContent: 'space-between',
              alignItems: 'flex-end',
              pb: 'var(--ob-space-050)',
              borderBottom:
                index < card.items.length - 1
                  ? '1px solid var(--ob-color-border-subtle)'
                  : 'none',
            }}
          >
            <Typography
              sx={{
                fontSize: 'var(--ob-font-size-xs)',
                color: 'text.secondary',
              }}
            >
              {item.label}
            </Typography>
            <Typography
              sx={{
                fontSize: 'var(--ob-font-size-sm)',
                fontWeight: 'var(--ob-font-weight-bold)',
                color: 'text.primary',
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
    </Card>
  )
})
