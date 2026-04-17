/**
 * Build Envelope Card - AI Studio layout
 * - Zone Code + Plot Ratio in header row (Zone Code in accent color)
 * - Divider
 * - Simple flex rows for remaining metrics
 * - Note at bottom
 */

import { Box, Divider, Typography } from '@mui/material'
import { GpsFixed as TargetIcon } from '@mui/icons-material'
import { CardHeader, ItemLabel, ItemValue, CardNote } from '../helpers'
import type { OverviewCard } from '../utils'
import { Card } from '../../../../../../components/canonical/Card'

export function BuildEnvelopeCard({ card }: { card: OverviewCard }) {
  const zoneCode = card.items.find((i) =>
    i.label.toLowerCase().includes('zone code'),
  )
  const plotRatio = card.items.find(
    (i) =>
      i.label.toLowerCase().includes('plot ratio') ||
      i.label.toLowerCase().includes('allowable'),
  )
  const otherItems = card.items.filter(
    (i) =>
      !i.label.toLowerCase().includes('zone code') &&
      !i.label.toLowerCase().includes('plot ratio') &&
      !i.label.toLowerCase().includes('allowable'),
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
      <CardHeader title={card.title} icon={TargetIcon} />

      <Box
        sx={{
          display: 'flex',
          flexDirection: 'column',
          gap: 'var(--ob-space-100)',
          flex: 1,
        }}
      >
        {/* Zone Code + Plot Ratio header row */}
        <Box
          sx={{
            display: 'flex',
            justifyContent: 'space-between',
            alignItems: 'flex-start',
          }}
        >
          {zoneCode && (
            <Box>
              <ItemLabel>{zoneCode.label}</ItemLabel>
              <ItemValue variant="accent">{zoneCode.value}</ItemValue>
            </Box>
          )}
          {plotRatio && (
            <Box sx={{ textAlign: 'right' }}>
              <ItemLabel>{plotRatio.label}</ItemLabel>
              <ItemValue>{plotRatio.value}</ItemValue>
            </Box>
          )}
        </Box>

        {/* Divider */}
        <Divider sx={{ borderColor: 'var(--ob-color-border-subtle)' }} />

        {/* Other metrics - simple rows */}
        <Box
          sx={{
            display: 'flex',
            flexDirection: 'column',
            gap: 'var(--ob-space-075)',
          }}
        >
          {otherItems.map((item) => (
            <Box
              key={item.label}
              sx={{
                display: 'flex',
                justifyContent: 'space-between',
                alignItems: 'center',
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
                  fontSize: 'var(--ob-font-size-xs)',
                  fontWeight: 'var(--ob-font-weight-semibold)',
                  color: 'text.primary',
                }}
              >
                {item.value}
              </Typography>
            </Box>
          ))}
        </Box>
      </Box>

      {/* Note */}
      {card.note && <CardNote>{card.note}</CardNote>}
    </Card>
  )
}
