/**
 * Location & Tenure Card - AI Studio layout
 * - Address as multi-line prominent text
 * - District/Tenure in 2-column grid
 * - Completion Year below
 */

import { Box, Typography } from '@mui/material'
import MapPinIcon from '@mui/icons-material/LocationOn'
import { CardHeader, ItemLabel, ItemValue } from '../helpers'
import type { OverviewCard } from '../utils'
import { Card } from '../../../../../../components/canonical/Card'

import { memo } from 'react'

export const LocationTenureCard = memo(function LocationTenureCard({
  card,
}: {
  card: OverviewCard
}) {
  const address = card.items.find((i) =>
    i.label.toLowerCase().includes('address'),
  )
  const district = card.items.find((i) =>
    i.label.toLowerCase().includes('district'),
  )
  const tenure = card.items.find((i) =>
    i.label.toLowerCase().includes('tenure'),
  )
  const completion = card.items.find(
    (i) =>
      i.label.toLowerCase().includes('completion') ||
      i.label.toLowerCase().includes('year'),
  )

  return (
    <Card
      sx={{
        p: 'var(--ob-space-125)',
        display: 'flex',
        flexDirection: 'column',
        height: '100%',
      }}
    >
      <CardHeader title={card.title} icon={MapPinIcon} />

      <Box
        sx={{
          display: 'flex',
          flexDirection: 'column',
          gap: 'var(--ob-space-100)',
          flex: 1,
        }}
      >
        {/* Address - prominent multi-line */}
        {address && (
          <Box>
            <ItemLabel>{address.label}</ItemLabel>
            <Typography
              sx={{
                fontSize: 'var(--ob-font-size-sm)',
                fontWeight: 'var(--ob-font-weight-semibold)',
                color: 'text.primary',
                lineHeight: 1.4,
                mt: 'var(--ob-space-025)',
              }}
            >
              {address.value}
            </Typography>
          </Box>
        )}

        {/* District / Tenure - 2-column grid */}
        <Box
          sx={{
            display: 'grid',
            gridTemplateColumns: 'repeat(2, 1fr)',
            gap: 'var(--ob-space-100)',
          }}
        >
          {district && (
            <Box>
              <ItemLabel>{district.label}</ItemLabel>
              <ItemValue>{district.value}</ItemValue>
            </Box>
          )}
          {tenure && (
            <Box>
              <ItemLabel>{tenure.label}</ItemLabel>
              <ItemValue>{tenure.value}</ItemValue>
            </Box>
          )}
        </Box>

        {/* Completion Year */}
        {completion && (
          <Box>
            <ItemLabel>{completion.label}</ItemLabel>
            <ItemValue>{completion.value}</ItemValue>
          </Box>
        )}
      </Box>
    </Card>
  )
})
