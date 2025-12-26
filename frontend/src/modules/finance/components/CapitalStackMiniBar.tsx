import { useMemo } from 'react'

import { Box } from '@mui/material'

import type { FinanceScenarioSummary } from '../../../api/finance'

interface CapitalStackMiniBarProps {
  stack: NonNullable<FinanceScenarioSummary['capitalStack']>
}

export function CapitalStackMiniBar({ stack }: CapitalStackMiniBarProps) {
  const bars = useMemo(() => {
    const total = Number(stack.total) || 1
    const equityPct = (Number(stack.equityTotal) / total) * 100
    const debtPct = (Number(stack.debtTotal) / total) * 100
    const otherPct = (Number(stack.otherTotal) / total) * 100 // Or calculate remaining gap

    // Safety check for NaN
    return [
      {
        type: 'equity',
        width: isNaN(equityPct) ? 0 : equityPct,
        color: 'var(--ob-color-brand-primary)',
      },
      {
        type: 'debt',
        width: isNaN(debtPct) ? 0 : debtPct,
        color: 'var(--ob-color-brand-secondary)',
      },
      {
        type: 'gap',
        width: isNaN(otherPct) ? 0 : otherPct,
        color: 'var(--ob-color-neutral-300)',
      },
    ]
  }, [stack])

  return (
    <Box
      className="capital-stack-mini-bar"
      sx={{
        display: 'flex',
        height: 'var(--ob-space-050)',
        width: '100%',
        borderRadius: 'var(--ob-radius-sm)',
        overflow: 'hidden',
        bgcolor: 'var(--ob-color-surface-muted)',
      }}
    >
      {bars.map(
        (bar) =>
          bar.width > 0 && (
            <Box
              key={bar.type}
              sx={{
                width: `${bar.width}%`,
                bgcolor: bar.color,
                height: '100%',
              }}
              title={`${bar.type}: ${bar.width.toFixed(1)}%`}
            />
          ),
      )}
    </Box>
  )
}
