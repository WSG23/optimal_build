/**
 * Heritage Context Card - AI Studio layout
 * - Risk Level as colored badge
 * - Description text
 * - Warning callout if needed
 */

import { Box, Typography } from '@mui/material'
import HistoryIcon from '@mui/icons-material/AccountBalance'
import { CardHeader, ItemLabel, CardNote } from '../helpers'
import type { OverviewCard } from '../utils'
import { Card } from '../../../../../../components/canonical/Card'

import { memo } from 'react'

export const HeritageCard = memo(function HeritageCard({
  card,
}: {
  card: OverviewCard
}) {
  const riskItem = card.items.find((i) =>
    i.label.toLowerCase().includes('risk'),
  )
  const riskValue = riskItem?.value?.toLowerCase() ?? ''
  const isLowRisk = riskValue.includes('low')
  const isHighRisk =
    riskValue.includes('high') ||
    riskValue.includes('critical') ||
    riskValue.includes('medium')

  const otherItems = card.items.filter(
    (i) => !i.label.toLowerCase().includes('risk'),
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
      <CardHeader title={card.title} icon={HistoryIcon} />

      <Box
        sx={{
          display: 'flex',
          flexDirection: 'column',
          gap: 'var(--ob-space-100)',
          flex: 1,
        }}
      >
        {/* Risk Level as badge */}
        {riskItem && (
          <Box>
            <ItemLabel>{riskItem.label}</ItemLabel>
            <Box sx={{ mt: 'var(--ob-space-025)' }}>
              <Box
                component="span"
                sx={{
                  display: 'inline-block',
                  px: 'var(--ob-space-075)',
                  py: 'var(--ob-space-025)',
                  borderRadius: 'var(--ob-radius-pill)',
                  fontSize: 'var(--ob-font-size-xs)',
                  fontWeight: 'var(--ob-font-weight-bold)',
                  bgcolor: isLowRisk
                    ? 'color-mix(in srgb, var(--ob-success-500) 15%, transparent)'
                    : 'color-mix(in srgb, var(--ob-warning-500) 15%, transparent)',
                  color: isLowRisk ? 'success.main' : 'warning.main',
                }}
              >
                {riskItem.value}
              </Box>
            </Box>
          </Box>
        )}

        {/* Other heritage items */}
        {otherItems.map((item) => (
          <Box key={item.label}>
            <ItemLabel>{item.label}</ItemLabel>
            <Typography
              sx={{
                fontSize: 'var(--ob-font-size-sm)',
                color: 'text.primary',
                mt: 'var(--ob-space-025)',
              }}
            >
              {item.value}
            </Typography>
          </Box>
        ))}

        {/* Warning callout for high risk */}
        {isHighRisk && card.note && (
          <Box
            sx={{
              display: 'flex',
              alignItems: 'flex-start',
              gap: 'var(--ob-space-075)',
              p: 'var(--ob-space-075)',
              bgcolor:
                'color-mix(in srgb, var(--ob-warning-500) 10%, transparent)',
              border: '1px solid',
              borderColor: 'warning.main',
              borderRadius: 'var(--ob-radius-sm)',
            }}
          >
            <Typography
              sx={{
                fontSize: 'var(--ob-font-size-xs)',
                color: 'warning.dark',
                lineHeight: 'var(--ob-line-height-snug)',
              }}
            >
              {card.note}
            </Typography>
          </Box>
        )}

        {/* Regular note for low risk */}
        {!isHighRisk && card.note && <CardNote>{card.note}</CardNote>}
      </Box>
    </Card>
  )
})
