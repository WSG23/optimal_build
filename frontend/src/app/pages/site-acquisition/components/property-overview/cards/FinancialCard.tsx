/**
 * Financial Card - reserved for downstream workflows outside Capture
 * - Large hero numbers for Est. Revenue and Est. CAPEX
 * - Divider
 * - Smaller rows for Capital Stack and Dominant Risk
 */

import { Box, Divider, Typography } from '@mui/material'
import TrendingUpIcon from '@mui/icons-material/TrendingUp'
import { CardHeader, ItemLabel, ItemValue, CardNote } from '../helpers'
import type { OverviewCard } from '../utils'
import { Card } from '../../../../../../components/canonical/Card'

import { memo } from 'react'

export const FinancialCard = memo(function FinancialCard({
  card,
}: {
  card: OverviewCard
}) {
  const revenue = card.items.find(
    (i) =>
      i.label.toLowerCase().includes('revenue') ||
      i.label.toLowerCase().includes('est. revenue'),
  )
  const capex = card.items.find(
    (i) =>
      i.label.toLowerCase().includes('capex') ||
      i.label.toLowerCase().includes('est. capex'),
  )
  const otherItems = card.items.filter(
    (i) =>
      !i.label.toLowerCase().includes('revenue') &&
      !i.label.toLowerCase().includes('capex'),
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
      <CardHeader title={card.title} icon={TrendingUpIcon} />

      <Box
        sx={{
          display: 'flex',
          flexDirection: 'column',
          gap: 'var(--ob-space-100)',
          flex: 1,
        }}
      >
        {/* Hero numbers for Rev/CAPEX */}
        <Box
          sx={{
            display: 'grid',
            gridTemplateColumns: '1fr',
            gap: 'var(--ob-space-075)',
          }}
        >
          {revenue && (
            <Box>
              <ItemLabel>Est. Revenue</ItemLabel>
              <ItemValue variant="large">{revenue.value}</ItemValue>
            </Box>
          )}
          {capex && (
            <Box>
              <ItemLabel>Est. CAPEX</ItemLabel>
              <ItemValue variant="large">{capex.value}</ItemValue>
            </Box>
          )}
        </Box>

        {/* Divider */}
        {otherItems.length > 0 && (
          <Divider sx={{ borderColor: 'var(--ob-color-border-subtle)' }} />
        )}

        {/* Other items - smaller rows */}
        {otherItems.map((item) => (
          <Box key={item.label}>
            <ItemLabel>{item.label}</ItemLabel>
            <Box
              sx={{
                display: 'flex',
                alignItems: 'center',
                gap: 'var(--ob-space-050)',
                mt: 'var(--ob-space-025)',
              }}
            >
              {item.label.toLowerCase().includes('risk') && (
                <Box
                  sx={{
                    width: 'var(--ob-space-050)',
                    height: 'var(--ob-space-050)',
                    borderRadius: 'var(--ob-radius-pill)',
                    bgcolor: 'success.main',
                  }}
                />
              )}
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
          </Box>
        ))}
      </Box>

      {/* Note */}
      {card.note && <CardNote>{card.note}</CardNote>}
    </Card>
  )
})
